import gradio as gr
import torch
from hashlib import sha1
import os
from diffusers import StableDiffusionPipeline
from PIL import Image

modelname = "CompVis/stable-diffusion-v1-4"
#"instruction-tuning-sd/cartoonizer",
#"pt-sk/stable-diffusion-1.5"

device = "cuda" if torch.cuda.is_available() else "cpu"
print (f"running on {device}")

def save_input_file(image):
    """Save the input image in a cache directory using its SHA-1 hash."""
    if not os.path.exists("cache"):
        os.makedirs("cache")
    if image is None: return
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


CACHED_MODEL = None
def load_model(style):
    """Load and return the Stable Diffusion model based on style."""
    if (CACHED_MODEL!= None): return CACHED_MODEL

    pipeline = StableDiffusionPipeline.from_pretrained(
        modelname,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
        #revision="fp16" if device == "cuda" else "",
    )
    pipeline = pipeline.to(device)
    return pipeline

def stylize(image, style):
    """Convert the entire input image to the selected style."""
    try:
        model = load_model(style)

        # Adjust the prompt based on style
        if style == "Anime":
            prompt = "anime-style painting"
        elif style == "Disney":
            prompt = "Disney-style artwork"
        else:
            prompt = "artistic painting"

        #result = model(prompt=prompt, image=image).images[0]
        steps = 30 if device == "cuda" else 10
        image = image.resize((512,512))
        result = model(prompt=prompt, num_inference_steps=steps, image=image).images[0]
        return result
    except RuntimeError as e:
        print(f"RuntimeError: {e}")

with gr.Blocks() as app:
    with gr.Row():
        gr.Markdown("### Stable Diffusion Stylization")

    with gr.Row():
        with gr.Column():
            image_input = gr.Image(label="Input Image", type="pil", height=512 )
            style_dropdown = gr.Radio([
                "Anime",
                "Disney",
                "Random"
            ], label="Style", value="Anime")
            start_button = gr.Button("Start")

        with gr.Column():
            output_image = gr.Image(label="Output Image", type="pil", height=512)

    # Save input image immediately on change
    image_input.change(
         fn=save_input_file,
         inputs=[image_input],
         outputs=[]
    )

    start_button.click(
        fn=stylize,
        inputs=[image_input, style_dropdown],
        outputs=[output_image]
    )

if __name__ == "__main__":
    CACHED_MODEL = load_model("none")
    app.launch()
