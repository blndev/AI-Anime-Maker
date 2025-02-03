import os
import requests                 # for downloads of files
from datetime import datetime   # for timestamp
import numpy as np              # for image manipulation e.g. sepia
from PIL import Image, ImageOps # for image handling
from hashlib import sha1        # generate image hash
import cv2                      # prepare images for face recognition
import onnxruntime as ort       # for age and gender classification
#import insightface              # face recognition
from insightface.app import FaceAnalysis    # face boxes detection
import src.config as config

def get_all_local_models(model_folder: str, extension: str = ".safetensors"):
    """read all local models to the system"""
    safetensors_files = []
    try:
        for root, _, files in os.walk(model_folder, followlinks=True):
            for file in files:
                if file.endswith(extension):
                    relative_path = "./" + os.path.relpath(os.path.join(root, file))
                    safetensors_files.append(relative_path)
        print(safetensors_files)
    except Exception as e:
        print(e)
    return safetensors_files


def download_file_if_not_existing(url, local_path):
    # Check if the file already exists
    if not os.path.exists(local_path):
        print(f"Downloading {local_path}... this can take some minutes")
        response = requests.get(url)
        response.raise_for_status()  # Check for download errors

        # Create directory if it does not exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Write the file to the specified path
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded {local_path} successfully.")
    else:
        print(f"File {local_path} already exists.")


def save_image_as_file(image: Image.Image, dir: str):
    """
    saves a image as JPEG to the given directory and uses the SHA1 as filename
    return value is the hash
    """
    try:
        if not os.path.exists(dir):
            os.makedirs(dir)
        # if we use imageEditor from Gradio:
        # try:
        #     image = image['background'] # if we use editor field
        # except:
        #     print("seems no background in image dict")
        #     print (image)
        # Convert the image to bytes and compute the SHA-1 hash
        image_bytes = image.tobytes()
        hash = sha1(image_bytes).hexdigest()
        filetype = "jpg"
        filename_hash = hash + "."+filetype
        file_path = os.path.join(dir, filename_hash)

        if not os.path.exists(file_path):
            image.save(file_path, format="JPEG")

        if config.DEBUG:
            print(f"Image saved to \"{file_path}\"")
        return hash
    except Exception as e:
        print(f"Error while saving image to cache:\n{e}")
        return None


def save_image_with_timestamp(image, folder_path, ignore_errors=False, reference=""):
    """
    saves a image in a given folder and returns the used path
    refernce: could be the SHA1 from source image to make a combined filename
    """
    try:
        # Create the folder if it does not exist
        os.makedirs(folder_path, exist_ok=True)

        # Generate a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        separator = "" if reference == "" else "-"
        # Create the filename with the timestamp
        filename = f"{reference}{separator}{timestamp}.png"  # Change the extension as needed

        # Full path to save the image
        file_path = os.path.join(folder_path, filename)

        # Save the image
        image.save(file_path)
        return file_path
    except Exception as e:
        print(f"save image failed: {e}")
        if not ignore_errors:
            raise e


def image_convert_to_sepia(input: Image):
    """converts a image to a sepia ton image"""

    img = np.array(input)
    sepia_filter = np.array([
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])
    sepia_img = img @ sepia_filter.T
    sepia_img = np.clip(sepia_img, 0, 255)
    sepia_img = sepia_img.astype(np.uint8)
    return Image.fromarray(sepia_img)

#emotions
#https://github.com/onnx/models/blob/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-2.onnx

#TODO: load model names from config

#https://github.com/onnx/models/tree/main/validated/vision/body_analysis/age_gender
age_classifier = ort.InferenceSession('./models/onnx/age_googlenet.onnx')
def age_is_below_ageClassifier(face_only_image):
    #def ageClassifier(orig_image):
    # Start from ORT 1.10, ORT requires explicitly setting the providers parameter if you want to use execution providers
    # other than the default CPU provider (as opposed to the previous behavior of providers getting set/registered by default
    # based on the build flags) when instantiating InferenceSession.
    # For example, if NVIDIA GPU is available and ORT Python package is built with CUDA, then call API as following:
    # ort.InferenceSession(path/to/model, providers=['CUDAExecutionProvider'])
    ageList=['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
    maxAgeList=[2, 6, 12, 20, 32, 43, 53, 100]
    minAgeList=[0, 4, 8, 15, 25, 38, 48, 60]
    image = cv2.cvtColor(face_only_image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224))
    image_mean = np.array([104, 117, 123])
    image = image - image_mean
    image = np.transpose(image, [2, 0, 1])
    image = np.expand_dims(image, axis=0)
    image = image.astype(np.float32)

    input_name = age_classifier.get_inputs()[0].name
    ages = age_classifier.run(None, {input_name: image})
    age = ageList[ages[0].argmax()]
    maxAge = maxAgeList[ages[0].argmax()]
    minAge = minAgeList[ages[0].argmax()]
    return age, minAge, maxAge

gender_classifier = ort.InferenceSession('./models/onnx/gender_googlenet.onnx')

# gender classification method
def isMale_genderClassifier(face_only_image):
    genderListText=['Male','Female']
    genderListBool=[True,False]
    image = cv2.cvtColor(face_only_image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224))
    image_mean = np.array([104, 117, 123])
    image = image - image_mean
    image = np.transpose(image, [2, 0, 1])
    image = np.expand_dims(image, axis=0)
    image = image.astype(np.float32)

    input_name = gender_classifier.get_inputs()[0].name
    genders = gender_classifier.run(None, {input_name: image})
    genderText = genderListText[genders[0].argmax()]
    isMale = genderListBool[genders[0].argmax()]
    return genderText, isMale


def get_gender_and_age_from_image(pil_image: Image):
    """ return values are a list of dictionaries. if len=0, then no face was detected"""
    retVal = []
    if config.SKIP_AI and False: return retVal

    try:
        face_detector = FaceAnalysis(name="buffalo_sc")  # https://github.com/deepinsight/insightface/tree/master/model_zoo
        # correct EXIF-Orientation!! very important
        pil_image = ImageOps.exif_transpose(pil_image)
        cv2_image = np.array(pil_image.convert("RGB"))

        # convert to OpenCV conforme colors
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGBA2RGB)

        if len(cv2_image.shape) == 2:  # if gray make RGB
            cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_GRAY2BGR)
        #ctx_id =0 GPU, -1=CPU, 1,2, select GPU to be used
        # size = scaling to for face detection (smaller = faster)
        face_detector.prepare(ctx_id=0, det_size=(1024,1024))
        faces = face_detector.get(cv2_image)

        for face in faces:
            #print ("Face bbox", face['bbox'])
            x1, y1, x2, y2 = map(int, face.bbox)
            cropped_face = cv2_image[y1:y2, x1:x2]
            #cv2.imwrite(img=cropped_face, filename=f"./models/face_{x1}.jpg")

            gender_name, isMale = isMale_genderClassifier(cropped_face)
            age, minAge, maxAge = age_is_below_ageClassifier(cropped_face)

            retVal.append({
                "age": age,
                "minAge": minAge,
                "maxAge": maxAge,
                "isMale": isMale,
                "isFemale": not isMale,
                "gender": gender_name,
                "smiling": False
            })
        if config.DEBUG:
            print("Detected Age and Gender: ", retVal)
    except Exception as e:
        print (f"Error while decting face: {e}")
    return retVal

if __name__ == "__main__":
    img = Image.open("unittests/testdata/face.png")
    v = get_gender_and_age_from_image(img)
    print(v)
