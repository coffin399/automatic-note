import os
import torch
from diffusers import (
    StableDiffusionPipeline, 
    EulerAncestralDiscreteScheduler, 
    EulerDiscreteScheduler, 
    DPMSolverMultistepScheduler, 
    DDIMScheduler
)
import logging
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalImageGenerator:
    def __init__(self, model_id="runwayml/stable-diffusion-v1-5", device="cpu", scheduler_name="Euler a", safety_checker=None):
        """
        Initializes the LocalImageGenerator.
        
        Args:
            model_id (str): The Hugging Face model ID.
            device (str): Device to run on ('cpu' or 'cuda'). Default is 'cpu' for N100.
            scheduler_name (str): Name of the scheduler to use.
            safety_checker (bool): Whether to use the safety checker. Default None (auto-disable if possible to save RAM).
        """
        self.device = device
        self.model_id = model_id
        self.scheduler_name = scheduler_name
        self.pipe = None
        
        logger.info(f"Initialized LocalImageGenerator config with model: {model_id}, scheduler: {scheduler_name} on {device}")
        # Pipeline is NOT loaded here to save memory. Call load() before use.

    def load(self):
        """Loads the pipeline into memory."""
        if self.pipe is not None:
            logger.info("Pipeline already loaded.")
            return

        logger.info(f"Loading pipeline for {self.model_id}...")
        try:
            # Determine dtype based on device
            torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            # Load the pipeline
            # Check if model_id is a local file (safetensors/ckpt)
            if os.path.isfile(self.model_id) or self.model_id.endswith((".safetensors", ".ckpt")):
                logger.info(f"Loading from single file: {self.model_id} ({torch_dtype})")
                self.pipe = StableDiffusionPipeline.from_single_file(
                    self.model_id,
                    torch_dtype=torch_dtype,
                    use_safetensors=True
                )
            else:
                # Load from folder or Hugging Face ID
                logger.info(f"Loading from pretrained (folder/HF): {self.model_id} ({torch_dtype})")
                self.pipe = StableDiffusionPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=torch_dtype,
                    use_safetensors=True
                )
            
            # Set Scheduler
            self._set_scheduler()

            self.pipe.to(self.device)
            
            # Optimization for CPU/Low RAM
            if self.device == "cpu":
                logger.info("Applying CPU optimizations (enable_attention_slicing)...")
                self.pipe.enable_attention_slicing()
            elif self.device == "cuda":
                logger.info("Applying GPU optimizations...")
                # Optional: enable_xformers_memory_efficient_attention() if xformers is installed
                # self.pipe.enable_xformers_memory_efficient_attention()
                pass
            
            logger.info("Pipeline loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load Diffusers pipeline: {e}")
            raise e

    def _set_scheduler(self):
        """Configures the scheduler based on the name."""
        if not self.pipe:
            return

        try:
            config = self.pipe.scheduler.config
            if self.scheduler_name == "Euler a":
                self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(config)
            elif self.scheduler_name == "Euler":
                self.pipe.scheduler = EulerDiscreteScheduler.from_config(config)
            elif self.scheduler_name == "DPM++ 2M Karras":
                self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(config, use_karras_sigmas=True)
            elif self.scheduler_name == "DPM++ SDE Karras":
                self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++")
            elif self.scheduler_name == "DDIM":
                self.pipe.scheduler = DDIMScheduler.from_config(config)
            else:
                logger.warning(f"Unknown scheduler '{self.scheduler_name}', using default.")
            
            logger.info(f"Scheduler set to: {self.scheduler_name}")
        except Exception as e:
            logger.error(f"Failed to set scheduler: {e}")

    def unload(self):
        """Unloads the pipeline and frees memory."""
        if self.pipe is not None:
            logger.info("Unloading pipeline...")
            del self.pipe
            self.pipe = None
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            gc.collect()
            logger.info("Pipeline unloaded and memory cleaned up.")

    def generate(self, prompt, output_path, negative_prompt=None, width=512, height=512, num_inference_steps=20):
        """
        Generates an image from a prompt and saves it.
        """
        # Auto-load if not loaded
        loaded_here = False
        if self.pipe is None:
            self.load()
            loaded_here = True
            
        logger.info(f"Generating image for prompt: '{prompt}'")
        try:
            image = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps
            ).images[0]
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            image.save(output_path)
            logger.info(f"Image saved to {output_path}")
            
            # Auto-unload if we loaded it just for this generation
            if loaded_here:
                self.unload()
                
            return output_path
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            # Ensure unload on error if we loaded it here
            if loaded_here:
                self.unload()
            return None

if __name__ == "__main__":
    # Test
    generator = LocalImageGenerator()
    generator.generate("A futuristic city with flying cars, cyberpunk style", "test_image.png")
