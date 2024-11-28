import os
import cv2
import torch
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Laad het MiDaS-model (voor dieptevoorspelling)
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')  # Het model draait op de CPU
midas.eval()  # Zet het model in evaluatiemodus (geen training)

# Voorbereiding van de invoertransformaties (nodig voor het MiDaS-model)
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

# Parameters
input_folder = "C:/Users/itayh/Desktop/python/MiDaS test object detection"  # Replace with the path to your folder
output_folder = "C:/Users/itayh/Desktop/python/MiDaS test object detection output"  # Folder to save results
os.makedirs(output_folder, exist_ok=True)
# Je ziet dat bijvoorbeeld bij de thresholds tussen de 350 en 400 het veel specifieker is dan bijvoorbeeld tussen 500 en 600. Dit komt doordat we de code meerdere keren hebben gerunt en elke keer rond de 300, 350 en 400 kregen, dus we wouden het specificeren
thresholds = [100, 200,250,275, 300,325,350,355,360,365,370,375,380,385,390,395, 400,425,450,475, 500, 600, 700, 800]  # drempelwaardes voor de diepte
percentage_thresholds = [5,10,15, 20,25, 30, 40, 50, 60, 70, 80]  # Percentage thresholds

# Initialize summary table
summary_table = []

# Initialiseer een dictionary om correctheid per combinatie te tellen
correctness_counts = {
    f"{threshold} at {percentage_threshold}%": 0 
    for threshold in thresholds 
    for percentage_threshold in percentage_thresholds
}

# Analyze object detection
for image_file in os.listdir(input_folder):
    if not image_file.lower().endswith(('png', 'jpg', 'jpeg')):
        continue  # Sla niet-afbeeldingsbestanden over

    # Laad de afbeelding
    image_path = os.path.join(input_folder, image_file)
    image_name = os.path.basename(image_file)

    frame = cv2.imread(image_path)  # Lees de afbeelding in met OpenCV
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converteer naar RGB
    imgbatch = transform(img).to('cpu')  # Transformeer invoer voor MiDaS

    # Voorspel de dieptekaart
    with torch.no_grad():  # Geen gradiënten nodig tijdens inferentie
        prediction = midas(imgbatch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img.shape[:2],
            mode='bicubic',
            align_corners=False
        ).squeeze()
        output = prediction.cpu().numpy()  # Converteer de voorspelling naar een numpy-array

    # Splits de dieptekaart in 9 delen en selecteer het middelste deel
    h, w = output.shape
    h_split, w_split = h // 3, w // 3
    middle_piece = output[h_split:2*h_split, w_split:2*w_split]

    # Analyseer objectdetectie
    detection_row = {"Image Name": image_name}  # Begin een nieuwe rij voor deze afbeelding
    detected_any_object = False  # Houd bij of er een object is gedetecteerd
    correct_thresholds = []  # Opslaan van correcte combinaties

    #calculations for percentages of pixels above the threshold
    for threshold in thresholds:
        total_pixels = middle_piece.size  # Totaal aantal pixels in het middelste stuk
        pixels_above_threshold = np.sum(middle_piece > threshold)  # Pixels boven de drempelwaarde
        percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100  # Percentage van pixels boven de drempel

        #check if object is detected
        for percentage_threshold in percentage_thresholds:
            key = f"{threshold} at {percentage_threshold}%"
            if percentage_above_threshold > percentage_threshold:
                detection_row[key] = "yes"
                detected_any_object = True
                # Controleer of de naam van de afbeelding "object" bevat en dit correct is
                if "object" in image_name.lower():
                    correct_thresholds.append(key)
                    correctness_counts[key] += 1
            else:
                detection_row[key] = "no"
                # Controleer of er geen object was en dit correct is
                if "object" not in image_name.lower():
                    correct_thresholds.append(key)
                    correctness_counts[key] += 1

    # Voeg een kolom toe om aan te geven of er een object werd verwacht
    detection_row["Was There an Object in the Image?"] = "yes" if "object" in image_name.lower() else "no"

    # Final column listing correct thresholds
    detection_row["Correct Thresholds"] = ", ".join(correct_thresholds)

    # Voeg deze rij toe aan de samenvattingstabel
    summary_table.append(detection_row)

# After processing all images, find the most correct combinations
most_correct_count = max(correctness_counts.values())
most_correct_combinations = [
    key for key, count in correctness_counts.items() if count == most_correct_count
]

# Save correctness counts as an additional CSV for reference (optional)
correctness_counts_df = pd.DataFrame(list(correctness_counts.items()), columns=["Threshold-Percentage Combination", "Correct Count"])
correctness_counts_file = os.path.join(output_folder, "correctness_counts.csv")
correctness_counts_df.to_csv(correctness_counts_file, index=False)

# Add the most correct combinations below the summary table
summary_table.append({"Image Name": "Most Correct Combination(s)", **{key: "" for key in correctness_counts}, "Correct Thresholds": ", ".join(most_correct_combinations)})

# Sla de samenvattingstabel op als een CSV-bestand
summary_df = pd.DataFrame(summary_table)
summary_file = os.path.join(output_folder, "object_detection_summary_with_most_correct.csv")
summary_df.to_csv(summary_file, index=False)

print(f"Resultaten opgeslagen in {output_folder}")
