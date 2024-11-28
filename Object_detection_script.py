import cv2
import torch
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import time

# Laad het MiDaS model voor dieptevoorspelling
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')  # Zet het model naar CPU (of 'cuda' voor GPU)
midas.eval()  # Zet het model in evaluatiemodus

# Input transformatie pipeline voor beeldverwerking
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

# Initialiseer variabelen
objectinfront = 0  # Houdt bij of er een object voor de camera is
arrived = 0  # De test stopt pas als dit op 1 staat (na 2 minuten)
start_time = time.time()  # Begin de tijd om te meten hoelang de test duurt
threshold = 372.5  # Drempel voor diepte, afgeleid uit eerder gevonden waarde
percentagethreshold = 10  # Drempelpercentage voor het aantal pixels boven de diepte-drempel
frame_counter = 0  # Teller voor het aantal frames

while not arrived:  # De test blijft draaien tot de tijd voorbij is (2 minuten)

    # Maak een enkel frame van de camera met 'libcamera-still' en pipet deze naar OpenCV
    subprocess.run("sudo libcamera-still -o /tmp/captured_frame.jpg --nopreview", shell=True)

    # Laad het vastgelegde frame in OpenCV
    frame = cv2.imread('/tmp/captured_frame.jpg')

    if frame is None:  # Controleer of het frame correct is geladen
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
            prediction = midas(imgbatch)  # Verkrijg de voorspelde dieptekaart
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],  # Verander de grootte naar die van het originele frame
                mode='bicubic',
                align_corners=False
            ).squeeze()

            output = prediction.cpu().numpy()  # Converteer naar NumPy array voor verdere verwerking

            # Verdeel de dieptekaart in 9 stukken en analyseer het middelste stuk
            h, w = output.shape
            h_split, w_split = h // 3, w // 3

            # Haal het middelste stuk eruit
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

            # Als het percentage van pixels boven de drempel groter is dan het percentage drempel
            if percentage_above_threshold > percentagethreshold:
                print("Er is een object voor de camera.")
                objectinfront = 1  # Zet de variabele op 1 om aan te geven dat er een object is

    # Controleer of er 2 minuten zijn verstreken
    elapsed_time = time.time() - start_time  # Bereken de verstreken tijd
    if elapsed_time >= 120:  # Als er 120 seconden (2 minuten) zijn verstreken
        arrived = 1  # Zet 'arrived' op 1 om de test te beëindigen
        print("Er zijn 2 minuten verstreken. De test is voltooid.")

    frame_counter += 1  # Verhoog de frame-teller voor elke iteratie
