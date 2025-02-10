from PIL import Image
import src.config as config

# this switch is basically for the build systems
if config.SKIP_ONNX:
    def get_gender_and_age_from_image(pil_image: Image):
        """ without onnx we cant detect and analyze faces"""
        return []
else:
    print("loading onnx functions")
    import src.onnx_analyzer as wrapped
    def get_gender_and_age_from_image(pil_image: Image):
        print("call onnx wrapper")
        return wrapped.get_gender_and_age_from_image(pil_image)
