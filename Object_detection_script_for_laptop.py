import cv2
import torch
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import time

# Laad het MiDaS model voor dieptevoorspelling
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')  # Het model naar de CPU verplaatsen (gebruik 'cuda' voor GPU)
midas.eval()  # Zet het model in evaluatiemodus

# Input transformatie pipeline voor beeldverwerking
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

objectinfront = 0
arrived = 0
start_time = time.time()  # Record the starting time
threshold = 500  # Depth threshold
percentagethreshold = 50 #threshold for percentage of depth above a certain threshold
frame_counter = 0

# Open de webcam (meestal apparaat index 0)
cap = cv2.VideoCapture(0)
if not cap.isOpened():  # Controleer of de webcam geopend kan worden
    print("Error: Could not open webcam.")
    exit()

while not arrived:  # Blijf doorgaan tot de test is voltooid (na 2 minuten)

    # Capture een enkel frame van de webcam
    ret, frame = cap.read()
    if not ret:  # Controleer of het frame goed is vastgelegd
        print("Error: Could not read frame from webcam.")
        continue

    print(f"Captured Frame Shape: {frame.shape}")
    print(f"Frame Data (Top-left corner): {frame[0, 0]}")  # Check the pixel value of top-left corner

    original_frame_filename = f'original_frame_{frame_counter}.png'
    cv2.imwrite(original_frame_filename, frame)

    # Transformeer het frame voor het MiDaS-model (om te zetten naar RGB voor verwerking)
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imgbatch = transform(img).to('cpu')

    # Maak een dieptevoorspelling met MiDaS
    with torch.no_grad():
        prediction = midas(imgbatch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img.shape[:2],
            mode='bicubic',
            align_corners=False
        ).squeeze()

        output = prediction.cpu().numpy()

        # Verdeel de dieptekaart in 9 stukken en analyseer het middelste stuk
        h, w = output.shape
        h_split, w_split = h // 3, w // 3

            # Extract all pieces
            middle_piece = output[h_split:2*h_split, w_split:2*w_split]

            # Save the depth map and middle piece with unique filenames depending on the frame it is at
            colored_depth_map_filename = f'depth_map_colored_{frame_counter}.png'
            colored_middle_piece_filename = f'middle_piece_colored_{frame_counter}.png'


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
            print("Er is een object voor de camera.")
            objectinfront = 1  # Zet de variabele op 1 om aan te geven dat er een object voor de camera is

    # Controleer of er 2 minuten zijn verstreken
    elapsed_time = time.time() - start_time
    if elapsed_time >= 120:  # Stop na 2 minuten
        arrived = 1
        print("Er zijn 2 minuten verstreken. De test is voltooid.")
    
    frame_counter += 1  # Verhoog de frame-teller voor elke iteratie

cap.release()  # Zorg ervoor dat de webcam wordt vrijgegeven nadat de test is voltooid
