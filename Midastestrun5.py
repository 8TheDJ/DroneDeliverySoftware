import cv2
import torch
import matplotlib.pyplot as plt
import numpy as np

# Download the MiDaS model
midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
midas.to('cpu')
midas.eval()


# Input transformation pipeline
transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = transforms.small_transform

# Hook into OpenCV
cap = cv2.VideoCapture(0)

# Allow the camera to adjust by reading a few frames first (without processing them)
for _ in range(10):  # Read 10 frames for adjustment (you can adjust the number)
    ret, _ = cap.read()

# Now that the camera has adjusted, capture the actual frame
ret, frame = cap.read()
cap.release()  # Release the capture after the actual frame

if ret:
    # Transform input for MiDaS 
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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

        # Save depth values to a text file
        with open('C:/Users/itayh/Desktop/python/depth_values.txt', 'w') as f:
            for row in output:
                f.write(' '.join(map(str, row)) + '\n')

        print("Depth values saved to 'depth_values.txt'")

        # Split depth map into 9 pieces and analyze the middle piece
        h, w = output.shape
        h_split, w_split = h // 3, w // 3

        # Extract middle piece
        middle_piece = output[h_split:2*h_split, w_split:2*w_split]

        # Check for object directly in front in the middle piece
        threshold = 500
        total_pixels = middle_piece.size
        pixels_above_threshold = np.sum(middle_piece > threshold)
        percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100

        print(f"{percentage_above_threshold:.2f}% of pixels in the middle piece have a depth value above {threshold}")
        # Check for object directly in front in the whole piece
        total_pixels2 = output.size
        pixels_above_threshold2 = np.sum(output > threshold)
        percentage_above_threshold2 = (pixels_above_threshold2 / total_pixels2) * 100

        print(f"{percentage_above_threshold2:.2f}% of pixels in the whole piece have a depth value above {threshold}")

    # Display the depth map, middle piece, and original frame
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.title("Original Depth Map") 
    plt.imshow(output, cmap='plasma')
    plt.colorbar()

    plt.subplot(1, 2, 2)
    plt.title("Middle Piece of Depth Map")
    plt.imshow(middle_piece, cmap='plasma')
    plt.colorbar()
    plt.show()

    cv2.imshow('Original Frame', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("Failed to capture frame.")