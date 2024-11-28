import cv2  # Bibliotheek voor computer vision
import torch  # PyTorch voor machine learning
import matplotlib.pyplot as plt  # Bibliotheek voor visualisatie
import numpy as np  # Bibliotheek voor numerieke berekeningen

# Download en laad het MiDaS model voor diepte-schatting
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')  # MiDaS_small is een lichtgewicht versie van het model
midas.to('cpu')  # Gebruik de CPU (indien beschikbaar, gebruik een GPU voor betere prestaties)
midas.eval()  # Zet het model in evaluatiemodus (niet trainen)

# Laad de transformaties die nodig zijn voor invoer naar het MiDaS model
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform  # Gebruik de transformaties voor het kleine MiDaS model

# Open de camera (standaard webcam: index 0)
cap = cv2.VideoCapture(0)

# Laat de camera zich aanpassen door een aantal frames te lezen zonder ze te verwerken
for _ in range(10):  # Lees 10 frames zodat de camera zich kan kalibreren
    ret, _ = cap.read()

# Na aanpassing: lees het daadwerkelijke frame
ret, frame = cap.read()  # `ret` is True als het frame succesvol is gelezen
cap.release()  # Sluit de cameracapture na het lezen van het frame

if ret:  # Controleer of het frame succesvol is vastgelegd
    # Transformeer de invoer voor het MiDaS model
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converteer van BGR (OpenCV standaard) naar RGB (vereist door MiDaS)
    imgbatch = transform(img).to('cpu')  # Pas transformaties toe en zet de afbeelding naar CPU

    # Voorspel de dieptekaart
    with torch.no_grad():  # Schakel gradientberekening uit voor snellere inferentie
        prediction = midas(imgbatch)  # Maak een voorspelling met het model
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),  # Voeg een kanaal toe (MiDaS vereist deze indeling)
            size=img.shape[:2],  # Schaal de voorspelling naar de originele afbeeldingsgrootte
            mode='bicubic',  # Gebruik bicubische interpolatie
            align_corners=False
        ).squeeze()  # Verwijder de extra dimensie om de array weer 2D te maken

        output = prediction.cpu().numpy()  # Converteer het resultaat naar een numpy-array

        # Sla de dieptewaarden op in een tekstbestand
        with open('C:/Users/itayh/Desktop/python/depth_values.txt', 'w') as f:
            for row in output:
                f.write(' '.join(map(str, row)) + '\n')  # Schrijf elke rij van de dieptekaart naar het bestand
        print("Dieptewaarden opgeslagen in 'depth_values.txt'")

        # Analyseer het middelste deel van de dieptekaart
        h, w = output.shape  # Verkrijg de hoogte en breedte van de dieptekaart
        h_split, w_split = h // 3, w // 3  # Verdeel de kaart in 3x3 gelijke delen

        # Pak het middelste deel van de dieptekaart
        middle_piece = output[h_split:2*h_split, w_split:2*w_split]

        # Controleer hoeveel pixels in het middelste deel een waarde hebben boven een bepaalde drempel
        threshold = 500  # Drempelwaarde voor diepte
        total_pixels = middle_piece.size  # Totaal aantal pixels in het middelste deel
        pixels_above_threshold = np.sum(middle_piece > threshold)  # Tellen van pixels boven de drempelwaarde
        percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100  # Percentage berekenen

        print(f"{percentage_above_threshold:.2f}% van de pixels in het middelste deel heeft een dieptewaarde boven {threshold}")

        # Analyseer de hele dieptekaart
        total_pixels2 = output.size  # Totaal aantal pixels in de dieptekaart
        pixels_above_threshold2 = np.sum(output > threshold)  # Tellen van pixels boven de drempelwaarde
        percentage_above_threshold2 = (pixels_above_threshold2 / total_pixels2) * 100  # Percentage berekenen

        print(f"{percentage_above_threshold2:.2f}% van de pixels in de gehele afbeelding heeft een dieptewaarde boven {threshold}")

    # Toon de originele dieptekaart en het middelste deel
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.title("Originele dieptekaart") 
    plt.imshow(output, cmap='plasma')  # Visualiseer de dieptekaart met een kleurrijk schema
    plt.colorbar()

    plt.subplot(1, 2, 2)
    plt.title("Middelste deel van de dieptekaart")
    plt.imshow(middle_piece, cmap='plasma')  # Visualiseer het middelste deel van de dieptekaart
    plt.colorbar()
    plt.show()

    # Toon het originele cameraframe
    cv2.imshow('Origineel frame', frame)  # Toon het vastgelegde frame
    cv2.waitKey(0)  # Wacht tot een toets wordt ingedrukt
    cv2.destroyAllWindows()  # Sluit alle OpenCV vensters
else:
    print("Het vastleggen van een frame is mislukt.")  # Foutmelding als de camera geen frame heeft vastgelegd
