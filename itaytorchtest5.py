import cv2
import torch
import numpy as np
import matplotlib.pyplot as plt
import subprocess

# Load the MiDaS model
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')
midas.eval()

# Input transformation pipeline
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

# Capture a single frame using libcamera-still and pipe it into OpenCV
# The command will capture a frame using libcamera and output it to stdout
subprocess.run("sudo libcamera-still -o /tmp/captured_frame.jpg --nopreview", shell=True)

# Laad de gemaakte afbeelding in OpenCV
frame = cv2.imread('/tmp/captured_frame.jpg')  # Lees de afbeelding uit het tijdelijke bestand

if frame is None:
    print("Fout: Kon de opgenomen afbeelding niet laden. Controleer of deze correct is opgeslagen.")
else:
    print(f"Afbeeldingsvorm: {frame.shape}")  # Druk de dimensies van de afbeelding af
    print(f"Pixelwaarde linksboven: {frame[0, 0]}")  # Controleer de pixelwaarde van de linkerbovenhoek
    cv2.imwrite('original_frame.jpg', frame)  # Sla het originele frame op voor referentie

    # Verwerk de afbeelding voor invoer naar MiDaS
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converteer afbeelding van BGR (OpenCV standaard) naar RGB
    imgbatch = transform(img).to('cpu')  # Pas transformaties toe en zet op CPU

    # Make a prediction
    with torch.no_grad():
        prediction = midas(imgbatch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),  # Voeg een dimensie toe (kanalen)
            size=img.shape[:2],  # Herformaat naar de originele afbeeldinggrootte
            mode='bicubic',  # Gebruik bicubische interpolatie
            align_corners=False
        ).squeeze()  # Verwijder de extra dimensie

        output = prediction.cpu().numpy()  # Converteer de tensor naar een numpy-array

        # Controleer het bereik van de voorspelde dieptewaarden
        print(f"Minimale diepte: {np.min(output)}, Maximale diepte: {np.max(output)}")

        # Sla de dieptewaarden op in een tekstbestand
        with open('depth_values.txt', 'w') as f:
            for row in output:
                f.write(' '.join(map(str, row)) + '\n')
        print("Dieptewaarden opgeslagen in 'depth_values.txt'")

        # Splits de dieptekaart in 9 stukken en analyseer het middelste stuk
        h, w = output.shape
        h_split, w_split = h // 3, w // 3

        # Pak het middelste stuk van de dieptekaart
        middle_piece = output[h_split:2 * h_split, w_split:2 * w_split]

        # Analyseer de dieptewaarden in het middelste stuk
        threshold = 500  # Drempelwaarde voor diepte
        total_pixels = middle_piece.size
        pixels_above_threshold = np.sum(middle_piece > threshold)  # Aantal pixels boven de drempel
        percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100

        print(f"{percentage_above_threshold:.2f}% van de pixels in het middelste stuk heeft een dieptewaarde boven {threshold}")

        # Analyseer de hele dieptekaart
        total_pixels2 = output.size
        pixels_above_threshold2 = np.sum(output > threshold)
        percentage_above_threshold2 = (pixels_above_threshold2 / total_pixels2) * 100

        print(f"{percentage_above_threshold2:.2f}% van de pixels in de hele afbeelding heeft een dieptewaarde boven {threshold}")

    # Sla de dieptekaart en het middelste stuk op als afbeeldingen
    cv2.imwrite('depth_map.png', output)  # Sla de volledige dieptekaart op
    cv2.imwrite('middle_piece.png', middle_piece)  # Sla het middelste stuk op

    # Optioneel: sla de dieptekaart op als een kleurrijke afbeelding
    plt.imsave('depth_map_colored.png', output, cmap='plasma')  # Kleurrijke visualisatie van de dieptekaart
    plt.imsave('middle_piece_colored.png', middle_piece, cmap='plasma')  # Kleurrijke visualisatie van het middelste stuk
