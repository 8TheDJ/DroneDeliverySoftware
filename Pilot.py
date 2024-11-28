from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException
import time
import socket
import argparse
import threading
#er staan geen coordinaten waar coordinaten hadden moeten staan, omdat het de onze locatie weg geeft aan het internet, er staat in het commentaar bij waar er coordinaten hadden moeten staan.

# Functie om verbinding te maken met de drone
def connectMyCopter():
    # Argumenten parseren om verbindingsstring in te stellen
    parser = argparse.ArgumentParser(description='commands')
    parser.add_argument('--connect', default='/dev/ttyAMA0', help='Vehicle connection target string. E.g., /dev/ttyAMA0')
    args = parser.parse_args()

    connection_string = args.connect  # Verbindingstring (zoals /dev/ttyAMA0 voor de Raspberry Pi)
    baud_rate = 57600  # Baud rate voor de communicatie

    try:
        print(f"Verbinden met de drone op: {connection_string} met baud rate {baud_rate}")
        # Maak verbinding met de drone
        vehicle = connect(connection_string, baud=baud_rate, wait_ready=True, heartbeat_timeout=60)
        print("Verbonden met de drone.")
    except APIException as e:
        print(f"APIException: {e}")
        return None
    except socket.error as e:
        print(f"Socket error: {e}")
        return None
    except Exception as e:
        print(f"Er is een onverwachte fout opgetreden: {e}")
        return None

    return vehicle  # Retourneer het vehicle object als verbinding is geslaagd

# Functie om de drone te wapenen en op te stijgen naar een doelhoogte
def arm_and_takeoff(vehicle, target_altitude):
    print("Voer pre-arm controles uit...")
    while not vehicle.is_armable:  # Wacht totdat de drone klaar is om te worden gewapend
        print("Wachten tot de drone wapenbaar is...")
        time.sleep(1)

    print("Motoren wapenen...")
    vehicle.mode = VehicleMode("GUIDED")  # Zet de modus van de drone op GUIDED (besturing met GPS)
    vehicle.armed = True  # Wapen de drone

    while not vehicle.armed:  # Wacht totdat de drone gewapend is
        print("Wachten totdat de drone gewapend is...")
        time.sleep(1)

    print(f"Opstijgen naar {target_altitude} meter...")
    vehicle.simple_takeoff(target_altitude)  # Maak een eenvoudige take-off naar de doelhoogte

    # Wacht totdat de drone de doelhoogte heeft bereikt
    while True:
        altitude = vehicle.location.global_relative_frame.alt  # Haal de huidige hoogte van de drone op
        print(f"Huidige hoogte: {altitude}")

        if altitude >= target_altitude - 1:  # Als de hoogte binnen 1 meter van de doelhoogte is
            print("Doelhoogte bereikt.")
            break  # Stop met wachten
        time.sleep(1)

# Functie voor de kill switch om de drone te laten landen of uit te schakelen
def kill_switch(vehicle):
    print("Kill switch geactiveerd! De drone zal landen.")
    vehicle.mode = VehicleMode("LAND")  # Zet de modus op LAND om de drone te laten landen
    while vehicle.armed:  # Wacht totdat de drone is uitgeschakeld
        print("Wachten tot de drone is uitgeschakeld...")
        time.sleep(1)
        timeslept += 1  # Verhoog de slaapcounter (voor noodgevallen, als de drone niet uitgeschakeld wordt)
        if timeslept > 15:  # Na 15 seconden forceer de drone om uit te schakelen
            vehicle.armed = False
            print("Drone geforceerd uitgeschakeld.")
    print("Drone uitgeschakeld.")

# Functie om naar de kill switch te luisteren (gebruikersinput voor noodstop)
def listen_for_kill(vehicle):
    while True:
        # Wacht op een gebruikersinvoer voor de kill switch
        command = input("Typ 'KILL' om de kill switch te activeren: ").strip().upper()
        if command == "KILL":  # Als de gebruiker 'KILL' typt, activeer de kill switch
            kill_switch(vehicle)
            break  # Stop met luisteren nadat de kill switch is geactiveerd

# Hoofdprogramma
if __name__ == "__main__":
    # Verbind met de drone
    vehicle = connectMyCopter()

    if vehicle:
        # Start een aparte thread om te luisteren naar de kill switch (noodstop)
        kill_thread = threading.Thread(target=listen_for_kill, args=(vehicle,))
        kill_thread.daemon = True  # Zorg ervoor dat de thread stopt als het hoofdprogramma eindigt
        kill_thread.start()

        # Wapen de drone en laat deze opstijgen naar 4 meter
        arm_and_takeoff(vehicle, 4)

        # Zet de vliegsnelheid in de lucht (na het opstijgen)
        vehicle.airspeed = 7  # Zet de luchtsnelheid in m/s
        print(f"Luchtsnelheid ingesteld op {vehicle.airspeed} m/s.")

        # Ga naar een specifieke locatie (voorbeeld: hetzelfde punt voor nu, pas dit aan indien nodig)
        print("Ga naar locatie1...")
        location1 = LocationGlobalRelative()  # Specifieke coördinaten (latitude, longitude, altitude) wel nog in te voeren
        vehicle.simple_goto(location1)  # Vlieg naar de opgegeven locatie

        # Wacht een bepaalde tijd op de locatie (kan worden aangepast)
        time.sleep(5000)

        # Ga terug naar de thuisbasis (RTL - Return To Launch)
        print("Terug naar de basis (RTL)...")
        vehicle.mode = VehicleMode("RTL")  # Zet de modus op RTL (Return To Launch)

        # Wacht totdat de drone landt of stop na 2000 seconden
        time.sleep(2000)

        # Sluit de verbinding met de drone
        print("Sluit de voertuigverbinding...")
        vehicle.close()

    else:
        print("Mislukt om verbinding te maken met de drone.")
