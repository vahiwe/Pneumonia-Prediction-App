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
