"""
ImageForge CLI Entry Point
"""
import typer
from typing import Optional

app = typer.Typer(
    name="imageforge",
    help="ImageForge - Local FLUX Image Generation Platform"
)


@app.command()
def master():
    """Start the master server"""
    from .master import main
    main()


@app.command()
def worker(
    master_url: str = typer.Option(
        "http://localhost:8100",
        "--master", "-m",
        help="Master server URL"
    ),
    worker_id: str = typer.Option(
        "worker-1",
        "--id", "-i", 
        help="Worker ID"
    ),
    device: str = typer.Option(
        "auto",
        "--device", "-d",
        help="Device (auto, cuda, mps, cpu)"
    ),
):
    """Start a worker"""
    from .worker import Worker
    import asyncio
    
    w = Worker(
        master_url=master_url,
        worker_id=worker_id,
        device=device,
    )
    
    try:
        asyncio.run(w.start())
    except KeyboardInterrupt:
        w.stop()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Image prompt"),
    master_url: str = typer.Option(
        "http://localhost:8100",
        "--master", "-m"
    ),
    width: int = typer.Option(1024, "--width", "-w"),
    height: int = typer.Option(1024, "--height", "-h"),
    steps: int = typer.Option(28, "--steps", "-s"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """Generate a single image (CLI)"""
    import httpx
    import time
    from rich.console import Console
    
    console = Console()
    
    console.print(f"[cyan]Submitting generation request...[/cyan]")
    
    with httpx.Client() as client:
        # Submit task
        response = client.post(
            f"{master_url}/api/generate",
            json={
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
            },
            timeout=10,
        )
        task = response.json()
        task_id = task["id"]
        
        console.print(f"Task ID: {task_id}")
        console.print("[yellow]Waiting for generation...[/yellow]")
        
        # Poll for completion
        while True:
            time.sleep(2)
            response = client.get(f"{master_url}/api/task/{task_id}")
            task = response.json()
            
            if task["status"] == "completed":
                console.print("[green]✓ Generation complete![/green]")
                
                # Download image
                if output:
                    response = client.get(f"{master_url}/api/image/{task_id}/0")
                    with open(output, "wb") as f:
                        f.write(response.content)
                    console.print(f"Saved to: {output}")
                else:
                    console.print(f"View at: {master_url}/api/image/{task_id}/0")
                break
                
            elif task["status"] == "failed":
                console.print(f"[red]✗ Generation failed: {task.get('error')}[/red]")
                break
            
            console.print(".", end="")


if __name__ == "__main__":
    app()
