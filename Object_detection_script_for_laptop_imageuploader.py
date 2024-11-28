import os
import cv2
import torch
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Load the MiDaS model
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')
midas.eval()

# Input transformation pipeline
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

# Parameters
input_folder = "Path_to_inputfolder"  # Path naar folder met plaatjes
output_folder = "Path_to_outputfolder"  # Folder om tabellen in op te slaan
os.makedirs(output_folder, exist_ok=True) #Checken of output folder bestaat

# Je ziet dat bijvoorbeeld bij de thresholds tussen de 350 en 400 het veel specifieker is dan bijvoorbeeld tussen 500 en 600. Dit komt doordat we de code meerdere keren hebben gerunt en elke keer rond de 300, 350 en 400 kregen, dus we wouden het specificeren
thresholds = [100, 200,250,275, 300,325,350,355,360,365,370,375,380,385,390,395, 400,425,450,475, 500, 600, 700, 800]  # drempelwaardes voor de diepte
percentage_thresholds = [5,10,15, 20,25, 30, 40, 50, 60, 70, 80]  # Drempelpercentages

# Tabel van object detectie summary opstellen
summary_table = []

# Initialize a dictionary to count correctness for each threshold-percentage combination
correctness_counts = {f"{threshold} at {percentage_threshold}%": 0 for threshold in thresholds for percentage_threshold in percentage_thresholds}

# Analyze object detection
for image_file in os.listdir(input_folder):
    if not image_file.lower().endswith(('png', 'jpg', 'jpeg')):
        continue  # Skip non-image files

    image_path = os.path.join(input_folder, image_file)
    image_name = os.path.basename(image_file)

    # Load and preprocess the image
    frame = cv2.imread(image_path)
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
    imgbatch = transform(img).to('cpu')

    # Predict depth map
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
    middle_piece = output[h_split:2*h_split, w_split:2*w_split]

    # Analyze object detection
    detection_row = {"Image Name": image_name}
    detected_any_object = False  # Track if any threshold detects an object
    correct_thresholds = []  # Store thresholds with correct detection

    for threshold in thresholds:
        total_pixels = middle_piece.size
        pixels_above_threshold = np.sum(middle_piece > threshold)
        percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100

        for percentage_threshold in percentage_thresholds:
            key = f"{threshold} at {percentage_threshold}%"
            if percentage_above_threshold > percentage_threshold:
                detection_row[key] = "yes"
                detected_any_object = True
                if "object" in image_name.lower():
                    correct_thresholds.append(key)
                    correctness_counts[key] += 1
            else:
                detection_row[key] = "no"
                if "object" not in image_name.lower():
                    correct_thresholds.append(key)
                    correctness_counts[key] += 1

    # Add a column for whether the word "object" is in the image name
    detection_row["Was There an Object in the Image?"] = "yes" if "object" in image_name.lower() else "no"

    # Final column listing correct thresholds
    detection_row["Correct Thresholds"] = ", ".join(correct_thresholds)

    # Add row to summary table
    summary_table.append(detection_row)

# After processing all images, find the most correct combinations
most_correct_count = max(correctness_counts.values())
most_correct_combinations = [key for key, count in correctness_counts.items() if count == most_correct_count]

# Save correctness counts as an additional CSV for reference (optional)
correctness_counts_df = pd.DataFrame(list(correctness_counts.items()), columns=["Threshold-Percentage Combination", "Correct Count"])
correctness_counts_file = os.path.join(output_folder, "correctness_counts.csv")
correctness_counts_df.to_csv(correctness_counts_file, index=False)

# Add the most correct combinations below the summary table
summary_table.append({"Image Name": "Most Correct Combination(s)", **{key: "" for key in correctness_counts}, "Correct Thresholds": ", ".join(most_correct_combinations)})

# Save summary table as a CSV
summary_df = pd.DataFrame(summary_table)
summary_file = os.path.join(output_folder, "object_detection_summary_with_most_correct.csv")
summary_df.to_csv(summary_file, index=False)

print(f"Results saved to {output_folder}")
