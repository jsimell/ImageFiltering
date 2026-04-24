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
    # convert image to numpy RGB float in [0, 1]
    img = np.array(image).astype(np.float32) / 255.0

    # parameter defaults
    # Keep backward compatibility with current UI ("param1" in [0, 10]).
    # intensity: 0 -> subtle effect, 1 -> stronger effect
    intensity = np.clip(params.get("param1", 5.0) / 10.0, 0.0, 1.0)

    contrast = params.get("contrast", 1.0 - 0.35 * intensity)
    noise_amount = params.get("noise_amount", 0.015 + 0.045 * intensity)
    warmth = params.get("warmth", 0.12 + 0.23 * intensity)
    warm_opacity = params.get("warm_opacity", 0.08 + 0.27 * intensity)

    contrast = np.clip(contrast, 0.4, 1.2)
    noise_amount = np.clip(noise_amount, 0.0, 0.2)
    warmth = np.clip(warmth, 0.0, 0.6)
    warm_opacity = np.clip(warm_opacity, 0.0, 0.6)

    # 1) lower contrast around midpoint 0.5
    vintage = (img - 0.5) * contrast + 0.5

    # 2) warm tone shift (more red/green, less blue)
    # RGB channel gains
    warm_gain = np.array([1.0 + warmth, 1.0 + 0.5 * warmth, 1.0 - 0.7 * warmth], dtype=np.float32)
    warm_shifted = np.clip(vintage * warm_gain, 0.0, 1.0)

    # 3) warm color mask overlay
    warm_mask_color = np.array([245.0, 210.0, 150.0], dtype=np.float32) / np.float32(255.0)
    warm_mask = np.ones_like(warm_shifted, dtype=np.float32) * warm_mask_color
    alpha = np.float32(warm_opacity)
    vintage = np.clip(
        warm_shifted.astype(np.float32) * (np.float32(1.0) - alpha) + warm_mask * alpha,
        0.0,
        1.0,
    )

    # 4) film grain noise
    noise = np.random.normal(0.0, noise_amount, vintage.shape).astype(np.float32)
    vintage = np.clip(vintage + noise, 0.0, 1.0)

    # convert back to PIL image
    vintage = (vintage * 255.0).astype(np.uint8)
    
    return Image.fromarray(vintage)
