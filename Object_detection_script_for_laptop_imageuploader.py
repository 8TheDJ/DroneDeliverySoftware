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
threshold = 500  # Depth threshold
percentagethreshold = 50 #threshold for percentage of depth above a certain threshold


frame = cv2.imread("C:/Users/itayh/Downloads/white_wall_test.jpg") #path to your image
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
            colored_depth_map_filename = f'depth_map_colored.png'
            colored_middle_piece_filename = f'middle_piece_colored.png'


            # Save the depth map and middle piece as colored images for visualization
            plt.imsave(colored_depth_map_filename, output, cmap='plasma')  # Colored depth map
            plt.imsave(colored_middle_piece_filename, middle_piece, cmap='plasma')  # Colored middle piece

            
            
            for i in range(5):
                threshold = 100*i + 300
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

                if percentage_above_threshold > 70:
                    print(f"There is an object in front of me ({threshold}, 70%)")
                    objectinfront = 1

                if percentage_above_threshold > 60:
                    print(f"There is an object in front of me ({threshold}, 60%)")
                    objectinfront = 1
                    
                if percentage_above_threshold > 50:
                    print(f"There is an object in front of me ({threshold}, 50%)")
                    objectinfront = 1

                if percentage_above_threshold > 40:
                    print(f"There is an object in front of me ({threshold}, 40%)")
                    objectinfront = 1

                if percentage_above_threshold > 30:
                    print(f"There is an object in front of me ({threshold}, 30%)")
                    objectinfront = 1