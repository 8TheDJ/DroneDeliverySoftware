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
        # Toon de vorm van het frame en de pixelwaarde van de bovenste linkerhoek voor debugging
        print(f"Captured Frame Shape: {frame.shape}")
        print(f"Frame Data (Top-left corner): {frame[0, 0]}") 

        # Sla het originele frame op
        cv2.imwrite('original_frame.jpg', frame)

        # Transformeer het frame voor het MiDaS model (omzetten naar RGB)
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converteer van BGR naar RGB
        imgbatch = transform(img).to('cpu')  # Pas de transformatie toe en stuur naar CPU

        # Maak een dieptevoorspelling met MiDaS
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

            # Genereer bestandsnamen voor de gekleurde dieptekaart en het middelste stuk
            colored_depth_map_filename = f'depth_map_colored_{frame_counter}.png'
            colored_middle_piece_filename = f'middle_piece_colored_{frame_counter}.png'

            # Sla de gekleurde dieptekaart en het middelste stuk op als afbeeldingen
            plt.imsave(colored_depth_map_filename, output, cmap='plasma')  # Geleide dieptekaart
            plt.imsave(colored_middle_piece_filename, middle_piece, cmap='plasma')  # Geleide middenstuk

            # Controleer of er een object direct voor de camera is in het middelste stuk
            total_pixels = middle_piece.size  # Totaal aantal pixels in het middelste stuk
            pixels_above_threshold = np.sum(middle_piece > threshold)  # Aantal pixels boven de drempel
            percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100  # Percentage van de pixels boven de drempel

            print(f"{percentage_above_threshold:.2f}% van de pixels in het middelste stuk hebben een diepte boven de drempel van {threshold}")

            # Controleer voor het volledige stuk (alle pixels van het frame)
            total_pixels2 = output.size  # Totaal aantal pixels in de volledige dieptekaart
            pixels_above_threshold2 = np.sum(output > threshold)  # Aantal pixels boven de drempel
            percentage_above_threshold2 = (pixels_above_threshold2 / total_pixels2) * 100  # Percentage voor de volledige afbeelding

            print(f"{percentage_above_threshold2:.2f}% van de pixels in de gehele dieptekaart hebben een diepte boven de drempel van {threshold}")

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
