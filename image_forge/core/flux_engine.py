"""
FLUX Image Generation Engine
Optimized for 8GB VRAM GPUs
"""
import torch
import gc
import time
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image
import io
import base64

from rich.console import Console

console = Console()


class FluxEngine:
    """FLUX Dev image generation engine with memory optimizations"""
    
    def __init__(
        self,
        model_id: str = "black-forest-labs/FLUX.1-dev",
        device: str = "auto",
        dtype: str = "float16",
        enable_cpu_offload: bool = True,
        enable_attention_slicing: bool = True,
        enable_vae_tiling: bool = True,
    ):
        self.model_id = model_id
        self.dtype = getattr(torch, dtype)
        self.enable_cpu_offload = enable_cpu_offload
        self.enable_attention_slicing = enable_attention_slicing
        self.enable_vae_tiling = enable_vae_tiling
        
        # Detect device
        self.device = self._detect_device(device)
        self.device_name = self._get_device_name()
        
        self.pipe = None
        self._loaded = False
        
        console.print(f"[green]FluxEngine initialized[/green]")
        console.print(f"  Device: {self.device} ({self.device_name})")
        console.print(f"  Model: {self.model_id}")
    
    def _detect_device(self, device: str) -> str:
        """Detect the best available device"""
        if device != "auto":
            return device
        
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _get_device_name(self) -> str:
        """Get human-readable device name"""
        if self.device == "cuda":
            return torch.cuda.get_device_name(0)
        elif self.device == "mps":
            return "Apple Silicon"
        else:
            return "CPU"
    
    def get_vram_gb(self) -> Optional[float]:
        """Get available VRAM in GB"""
        if self.device == "cuda":
            props = torch.cuda.get_device_properties(0)
            return props.total_memory / (1024**3)
        return None
    
    def load_model(self):
        """Load FLUX model with optimizations"""
        if self._loaded:
            return
        
        console.print("[yellow]Loading FLUX model...[/yellow]")
        start_time = time.time()
        
        try:
            from diffusers import FluxPipeline
            
            # Load pipeline
            self.pipe = FluxPipeline.from_pretrained(
                self.model_id,
                torch_dtype=self.dtype,
            )
            
            # Apply memory optimizations
            if self.enable_cpu_offload and self.device == "cuda":
                console.print("  Enabling CPU offload...")
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe = self.pipe.to(self.device)
            
            if self.enable_attention_slicing:
                console.print("  Enabling attention slicing...")
                self.pipe.enable_attention_slicing(1)
            
            if self.enable_vae_tiling:
                console.print("  Enabling VAE tiling...")
                self.pipe.enable_vae_tiling()
            
            self._loaded = True
            load_time = time.time() - start_time
            console.print(f"[green]Model loaded in {load_time:.1f}s[/green]")
            
        except Exception as e:
            console.print(f"[red]Failed to load model: {e}[/red]")
            raise
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
            self._loaded = False
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
            console.print("[yellow]Model unloaded[/yellow]")
    
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
        guidance: float = 3.5,
        seed: Optional[int] = None,
        batch_size: int = 1,
    ) -> Tuple[List[Image.Image], int, float]:
        """
        Generate images from prompt
        
        Returns:
            Tuple of (images, seed_used, generation_time)
        """
        if not self._loaded:
            self.load_model()
        
        # Set seed
        if seed is None:
            seed = torch.randint(0, 2**32 - 1, (1,)).item()
        
        generator = torch.Generator(device="cpu").manual_seed(seed)
        
        console.print(f"[cyan]Generating {batch_size} image(s)...[/cyan]")
        console.print(f"  Prompt: {prompt[:80]}...")
        console.print(f"  Size: {width}x{height}, Steps: {steps}, Seed: {seed}")
        
        start_time = time.time()
        
        try:
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance,
                num_images_per_prompt=batch_size,
                generator=generator,
            )
            
            images = result.images
            generation_time = time.time() - start_time
            
            console.print(f"[green]Generated in {generation_time:.1f}s[/green]")
            
            # Clear cache after generation
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            return images, seed, generation_time
            
        except Exception as e:
            console.print(f"[red]Generation failed: {e}[/red]")
            raise
    
    @staticmethod
    def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def save_image(image: Image.Image, path: Path) -> Path:
        """Save image to file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        return path
