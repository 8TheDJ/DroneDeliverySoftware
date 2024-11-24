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
frame_counter = 0


while not arrived:

    # Capture a single frame using libcamera-still and pipe it into OpenCV
    # The command will capture a frame using libcamera and output it to stdout
    # Capture a single frame using libcamera-still and pipe it into OpenCV
    subprocess.run("sudo libcamera-still -o /tmp/captured_frame.jpg --nopreview", shell=True)

    # Load the captured frame into OpenCV
    frame = cv2.imread('/tmp/captured_frame.jpg')

    if frame is None:
        print("Error: Could not read the captured frame. Make sure it's saved correctly.")
    else:
        print(f"Captured Frame Shape: {frame.shape}")
        print(f"Frame Data (Top-left corner): {frame[0, 0]}")  # Check the pixel value of top-left corner
        # Save the original frame captured by libcamera
        cv2.imwrite('original_frame.jpg', frame)
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

            # Extract middle piece
            middle_piece = output[h_split:2*h_split, w_split:2*w_split]

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

            if percentage_above_threshold > 50:
                print("There is an object in front of me")
                objectinfront = 1
            
    # Check if one minute has passed
    elapsed_time = time.time() - start_time
    if elapsed_time >= 60:
        arrived = 1
        print("One minute has passed. This test is completed")
    frame_counter += 1
        