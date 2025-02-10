import numpy as np              # for image manipulation e.g. sepia
from PIL import Image, ImageOps # for image handling
import cv2                      # prepare images for face recognition
import onnxruntime as ort       # for age and gender classification
#import insightface              # face recognition
from insightface.app import FaceAnalysis    # face boxes detection
import src.config as config


#emotions
#https://github.com/onnx/models/blob/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-2.onnx
#ctx_id =0 GPU, -1=CPU, 1,2, select GPU to be used
ctx_id=1

#https://github.com/onnx/models/tree/main/validated/vision/body_analysis/age_gender
age_classifier = ort.InferenceSession(config.get_modelfile_onnx_age_googlenet())
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

gender_classifier = ort.InferenceSession(config.get_modelfile_onnx_gender_googlenet())

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
    try:
        face_detector = FaceAnalysis(name="buffalo_sc")  # https://github.com/deepinsight/insightface/tree/master/model_zoo
        # correct EXIF-Orientation!! very important
        max_size = config.get_max_size()
        pil_image.thumbnail((max_size, max_size))
        pil_image = ImageOps.exif_transpose(pil_image)
        cv2_image = np.array(pil_image.convert("RGB"))

        # convert to OpenCV conforme colors
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGBA2RGB)

        if len(cv2_image.shape) == 2:  # if gray make RGB
            cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_GRAY2BGR)
        #ctx_id =0 GPU, -1=CPU, 1,2, select GPU to be used
        #size = scaling to for face detection (smaller = faster)
        #if size is bigger then the image size, we got no detection so 512x512 is fine
        face_detector.prepare(ctx_id=ctx_id, det_size=(512,512))
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