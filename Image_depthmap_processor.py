import os
import cv2
import torch
import matplotlib.pyplot as plt


# Load the MiDaS model
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')
midas.eval()

# Input transformation pipeline
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

# Parameters
input_folder = "C:/Users/itayh/Desktop/python/MiDaS test object detection"  # Path naar folder met plaatjes
output_folder = "C:/Users/itayh/Desktop/python/MiDaS test object detection output"  # Folder om tabellen in op te slaan
os.makedirs(output_folder, exist_ok=True) #Checken of output folder bestaat

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

    # Save the depth map and middle piece with unique filenames in the output folder
    colored_depth_map_filename = os.path.join(output_folder, f'depth_map_colored_{image_name}.png')
    colored_middle_piece_filename = os.path.join(output_folder, f'middle_piece_colored_{image_name}.png')

    # Save the depth map and middle piece as colored images for visualization
    plt.imsave(colored_depth_map_filename, output, cmap='plasma')  # Colored depth map
    plt.imsave(colored_middle_piece_filename, middle_piece, cmap='plasma')  # Colored middle piece
