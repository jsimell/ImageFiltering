import cv2
import numpy as np
from PIL import Image

### This module contains the implementations of the image filters.
### Feel free to add any helper functions you need here as well.
### The params of each function depend on what parameter choices we give the user in the UI (e.g. strength, kernel size, etc.).
### The functions should return the filtered image.


def selective_colour(image, params):    # author: Elisavet Kouimtzidou
    # convert image
    img = np.array(image.convert("RGB"))
    # image in BGR
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    # image in HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # parameters    
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


def cartoon(image, params):    # author: Elisavet Kouimtzidou
    # convert image
    img = np.array(image.convert("RGB"))

    # parameters
    # NOTE:   edges intensity takes values from 20 to 100 where 
    #         100 is the least intense and 20 the most, so so the slider
    #         in the GUI is "backwards" to be more user friendly. 
    levels = params.get("color_levels", 3)
    
    ui_edges_intensity = params.get("edges", 50)
    # convert the "user-friendly" slider to the actual values
    edges_intensity = 120 - ui_edges_intensity
    
    # ----- blur -----
    blurred = cv2.GaussianBlur(img, (3,3), 1.5)

    # ----- edge detection -----
    
    # first, convert image to grayscale
    rows, cols, _ = img.shape
    gray = np.zeros((rows, cols), dtype=np.uint8)
    
    for i in range(rows):
        for j in range(cols):
            pixel = blurred[i,j]
            R = float(pixel[0])
            G = float(pixel[1])
            B = float(pixel[2])
            gray_val = 0.299*R + 0.587*G + 0.114*B
            gray[i,j] = gray_val

    # vertical edges
    kernelGy = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ])
    # convolution
    edge_vert = cv2.filter2D(gray, cv2.CV_32F, kernelGy)
    # normalisation
    if np.max(np.abs(edge_vert)) > 0:
        edge_vert = edge_vert / np.max(np.abs(edge_vert)) * 255

    # horizontal edges
    kernelGx = np.array([
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1]
    ])
    # convolution
    edge_hor = cv2.filter2D(gray, cv2.CV_32F, kernelGx)
    # normalisation
    if np.max(np.abs(edge_hor)) > 0:
        edge_hor = edge_hor / np.max(np.abs(edge_hor)) * 255

    # all edges
    edge = np.abs(edge_vert) + np.abs(edge_hor)
    edge = np.clip(edge, 0, 255).astype(np.uint8)
    
    # edges threshold
    _, edge = cv2.threshold(edge, edges_intensity, 255, cv2.THRESH_BINARY)

    # invert edges
    edge = cv2.bitwise_not(edge)


    # ----- color quantisation -----
    color = np.zeros((rows, cols, 3), dtype=np.uint8)
    # size of step
    step = 255 // levels
    # pixel-by-pixel loops for quantisation
    for i in range (rows):
        for j in range(cols):
            r, g, b = blurred[i,j]
            # quantisation
            r = round(r / step) * step
            g = round(g / step) * step
            b = round(b / step) * step
            
            color[i,j] = [r,g,b]
            
    color = np.clip(color, 0, 255).astype(np.uint8)
    
    # add the edges to the final image
    cartoon = cv2.bitwise_and(color, color, mask=edge)
    
    return Image.fromarray(cartoon)


def bilateral(image, params):    # author: Clara Schindler
    # convert image to float RGB in [0, 1]
    img = np.array(image.convert("RGB"), dtype=np.float32) / 255.0

    # get parameters from UI
    radius = 5
    sigma_spatial = float(params.get("sigma_spatial", 5.0))
    sigma_range = float(params.get("sigma_range", 0.15))

    # ensure parameters are within valid ranges
    sigma_spatial = max(1e-6, sigma_spatial)
    sigma_range = max(1e-6, sigma_range)

    height, width, _ = img.shape
    output = np.zeros_like(img, dtype=np.float32)

    # reflect padding for image borders
    padded = np.pad(img, ((radius, radius), (radius, radius), (0, 0)), mode="reflect")

    # precompute spatial gaussian weights
    offsets = np.arange(-radius, radius + 1, dtype=np.float32)
    yy, xx = np.meshgrid(offsets, offsets, indexing="ij")
    spatial_weights = np.exp(-(xx * xx + yy * yy) / (2.0 * sigma_spatial * sigma_spatial)).astype(np.float32)

    # bilateral filter loop
    for row in range(height):
        for col in range(width):
            # extract the patch around the current pixel
            patch = padded[row:row + 2 * radius + 1, col:col + 2 * radius + 1, :]
            center = padded[row + radius, col + radius, :]

            # color distance in RGB to compute range weights
            diff = patch - center
            dist2 = np.sum(diff * diff, axis=2)
            range_weights = np.exp(-dist2 / (2.0 * sigma_range * sigma_range)).astype(np.float32)

            # combine spatial and range weights
            weights = spatial_weights * range_weights
            weight_sum = np.sum(weights)

            # apply weights to the patch and normalize
            if weight_sum > 1e-12:
                output[row, col, :] = np.sum(patch * weights[:, :, None], axis=(0, 1)) / weight_sum
            else:
                output[row, col, :] = center

    output = np.clip(output, 0.0, 1.0)
    output = (output * 255.0).astype(np.uint8)

    return Image.fromarray(output)


def vintage_film(image, params):    # author: Clara Schindler
    # convert image to RGB (handle grayscale images safely)
    img = np.array(image.convert("RGB")).astype(np.float32) / 255.0

    # get parameters from UI
    contrast = params.get("contrast", 0.75)
    warmth = params.get("warmth", 0.25)
    noise_amount = params.get("noise_amount", 0.05)
    noise_clip = float(params.get("noise_clip", 1.5))

    # ensure parameters are within valid ranges
    contrast = np.clip(contrast, 0.4, 1.2)
    noise_amount = np.clip(noise_amount, 0.0, 0.2)
    warmth = np.clip(warmth, 0.0, 0.6)
    noise_clip = np.clip(noise_clip, 0.0, 1.0)

    # lower contrast around midpoint 0.5
    vintage = (img - 0.5) * contrast + 0.5
    # lighten midtones to compensate for contrast reduction
    vintage = np.clip(vintage * 1.15, 0.0, 1.0)

    # warm tone shift (more red and green, less blue)
    warm_gain = np.array([1.0 + warmth, 1.0 + 0.2 * warmth, 1.0], dtype=np.float32)
    vintage = np.clip(vintage * warm_gain, 0.0, 1.0)

    # add gaussian grain noise
    noise = np.random.normal(0.0, noise_amount, vintage.shape).astype(np.float32)

    # clip extremes so pixels don't jump to unnatural values
    clip_val = noise_clip * noise_amount
    noise = np.clip(noise, -clip_val, clip_val)

    # add noise to the image
    vintage = np.clip(vintage + noise, 0.0, 1.0)

    # convert back to PIL image
    vintage = (vintage * 255.0).astype(np.uint8)
    
    return Image.fromarray(vintage)


def pencil_sketch(image, params):    # author: Jiri Simell
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

