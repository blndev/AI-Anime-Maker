import gradio as gr
import torch
from hashlib import sha1
import os
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from PIL import Image, ImageDraw

modelname = "CompVis/stable-diffusion-v1-4"
# "runwayml/stable-diffusion-inpainting"
# "CompVis/stable-diffusion-v1-4"
# "instruction-tuning-sd/cartoonizer",
# "pt-sk/stable-diffusion-1.5"

device = "cuda" if torch.cuda.is_available() else "cpu"
print (f"running on {device}")

def save_input_file(image):
    """Save the input image in a cache directory using its SHA-1 hash."""
    if not os.path.exists("cache"):
        os.makedirs("cache")
    if image is None: return gr.update(interactive=False)
    # try:
    #     image = image['background'] # if we use editor field
    # except:
    #     print("seems no background in image dict")
    #     print (image)
    try:
        #print (image)
        # Convert the image to bytes and compute the SHA-1 hash
        image_bytes = image.tobytes()
        filetype = "jpg"
        filename_hash = sha1(image_bytes).hexdigest() + "."+filetype
        file_path = os.path.join("cache", filename_hash)

        if not os.path.exists(file_path):
            image.save(file_path, format="JPEG")

    except Exception as e:
        print(f"Error while saving image:\n{e}")

    return gr.update(interactive=True)


def check_safety(x_image):
    return x_image, False # has_nsfw_concept

CACHED_MODEL = None
def load_model(style):
    """Load and return the Stable Diffusion model based on style."""
    if (CACHED_MODEL!= None): return CACHED_MODEL

    #pipeline = StableDiffusionPipeline.from_pretrained(
    pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
        modelname,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        safety_checker = None, requires_safety_checker = False
        #revision="fp16" if device == "cuda" else "",
    )
    pipeline = pipeline.to(device)
    return pipeline


def stylize(image, style, strength, steps):
    """Convert the entire input image to the selected style."""
    try:
        model = load_model(style)

        # Adjust the prompt based on style
        if style == "Anime":
            prompt = "anime-style painting"
        elif style == "Disney":
            prompt = "Disney-style artwork of a closeup man face"
        elif style == "Comic":
            prompt = "drawing in a style of a comic"
        elif style == "Fantasy":
            prompt = "fantasy art style"
        elif style == "Pop Art":
            prompt = "pop art style"
        else:
            prompt = "artistic painting"

        # previews = []
        # def preview_callback(step, timestep, latents):
        #         """Callback function to store previews every 5 steps."""
        #         if step % 5 == 0:
        #             with torch.no_grad():
        #                 preview_image = model.decode_latents(latents)
        #                 preview_pil = model.numpy_to_pil(preview_image)[0]
        #                 previews.append(preview_pil)

        #steps = 60 if device == "cuda" else 30
        if not image is None: image = image.resize((512,512))
        mask = Image.new("L", (512, 512), 255)  # Create a white mask
        #draw = ImageDraw.Draw(mask)
        #draw.rectangle([150, 150, 350, 350], fill=255) 
        result = model(
            prompt=prompt, 
            num_inference_steps=steps, 
            image=image, 
            mask_image=mask, 
            strength=strength,
            ).images[0]
        return result
    except RuntimeError as e:
        print(f"RuntimeError: {e}")

with gr.Blocks() as app:
    with gr.Row():
        gr.Markdown("### Stable Diffusion Stylization")

    with gr.Row():
        with gr.Column():
            image_input = gr.Image(label="Input Image", type="pil", height=512)
            style_dropdown = gr.Radio([
                "Anime",
                "Disney",
                "Comic",
                "Fantasy",
                "Pop Art"
            ], label="Style", value="Anime")
            strength_slider = gr.Slider(label="Strength", minimum=0.1, maximum=1, value=0.6, step=0.1)
            steps_slider = gr.Slider(label="Steps", minimum=10, maximum=100, value=40, step=5)
            start_button = gr.Button("Start", interactive=False)

        with gr.Column():
            output_image = gr.Image(label="Output Image", type="pil", height=512)

    # Save input image immediately on change
    image_input.change(
         fn=save_input_file,
         inputs=[image_input],
         outputs=[start_button]
    )

    start_button.click(
        fn=stylize,
        inputs=[image_input, style_dropdown, strength_slider, steps_slider],
        outputs=[output_image]
    )

if __name__ == "__main__":
    CACHED_MODEL = load_model("none")
    app.launch()
