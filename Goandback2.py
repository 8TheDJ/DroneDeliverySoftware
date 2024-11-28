# Importeer benodigde bibliotheken
from dronekit import *  # DroneKit wordt gebruikt voor communicatie met de drone
import time  # Voor het instellen van vertragingen en wachten
import socket  # Voor netwerkmogelijkheden (o.a. foutafhandeling)
import argparse  # Om argumenten van de commandoregel te verwerken
import math  # Voor wiskundige berekeningen (hoewel het hier niet wordt gebruikt)
from pymavlink import mavutil  # Voor MAVLink-communicatie
# wij willen onze locatie niet weggeven aan het internet, daarom staan de coördinaten niet ingevuld, waar die moeten staan, staat er een opmerking in het commentaar

# Functie om verbinding te maken met de drone
def connectMyCopter():
    # Initialiseer de commandoregel parser
    parser = argparse.ArgumentParser(description='commands')  # Beschrijving van het script
    parser.add_argument('--connect', default='/dev/ttyAMA0', help='Doelstring voor verbinding met de drone, bijvoorbeeld /dev/ttyAMA0')  # Verbindopties
    args = parser.parse_args()

    # Haal de verbindingsinformatie op
    connection_string = args.connect
    baud_rate = 57600  # Snelheid van de seriële verbinding

    try:
        # Probeer verbinding te maken met de drone
        print(f"Verbinding maken met drone op: {connection_string} met baudrate {baud_rate}")
        vehicle = connect(connection_string, baud=baud_rate, wait_ready=True, heartbeat_timeout=60)
        print("Verbonden met drone.")
    except APIException as e:
        # Foutafhandeling bij API-problemen
        print(f"APIException: {e}")
        return None
    except socket.error as e:
        # Foutafhandeling bij netwerkproblemen
        print(f"Socket error: {e}")
        return None
    except Exception as e:
        # Algemene foutafhandeling
        print(f"Een onverwachte fout is opgetreden: {e}")
        return None

    # Retourneer het voertuigobject als de verbinding succesvol is
    return vehicle

# Functie om de drone te armeren en op te stijgen tot een doelhoogte
def arm_and_takeoff(vehicle, target_altitude):
    print("Uitvoeren van pre-arm controles...")
    # Wachten tot de drone armable is
    while not vehicle.is_armable:
        print(" Wachten tot de drone armeerbaar is...")
        time.sleep(1)

    print("Motoren armeren...")
    vehicle.mode = VehicleMode("GUIDED")  # Stel de modus in op 'GUIDED'
    vehicle.armed = True  # Armeer de motoren

    # Wachten tot de motoren geactiveerd zijn
    while not vehicle.armed:
        print(" Wachten op armeren...")
        time.sleep(1)

    # Start het opstijgen
    print(f"Opstijgen naar {target_altitude} meter...")
    vehicle.simple_takeoff(target_altitude)  # Stijg op tot de doelhoogte

    # Monitor de hoogte tot de gewenste hoogte is bereikt
    while True:
        altitude = vehicle.location.global_relative_frame.alt  # Huidige relatieve hoogte
        print(f" Huidige hoogte: {altitude}")

        if altitude >= target_altitude - 1:  # Controleer of de hoogte bijna bereikt is
            print("Doelhoogte bereikt.")
            break
        time.sleep(1)  # Wacht een seconde voordat opnieuw gecontroleerd wordt

# Hoofdprogramma
if __name__ == "__main__":
    # Maak verbinding met de drone
    vehicle = connectMyCopter()
    
    if vehicle:
        # Stel de RTL (Return to Launch) hoogte in vóór opstijgen
        rtl_altitude = 6  # RTL hoogte in meters
        vehicle.parameters['RTL_ALT'] = rtl_altitude * 100  # RTL_ALT wordt in centimeters opgeslagen
        print(f"RTL hoogte ingesteld op {rtl_altitude} meter")

        # Armeer de drone en stijg op tot een hoogte van 5 meter
        arm_and_takeoff(vehicle, 5)

        # Stel de luchtsnelheid in na het opstijgen
        vehicle.airspeed = 5  # Luchtsnelheid in m/s
        print(f"Luchtsnelheid ingesteld op {vehicle.airspeed} m/s.")

        # Beweeg naar een specifieke locatie
        print("Navigeren naar locatie1...")
        location1 = LocationGlobalRelative()  # Specifieke GPS-locatie en hoogte(latitude, longitude, altitude), wel nog in te voeren
        vehicle.simple_goto(location1)  # Beweeg naar de opgegeven locatie
        time.sleep(5)  # Wacht een paar seconden

        # Blijf een tijdje op de locatie (hier 10 seconden)
        time.sleep(10)

        # Retourneer naar de startlocatie
        print("Terugkeren naar basis (RTL)...")
        vehicle.mode = VehicleMode("RTL")  # Schakel naar 'Return to Launch'-modus

        # Wacht tot de drone landt of een time-out na 10 seconden
        time.sleep(10)

        # Sluit de verbinding met de drone
        print("Verbinding met drone sluiten...")
        vehicle.close()

    else:
        # Foutmelding als de verbinding mislukt
        print("Kon geen verbinding maken met de drone.")
