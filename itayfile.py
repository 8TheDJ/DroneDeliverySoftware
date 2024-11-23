import cv2
import os
import subprocess
import time

# Video output settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_RATE = 20  # Frames per second
OUTPUT_FILE = "output.avi"  # Change to .mp4 if needed

# Temporary directory to store images
TEMP_DIR = "/tmp/libcamera_frames"
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize VideoWriter for saving video
fourcc = cv2.VideoWriter_fourcc(*"XVID")  # Use 'XVID' for AVI or 'mp4v' for MP4
video_writer = cv2.VideoWriter(OUTPUT_FILE, fourcc, FRAME_RATE, (FRAME_WIDTH, FRAME_HEIGHT))

# Command template for capturing images with libcamera-still
def capture_frame(output_file):
    subprocess.run(
        [
            "libcamera-still",
            "--width", str(FRAME_WIDTH),
            "--height", str(FRAME_HEIGHT),
            "-o", output_file,
            "-n",  # No preview
            "-t", "1",  # Minimum timeout
        ],
        check=True,
    )

try:
    start_time = time.time()
    while True:
        # Generate a unique filename for the frame
        frame_path = os.path.join(TEMP_DIR, f"frame_{int(time.time() * 1000)}.jpg")

        # Capture the frame
        capture_frame(frame_path)

        # Read the frame
        frame = cv2.imread(frame_path)
        if frame is not None:
            # Write the frame to the video file
            video_writer.write(frame)

        # Clean up the temporary frame
        os.remove(frame_path)

        # Stop recording after a fixed duration (e.g., 10 seconds)
        if time.time() - start_time > 10:  # Adjust duration as needed
            break

except KeyboardInterrupt:
    print("Recording interrupted...")

finally:
    # Release the video writer and clean up
    video_writer.release()
    print(f"Video saved as {OUTPUT_FILE}")

    # Remove the temporary directory
    os.rmdir(TEMP_DIR)