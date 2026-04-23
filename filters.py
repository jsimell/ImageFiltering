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
    ui_strength = params.get("strength", 1.0)
    # Convert the user-friendly slider value to the actual strength value used in the kernel
    strength = 6.0 - ui_strength

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
    # convert image
    img = np.array(image.convert("RGB"))
    # image in BGR
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    # image in HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # parameters
    # NOTE: the tolerance should take values from 0.0 to 30.0, initial value 5.0
    #       and the initial color could be red (#ff0000)
    #
    # Also, it would be best if the user would have a simple slider to choose
    # only the hue of the color and not the saturation/value, in order to only work 
    # with fully saturated, clear colors, since the function chooses the colors 
    # to maintain based only on their hue.
    # (the target color still in hexadecimal, like now)
    
    color_hex = params.get("color", "ff0000")
    tolerance = params.get("tolerance", 5.0)

    # convert color_hex from hexadecimal to rgb
    color_hex = color_hex.lstrip('#')
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16)
    b = int(color_hex[4:6], 16)

    # convert to bgr and hsv color
    color_bgr = np.uint8([[[b, g, r]]])
    color_hsv = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2HSV)

    target_hue = color_hsv[0][0][0]

    h, s, v = cv2.split(hsv)

    # loops for pixel-by-pixel iteration
    rows, cols, _ = img.shape
    for i in range(rows):
        for j in range(cols):
            # hue saturation and value of the pixel
            hue = h[i,j]
            sat = s[i,j]
            val = v[i,j]

            # check if the pixel's hue is within the tolerance to the target hue
            
            # in case of being near red hues which are at the ends of the spectrum (h~0 or h~180)
            if target_hue < tolerance:
                in_range = ( (hue <= target_hue + tolerance) or (hue >= 180 - tolerance + target_hue) )
            elif target_hue > 180 - tolerance:
                in_range = ( (hue >= target_hue - tolerance) or (hue <= + tolerance + target_hue -180) )
            # not at the ends of the spectrum
            else:
                in_range = ( hue <= target_hue + tolerance and hue >= target_hue - tolerance)

            # check if NOT within the above range and NOT within a saturation and value limit
            if not (in_range and  sat > 50 and val > 50):
                # convert to grayscale
                pixel = img[i,j]
                B = float(pixel[0])
                G = float(pixel[1])
                R = float(pixel[2])
                gray_val = 0.299*R + 0.587*G + 0.114*B
                img[i,j] = [gray_val, gray_val, gray_val]

    # convert image back to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return Image.fromarray(img)

def cartoon(image, params):
    # IMPLEMENT
    pass

def bilateral(image, params):
    # IMPLEMENT
    pass

def vintage_film(image, params):
    # IMPLEMENT
    pass

def pencil_sketch(image, params):
    src = np.array(image)
    intensity = int(params.get("intensity", 3))
    intensity = max(1, min(intensity, 5))

    # We use an internal mapping that maps the user-friendly intensity value (1-5) to actual 
    # parameter values for kernel size, sigma, and scale.
    intensity_mapping = {
        1: {"kernel_size": 3, "sigma": 0.8, "scale": 192},
        2: {"kernel_size": 5, "sigma": 1.2, "scale": 208},
        3: {"kernel_size": 7, "sigma": 1.8, "scale": 224},
        4: {"kernel_size": 9, "sigma": 2.4, "scale": 240},
        5: {"kernel_size": 11, "sigma": 3.0, "scale": 255},
    }

    kernel_size = intensity_mapping[intensity]["kernel_size"]
    sigma = intensity_mapping[intensity]["sigma"]
    scale = intensity_mapping[intensity]["scale"]


    # Convert the image to a grayscale openCV image (if it's not already in grayscale)
    if not len(src.shape) == 2: # if the image is not already grayscale
        grayscale = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)
    else:
        grayscale = src

    # Convert the grayscale image to inverted grayscale
    inverted = 255.0 - grayscale.astype(np.float32)
    
    # Apply a Gaussian blur to the inverted grayscale image
    # Here we use a separate pass for horizontal and vertical blurring for efficiency
    kernel_1D = np.zeros((kernel_size), dtype=np.float32)
    for i in range(kernel_size):
        kernel_1D[i] = np.exp(-0.5 * ((i - kernel_size // 2) / sigma) ** 2)
    kernel_1D /= np.sum(kernel_1D) # Normalize the kernel

    # Horizontal pass
    rows, cols = grayscale.shape
    blurred_horizontal = np.zeros_like(inverted, dtype=np.float32)
    for i in range(rows):
        for j in range(cols):
            sum = 0
            for n in range(kernel_size):
                p = j - kernel_size // 2 + n
                # Use edge padding for out-of-bounds indices
                p = max(0, min(p, cols - 1))
                sum += inverted[i, p] * kernel_1D[n]
            blurred_horizontal[i, j] = sum

    # Vertical pass
    blurred = np.zeros_like(blurred_horizontal, dtype=np.float32)
    for i in range(rows):
        for j in range(cols):
            sum = 0
            for n in range(kernel_size):
                p = i - kernel_size // 2 + n
                # Use edge padding for out-of-bounds indices
                p = max(0, min(p, rows - 1))
                sum += blurred_horizontal[p, j] * kernel_1D[n]
            blurred[i, j] = sum

    # Invert image back
    inverted_back = np.clip(255.0 - blurred, 0.1, 255.0)

    # Perform element-wise division between the inverted back image and the original grayscale image
    sketch = np.zeros_like(inverted_back, dtype=np.float32)
    for i in range(rows):
        for j in range(cols):
            sketch[i, j] = min(255, (float(grayscale[i, j]) * scale) / inverted_back[i, j])

    return Image.fromarray(sketch.astype(np.uint8))

