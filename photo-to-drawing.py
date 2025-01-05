import gradio as gr
import torch
from hashlib import sha1
import os
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from PIL import Image, ImageDraw
from transformers import pipeline # for captioning

modelname = "./models/photon_v1.safetensors"
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
    
    # deactivate the start buttons
    if image is None: return [gr.update(interactive=False), gr.update(interactive=False)]
    # if we use imageEditor from Gradio:
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

    # there is an image, activate teh start buttons
    return [gr.update(interactive=True), gr.update(interactive=True)]


def check_safety(x_image):
    """Support function to check if the image is NSFW."""
    # all images are SFW ;)
    return x_image, False 

IMG_TO_TEXT_PIPELINE = None
def load_captioner():
    """Load and return a image to text model."""
    if (IMG_TO_TEXT_PIPELINE!= None): return IMG_TO_TEXT_PIPELINE

    captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
    # TODO: change to this pipeline to query details about the image in Version 2
    #captioner = pipeline("image-text-to-text", model="Salesforce/blip-image-captioning-base")


    #value = captioner("https://huggingface.co/datasets/Narsil/image_dummy/resolve/main/parrots.png")
    #print (value[0]['generated_text'])
    return captioner

def describe_image(image):
    """describe an image based."""
    captioner = load_captioner()
    # messages = [
    # {
    #     "role": "user",
    #     "content": [
    #         {"type": "image", "image": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg"},
    #         {"type": "text", "text": "What do we see in this image?"},
    #     ]
    # }]
    # prompt = captioner.apply_chat_template(messages)
    #value = captioner(image, text=prompt, return_full_text=False)
    value = captioner(image)
    #print (value)
    return value[0]['generated_text']

CACHED_MODEL = None
def load_model(style):
    """Load and return the Stable Diffusion model based on style."""
    if (CACHED_MODEL!= None): return CACHED_MODEL

    #pipeline = StableDiffusionPipeline.from_pretrained(
    #pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
    pipeline = StableDiffusionImg2ImgPipeline.from_single_file(
        modelname,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        safety_checker = None, requires_safety_checker = False
        #revision="fp16" if device == "cuda" else "",
    )
    pipeline = pipeline.to(device)
    return pipeline


def stylize(image, style, strength, steps, image_description):
    """Convert the entire input image to the selected style."""
    try:
        model = load_model(style)
        negative_prompt = ""
        # Adjust the prompt based on style
        if style == "Anime":
            prompt = "anime-style painting of "
            negative_prompt = "realistic photo"
        elif style == "Disney":
            prompt = "In a castle, A scene from a Walt Disney movie, perfect drawing in the style of Walt Disney, many details:"
            negative_prompt = "realistic photo"
            strength = 0.4
        elif style == "Painting":
            prompt = "modern oil painting of"
            strength = 0.5
            negative_prompt = "realistic photo"
        elif style == "Fantasy":
            prompt = "fantasy art style"
        elif style == "Old":
            prompt = "photo of very old "
            strength = 0.6
            if (image_description.startswith("a ")): image_description = image_description[2:]
            negative_prompt = "young people"
        elif style == "Young":
            prompt = "photo of child "  
            if (image_description.startswith("a ")): image_description = image_description[2:]
            strength = 0.6
            negative_prompt = "old people"


        else:
            prompt = ""
        
        #image_description = describe_image(image)
        if image_description is None: image_description = "existing image"
        prompt += f": {image_description}"

        print (prompt)

        # TODO Previews in Version 2
        # previews = []
        # def preview_callback(step, timestep, latents):
        #         """Callback function to store previews every 5 steps."""
        #         if step % 5 == 0:
        #             with torch.no_grad():
        #                 preview_image = model.decode_latents(latents)
        #                 preview_pil = model.numpy_to_pil(preview_image)[0]
        #                 previews.append(preview_pil)

        #steps = 60 if device == "cuda" else 30
        if not image is None: 
            #image = image.resize((512,512))
            image.thumbnail((1024,1024))
            mask = Image.new("L", image.size, 255)  # Create a white mask

            # Generate new picture
            result = model(
                prompt=prompt, 
                negative_prompt=negative_prompt,
                num_inference_steps=steps, 
                image=image, 
                mask_image=mask, 
                strength=strength,
                ).images[0]
            return result
        else:
            return None
    except RuntimeError as e:
        print(f"RuntimeError: {e}")

# Gradio Starts
#---------------------------------------------------------------------------
# Render UI
#--------------------------------------------------------------
with gr.Blocks() as app:
    with gr.Row():
        gr.Markdown("### Stable Diffusion Stylization")

    with gr.Row():
        with gr.Column():
            image_input = gr.Image(label="Input Image", type="pil", height=512)
            describe_button = gr.Button("Describe", interactive=False)
            text_description = gr.Textbox(label="Image description for better results")
            style_dropdown = gr.Radio([
                "Anime",
                "Disney",
                "Painting",
                "Fantasy",
                "Old",
                "Young",
                "Debug"
            ], label="Style", value="Anime")
            strength_slider = gr.Slider(label="Strength", minimum=0.1, maximum=1, value=0.4, step=0.1)
            steps_slider = gr.Slider(label="Steps", minimum=10, maximum=100, value=75, step=5)
            start_button = gr.Button("Start", interactive=False)

        with gr.Column():
            output_image = gr.Image(label="Output Image", type="pil", height=512)


    # Save input image immediately on change
    image_input.change(
         fn=save_input_file,
         inputs=[image_input],
         outputs=[start_button, describe_button]
    )

    describe_button.click(
        fn=describe_image,
        inputs=[image_input],
        outputs=[text_description]
    )

    start_button.click(
        fn=stylize,
        inputs=[image_input, style_dropdown, strength_slider, steps_slider, text_description],
        outputs=[output_image]
    )

if __name__ == "__main__":
    #CACHED_MODEL = load_model("none")
    IMG_TO_TEXT_PIPELINE = load_captioner()
    app.launch()
