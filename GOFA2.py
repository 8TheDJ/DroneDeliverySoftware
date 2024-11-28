import subprocess  # Voor het uitvoeren van externe commando's zoals libcamera-vid

# Video-uitvoer instellingen
FRAME_WIDTH = 640  # Breedte van het videoframe in pixels
FRAME_HEIGHT = 480  # Hoogte van het videoframe in pixels
FRAME_RATE = 30  # Gewenste framerate (beelden per seconde)
DURATION = 10  # Opnameduur in seconden
OUTPUT_FILE = "output.h264"  # Naam van het uitvoerbestand

# Bouw het libcamera-vid commando
command = [
    "libcamera-vid",  # Commando voor video-opname via de Raspberry Pi-camera
    "--width", str(FRAME_WIDTH),  # Stel de breedte van het frame in
    "--height", str(FRAME_HEIGHT),  # Stel de hoogte van het frame in
    "--framerate", str(FRAME_RATE),  # Stel de framerate in
    "--codec", "h264",  # Gebruik de H.264 codec voor compressie
    "-o", OUTPUT_FILE,  # Naam van het uitvoerbestand
    "-t", str(DURATION * 1000),  # Opnameduur in milliseconden
]

# Voer het commando uit
try:
    print(f"Video opnemen met {FRAME_RATE} FPS gedurende {DURATION} seconden...")
    # Start het opnameproces en controleer op fouten
    subprocess.run(command, check=True)
    print(f"Video opgeslagen als {OUTPUT_FILE}")
except subprocess.CalledProcessError as e:
    # Foutafhandeling als het subprocess mislukt
    print(f"Er is een fout opgetreden: {e}")
