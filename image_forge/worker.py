"""
ImageForge Worker
Runs on GPU machines to process generation tasks
"""
import asyncio
import time
from pathlib import Path
from datetime import datetime
import httpx
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import config
from .core.flux_engine import FluxEngine
from .core.models import WorkerInfo, TaskStatus

console = Console()
app = typer.Typer()


class Worker:
    """Worker that processes generation tasks"""
    
    def __init__(
        self,
        master_url: str,
        worker_id: str,
        device: str = "auto",
    ):
        self.master_url = master_url.rstrip("/")
        self.worker_id = worker_id
        self.device = device
        
        self.engine: FluxEngine = None
        self.running = False
        self.tasks_completed = 0
        
    async def start(self):
        """Start the worker"""
        console.print(f"[bold green]🚀 Starting ImageForge Worker[/bold green]")
        console.print(f"   Worker ID: {self.worker_id}")
        console.print(f"   Master: {self.master_url}")
        
        # Initialize FLUX engine
        self.engine = FluxEngine(
            model_id=config.FLUX_MODEL,
            device=self.device,
            dtype=config.FLUX_DTYPE,
            enable_cpu_offload=config.ENABLE_CPU_OFFLOAD,
            enable_attention_slicing=config.ENABLE_ATTENTION_SLICING,
            enable_vae_tiling=config.ENABLE_VAE_TILING,
        )
        
        # Load model
        console.print("\n[yellow]Loading FLUX model (this may take a few minutes)...[/yellow]")
        self.engine.load_model()
        
        # Register with master
        await self._register()
        
        # Start processing loop
        self.running = True
        await self._process_loop()
    
    async def _register(self):
        """Register worker with master server"""
        worker_info = WorkerInfo(
            id=self.worker_id,
            device=self.engine.device,
            device_name=self.engine.device_name,
            vram_gb=self.engine.get_vram_gb(),
            status="idle",
        )
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.master_url}/api/worker/register",
                    json=worker_info.model_dump(),
                    timeout=10,
                )
                response.raise_for_status()
                console.print("[green]✓ Registered with master[/green]")
            except Exception as e:
                console.print(f"[red]Failed to register: {e}[/red]")
                raise
    
    async def _heartbeat(self):
        """Send heartbeat to master"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.master_url}/api/worker/{self.worker_id}/heartbeat",
                    timeout=5,
                )
            except:
                pass
    
    async def _get_task(self):
        """Get next task from master"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.master_url}/api/worker/{self.worker_id}/task",
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if data else None
            except Exception as e:
                console.print(f"[yellow]Failed to get task: {e}[/yellow]")
            return None
    
    async def _complete_task(self, task_id: str, result_paths: list, duration: float):
        """Report task completion to master"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.master_url}/api/worker/{self.worker_id}/complete",
                    params={
                        "task_id": task_id,
                        "duration": duration,
                    },
                    json=result_paths,
                    timeout=10,
                )
            except Exception as e:
                console.print(f"[red]Failed to report completion: {e}[/red]")
    
    async def _fail_task(self, task_id: str, error: str):
        """Report task failure to master"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.master_url}/api/worker/{self.worker_id}/fail",
                    params={
                        "task_id": task_id,
                        "error": error,
                    },
                    timeout=10,
                )
            except Exception as e:
                console.print(f"[red]Failed to report failure: {e}[/red]")
    
    async def _process_task(self, task: dict):
        """Process a single generation task"""
        task_id = task["id"]
        request = task["request"]
        
        console.print(f"\n[cyan]📋 Processing task {task_id[:8]}...[/cyan]")
        
        try:
            # Generate images
            images, seed, duration = self.engine.generate(
                prompt=request["prompt"],
                negative_prompt=request.get("negative_prompt", ""),
                width=request.get("width", 1024),
                height=request.get("height", 1024),
                steps=request.get("steps", 28),
                guidance=request.get("guidance", 3.5),
                seed=request.get("seed"),
                batch_size=request.get("batch_size", 1),
            )
            
            # Save images
            result_paths = []
            output_dir = config.OUTPUT_DIR / task_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for i, image in enumerate(images):
                path = output_dir / f"image_{i}.png"
                self.engine.save_image(image, path)
                result_paths.append(str(path))
            
            # Report completion
            await self._complete_task(task_id, result_paths, duration)
            
            self.tasks_completed += 1
            console.print(f"[green]✓ Task completed ({duration:.1f}s)[/green]")
            console.print(f"   Total completed: {self.tasks_completed}")
            
        except Exception as e:
            console.print(f"[red]✗ Task failed: {e}[/red]")
            await self._fail_task(task_id, str(e))
    
    async def _process_loop(self):
        """Main processing loop"""
        console.print("\n[bold]👀 Waiting for tasks...[/bold]")
        
        heartbeat_interval = 30
        last_heartbeat = time.time()
        
        while self.running:
            # Send heartbeat
            if time.time() - last_heartbeat > heartbeat_interval:
                await self._heartbeat()
                last_heartbeat = time.time()
            
            # Get next task
            task = await self._get_task()
            
            if task:
                await self._process_task(task)
            else:
                # No task available, wait a bit
                await asyncio.sleep(2)
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        if self.engine:
            self.engine.unload_model()


@app.command()
def main(
    master: str = typer.Option(
        config.MASTER_URL,
        "--master", "-m",
        help="Master server URL",
    ),
    worker_id: str = typer.Option(
        config.WORKER_ID,
        "--id", "-i",
        help="Worker ID",
    ),
    device: str = typer.Option(
        config.WORKER_DEVICE,
        "--device", "-d",
        help="Device to use (auto, cuda, mps, cpu)",
    ),
):
    """Start ImageForge worker"""
    worker = Worker(
        master_url=master,
        worker_id=worker_id,
        device=device,
    )
    
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        worker.stop()


if __name__ == "__main__":
    app()
