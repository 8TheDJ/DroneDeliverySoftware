import cv2
import torch
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import time

# Load the MiDaS model
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')
midas.eval()

# Input transformation pipeline
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

objectinfront = 0
arrived = 0
start_time = time.time()  # Record the starting time
threshold = 372.5  # Drempelwaarde voor de diepte, gevonden met "Object_detection_script_for_laptop_imageuploader.py"
percentagethreshold = 10 #drempelpercentage, gevonden met "Object_detection_script_for_laptop_imageuploader.py"
frame_counter = 0

# Open the webcam (device index 0 for most systems)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

while not arrived:

    # Capture a single frame from the webcam
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from webcam.")
        continue

    original_frame_filename = f'original_frame_{frame_counter}.png'
    cv2.imwrite(original_frame_filename, frame)

    # Transform input for MiDaS
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
    imgbatch = transform(img).to('cpu')

        # Make a prediction
    with torch.no_grad():
            prediction = midas(imgbatch)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],
                mode='bicubic',
                align_corners=False
            ).squeeze()

            output = prediction.cpu().numpy()

            # Split depth map into 9 pieces and analyze the middle piece
            h, w = output.shape
            h_split, w_split = h // 3, w // 3

            # Extract all pieces
            middle_piece = output[h_split:2*h_split, w_split:2*w_split]

            # Check for object directly in front in the middle piece
            total_pixels = middle_piece.size
            pixels_above_threshold = np.sum(middle_piece > threshold)
            percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100

            if percentage_above_threshold > percentagethreshold:
                print("There is an object in front of me")
                objectinfront = 1
            
    # Check if one minute has passed
    elapsed_time = time.time() - start_time
    if elapsed_time >= 120:
        arrived = 1
        print("2 minutes have passed. This test is completed")
    frame_counter += 1
        