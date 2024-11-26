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

# Initialize variables
objectinfront = 0
thresholds = [300, 400, 500, 600, 700]  # Depth thresholds
image_name = "2meterschoolmuur.jpg"
frame = cv2.imread(f"C:/Users/itayh/Desktop/python/MiDaS test plaatjes/{image_name}")  # Path to your image

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
    middle_piece = output[h_split:2 * h_split, w_split:2 * w_split]

    # Save the depth map as a visualization
    plt.imsave('depth_map_colored.png', output, cmap='plasma')  # Colored depth map

        # Initialize data storage for the table
    data = {"Image Name": [image_name]}  # Start with the image name
    object_rows = []  # Rows for object detection results

    # Calculate percentages for each threshold
    for threshold in thresholds:
        # Check percentage above threshold in the middle piece
        total_pixels = middle_piece.size
        pixels_above_threshold = np.sum(middle_piece > threshold)
        percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100

        # Add to the data dictionary
        data[f"Percentage Above {threshold}"] = [percentage_above_threshold]

        # Check if an object is in front for various percentage thresholds
        threshold_messages = [30, 40, 50, 60, 70]  # List of percentage thresholds

        for percentage_threshold in threshold_messages:
            if percentage_above_threshold > percentage_threshold:
                object_rows.append(
                    {
                        "Threshold": threshold,
                        "Percentage": percentage_above_threshold,
                        "Message": f"Object detected at {percentage_threshold}% threshold"
                    }
                )
            else:
                object_rows.append(
                    {
                        "Threshold": threshold,
                        "Percentage": percentage_above_threshold,
                        "Message": f"No object detected at {percentage_threshold}% threshold"
                    }
                )

    # Save the table to a CSV file
    df = pd.DataFrame(data)
    df.to_csv('depth_analysis.csv', index=False)

    # Save object detection results as a separate CSV file
    if object_rows:
        object_df = pd.DataFrame(object_rows)
        object_df.to_csv('object_detection.csv', index=False)

print("Analysis saved to 'depth_analysis.csv' and 'object_detection.csv'.")
