import os
import torch
from diffusers import StableDiffusionPipeline
import logging
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalImageGenerator:
    def __init__(self, model_id="runwayml/stable-diffusion-v1-5", device="cpu", safety_checker=None):
        """
        Initializes the LocalImageGenerator.
        
        Args:
            model_id (str): The Hugging Face model ID.
            device (str): Device to run on ('cpu' or 'cuda'). Default is 'cpu' for N100.
            safety_checker (bool): Whether to use the safety checker. Default None (auto-disable if possible to save RAM).
        """
        self.device = device
        self.model_id = model_id
        self.pipe = None
        
        logger.info(f"Initialized LocalImageGenerator config with model: {model_id} on {device}")
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
