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

# Initialiseer variabelen
objectinfront = 0  # Variabele om te controleren of er een object voor de camera is
arrived = 0  # Dit bepaalt wanneer het script stopt (na 2 minuten)
start_time = time.time()  # Starttijd opnemen om de tijdsduur te meten
threshold = 500  # Diepte-drempelwaarde om te bepalen of er een object voor de camera is
percentagethreshold = 50  # Drempel voor percentage van diepte boven een bepaalde waarde
frame_counter = 0  # Teller voor het aantal frames

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

    print(f"Captured Frame Shape: {frame.shape}")  # Toon de vorm van het frame
    print(f"Frame Data (Top-left corner): {frame[0, 0]}")  # Toon de pixelwaarde van de bovenste linkerhoek

    # Sla het originele frame op met een unieke naam op basis van de frame-counter
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

        # Extractie van het middelste stuk van de dieptekaart
        middle_piece = output[h_split:2*h_split, w_split:2*w_split]

        # Genereer bestandsnamen voor de gekleurde dieptekaart en het middelste stuk
        colored_depth_map_filename = f'depth_map_colored_{frame_counter}.png'
        colored_middle_piece_filename = f'middle_piece_colored_{frame_counter}.png'

        # Sla de gekleurde dieptekaart en het middelste stuk op als afbeeldingen voor visualisatie
        plt.imsave(colored_depth_map_filename, output, cmap='plasma')
        plt.imsave(colored_middle_piece_filename, middle_piece, cmap='plasma')

        # Controleer of er een object voor de camera is in het middelste stuk
        total_pixels = middle_piece.size
        pixels_above_threshold = np.sum(middle_piece > threshold)
        percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100

        print(f"{percentage_above_threshold:.2f}% van de pixels in het middelste stuk hebben een diepte boven de drempel van {threshold}")

        # Controleer of er een object voor de camera is in het volledige stuk
        total_pixels2 = output.size
        pixels_above_threshold2 = np.sum(output > threshold)
        percentage_above_threshold2 = (pixels_above_threshold2 / total_pixels2) * 100

        print(f"{percentage_above_threshold2:.2f}% van de pixels in de hele afbeelding hebben een diepte boven de drempel van {threshold}")

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
