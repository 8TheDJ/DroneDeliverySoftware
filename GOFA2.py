import subprocess

# Video output settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_RATE = 30  # Desired frames per second
DURATION = 10  # Recording duration in seconds
OUTPUT_FILE = "output.h264"  # Output video file

# Build the libcamera-vid command
command = [
    "libcamera-vid",
    "--width", str(FRAME_WIDTH),
    "--height", str(FRAME_HEIGHT),
    "--framerate", str(FRAME_RATE),
    "--codec", "h264",  # Use H.264 codec
    "-o", OUTPUT_FILE,
    "-t", str(DURATION * 1000),  # Duration in milliseconds
]

# Run the command
try:
    print(f"Recording video at {FRAME_RATE} FPS for {DURATION} seconds...")
    subprocess.run(command, check=True)
    print(f"Video saved as {OUTPUT_FILE}")
except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e}")