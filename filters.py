import cv2
import numpy as np
from PIL import Image

### This module contains the implementations of the image filters.
### Feel free to add any helper functions you need here as well.
### The params of each function depend on what parameter choices we give the user in the UI (e.g. strength, kernel size, etc.).
### The functions should return the filtered image.

def sharpness(image, params):
    
    # convert image to numpy BGR
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    sharp = np.zeros_like(img, dtype=np.float32)

    # Parameters
    # NOTE: strength should take values from -1.0 (-0.9999 to avoid division by 0) to 4.0,
    #       where 4 is the least sharp and -1 is the sharpest,
    #       so the slider in the GUI could be "backwards" to be more user friendly.
    strength = params.get("strength", 1.0)

    # kernel to do the covolution
    kernel = 1/(1+strength) * np.array([
        [0, -1, 0],
        [-1, 5 + strength, -1],
        [0, -1, 0]
    ], dtype=np.float32)
    # NOTE: the factor 1/(1+strength) is to "normalise"
    #       the resulting brightness of the image

    sharp = cv2.filter2D(img, -1, kernel)

    # convert the image back to the initial format
    sharp = cv2.cvtColor(sharp, cv2.COLOR_BGR2RGB)

    return Image.fromarray(sharp)
    

def selective_colour(image, params):
    # IMPLEMENT
    pass

def gaussian_blur(image, params):
    # IMPLEMENT
    pass

def vintage_film(image, params):
    # IMPLEMENT
    pass
