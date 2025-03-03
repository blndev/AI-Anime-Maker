import numpy as np              # for image manipulation e.g. sepia
from PIL import Image, ImageOps  # for image handling
import logging
import src.config as config
import cv2                      # prepare images for face recognition
import onnxruntime as ort       # for age and gender classification
# import insightface              # face recognition
from insightface.app import FaceAnalysis    # face boxes detection

# Set up module logger
logger = logging.getLogger(__name__)


class FaceAnalyzer:
    def __init__(self):
        logger.debug("Initializing FaceAnalyzer")
        # https://github.com/onnx/models/blob/main/validated/vision/body_analysis/emotion
        # _ferplus/model/emotion-ferplus-2.onnx
        # FIXME V3: we can have a switch here if GPU Memory >20GB(?) then onnx can run on GPU as well
        # ctx_id =0 GPU, -1=CPU, 1,2, select GPU to be used
        self.ctx_id = -1  # to save gpu memory
        # providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        providers = ['CPUExecutionProvider']
        try:
            # https://github.com/onnx/models/tree/main/validated/vision/body_analysis/age_gender
            self.age_classifier = ort.InferenceSession(
                config.get_modelfile_onnx_age_googlenet(),  providers=providers)  # emotions
            self.gender_classifier = ort.InferenceSession(
                config.get_modelfile_onnx_gender_googlenet(),  providers=providers)

            # https://github.com/deepinsight/insightface/tree/master/model_zoo
            self.face_detector = FaceAnalysis(name="buffalo_sc", providers=providers)
            self.face_detector.prepare(ctx_id=self.ctx_id, det_size=(512, 512))
            logger.debug("FaceAnalyzer ONNX initialization done")
        except Exception as e:
            logger.error("Error while initializing FaceAnalyzer: %s", str(e))
            logger.debug("Exception details:", exc_info=True)

    def _run_classifier(self, classifier, face_only_image):
        image = cv2.cvtColor(face_only_image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (224, 224))
        image_mean = np.array([104, 117, 123])
        image = image - image_mean
        image = np.transpose(image, [2, 0, 1])
        image = np.expand_dims(image, axis=0)
        image = image.astype(np.float32)
        input_name = classifier.get_inputs()[0].name
        values = classifier.run(None, {input_name: image})
        return values

    def _get_age(self, face_only_image):
        # def ageClassifier(orig_image):
        # Start from ORT 1.10, ORT requires explicitly setting the providers parameter
        # if you want to use execution providers other than the default CPU provider
        # (as opposed to the previous behavior of providers getting set/registered by default
        # based on the build flags) when instantiating InferenceSession.
        # For example, if NVIDIA GPU is available and ORT Python package is built with CUDA, then call API as following:
        # ort.InferenceSession(path/to/model, providers=['CUDAExecutionProvider'])
        ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        maxAgeList = [2, 6, 12, 20, 32, 43, 53, 100]
        minAgeList = [0, 4, 8, 15, 25, 38, 48, 60]

        ages = self._run_classifier(self.age_classifier, face_only_image)

        age = ageList[ages[0].argmax()]
        maxAge = maxAgeList[ages[0].argmax()]
        minAge = minAgeList[ages[0].argmax()]
        return age, minAge, maxAge

    # gender classification method
    def _is_male(self, face_only_image):
        gender_text = ['Male', 'Female']
        gender_male = [True, False]

        genders = self._run_classifier(self.gender_classifier, face_only_image)

        gender = gender_text[genders[0].argmax()]
        isMale = gender_male[genders[0].argmax()]
        return gender, isMale

    def get_gender_and_age_from_image(self, pil_image: Image):
        """ return values are a list of dictionaries. if len=0, then no face was detected"""
        retVal = []
        try:
            # reduce size if it is a big image to process it faster
            max_size = config.get_max_size()
            pil_image.thumbnail((max_size, max_size))
            # correct EXIF-Orientation!! very important
            pil_image = ImageOps.exif_transpose(pil_image)
            # face analysis needs a base RGB format
            cv2_image = np.array(pil_image.convert("RGB"))

            # convert to OpenCV conforme colors
            cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGBA2RGB)

            if len(cv2_image.shape) == 2:  # if gray make RGB
                cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_GRAY2BGR)

            # size = scaling to for face detection (smaller = faster)
            # if size is bigger then the image size, we got no detection so 512x512 is fine
            faces = self.face_detector.get(cv2_image)

            for face in faces:
                # print ("Face bbox", face['bbox'])
                x1, y1, x2, y2 = map(int, face.bbox)
                cropped_face = cv2_image[y1:y2, x1:x2]
                # cv2.imwrite(img=cropped_face, filename=f"./models/face_{x1}.jpg")

                gender_name, isMale = self._is_male(cropped_face)
                age, minAge, maxAge = self._get_age(cropped_face)

                retVal.append({
                    "age": age,
                    "minAge": minAge,
                    "maxAge": maxAge,
                    "isMale": isMale,
                    "isFemale": not isMale,
                    "gender": gender_name,
                    "smiling": False
                })
            logger.debug("Detected Age and Gender: %s", retVal)
        except Exception as e:
            logger.error("Error while detecting face: %s", str(e))
            logger.debug("Exception details:", exc_info=True)
        return retVal
