import json
import numpy as np
import sys
import os
import requests
from PIL import Image
import numpy as np
from skimage import transform

IMG_HEIGHT = 100
IMG_WIDTH = 100


def load(filename):
    np_image = Image.open(filename)
    np_image = np.array(np_image).astype('float32')/255
    # (IMG_HEIGHT, IMG_WIDTH, 3))
    np_image = transform.resize(np_image, (IMG_HEIGHT, IMG_WIDTH, 3))
    np_image = np.expand_dims(np_image, axis=0)
    return np_image


arr = os.listdir("./PNEUMONIA_val")
print(len(arr))
# file_name = sys.argv[1]
# # Decoding and pre-processing image
# try:
#     img = load(file_name)
# except FileNotFoundError:
#     print("File not Found")
#     sys.exit()

# # Creating payload for TensorFlow serving request
# data = json.dumps({"signature_name": "serving_default",
#                    "instances": img.tolist()})

# # Making POST request
# headers = {"content-type": "application/json"}
# json_response = requests.post(
#     'http://34.82.175.150:8501/v1/models/pybenders_model:predict', data=data, headers=headers)

# # Decoding results from TensorFlow Serving server
# predictions = json_response.json()['predictions'][0][0]
# print(predictions)
