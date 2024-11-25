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
threshold = 500  # Depth threshold
percentagethreshold = 50 #threshold for percentage of depth above a certain threshold
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

    print(f"Captured Frame Shape: {frame.shape}")
    print(f"Frame Data (Top-left corner): {frame[0, 0]}")  # Check the pixel value of top-left corner

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
            one_piece = output[h_split:1*h_split, w_split:1*w_split]
            two_piece = output[h_split:2*h_split, w_split:1*w_split]
            three_piece = output[h_split:3*h_split, w_split:1*w_split]
            four_piece = output[h_split:1*h_split, w_split:2*w_split]
            six_piece = output[h_split:3*h_split, w_split:2*w_split]
            seven_piece = output[h_split:1*h_split, w_split:3*w_split]
            eight_piece = output[h_split:2*h_split, w_split:3*w_split]
            nine_piece = output[h_split:3*h_split, w_split:3*w_split]

            # Save the depth map and middle piece with unique filenames depending on the frame it is at
            depth_map_filename = f'depth_map_{frame_counter}.png'
            middle_piece_filename = f'middle_piece_{frame_counter}.png'
            colored_depth_map_filename = f'depth_map_colored_{frame_counter}.png'
            colored_middle_piece_filename = f'middle_piece_colored_{frame_counter}.png'

            cv2.imwrite(depth_map_filename, output)  # Save the full depth map
            cv2.imwrite(middle_piece_filename, middle_piece)  # Save the middle piece

            # Save the depth map and middle piece as colored images for visualization
            plt.imsave(colored_depth_map_filename, output, cmap='plasma')  # Colored depth map
            plt.imsave(colored_middle_piece_filename, middle_piece, cmap='plasma')  # Colored middle piece

            # Check for object directly in front in the middle piece
            total_pixels = middle_piece.size
            pixels_above_threshold = np.sum(middle_piece > threshold)
            percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100

            print(f"{percentage_above_threshold:.2f}% of pixels in the middle piece have a depth value above {threshold}")

            # Check for object directly in front in the whole piece
            total_pixels2 = output.size
            pixels_above_threshold2 = np.sum(output > threshold)
            percentage_above_threshold2 = (pixels_above_threshold2 / total_pixels2) * 100

            print(f"{percentage_above_threshold2:.2f}% of pixels in the whole piece have a depth value above {threshold}")

            if percentage_above_threshold > percentagethreshold:
                print("There is an object in front of me")
                objectinfront = 1
            
    # Check if one minute has passed
    elapsed_time = time.time() - start_time
    if elapsed_time >= 5:
        arrived = 1
        print("5/60 minutes have passed. This test is completed")
    frame_counter += 1
        