# Importeer benodigde bibliotheken
from dronekit import connect, VehicleMode
import time
import argparse
from pymavlink import mavutil

# Functie om verbinding te maken met de drone
def connectMyCopter():
    parser = argparse.ArgumentParser(description='commands')
    parser.add_argument('--connect', default='/dev/ttyAMA0', help='Verbindingsstring')
    args = parser.parse_args()
    
    connection_string = args.connect
    baud_rate = 57600  

    try:
        print(f"Verbinding maken met drone op: {connection_string} met baudrate {baud_rate}")
        vehicle = connect(connection_string, baud=baud_rate, wait_ready=True, heartbeat_timeout=60)
        print("Verbonden met drone.")
        return vehicle
    except Exception as e:
        print(f"Fout bij verbinding: {e}")
        return None

# Functie om de drone te armeren en op te stijgen zonder GPS
def arm_and_takeoff(vehicle, target_altitude):
    print("Uitvoeren van pre-arm controles...")
    while not vehicle.is_armable:
        print(" Wachten tot de drone armeerbaar is...")
        time.sleep(1)

    print("Motoren armeren...")
    vehicle.mode = VehicleMode("GUIDED_NOGPS")  
    vehicle.armed = True  

    while not vehicle.armed:
        print(" Wachten op armeren...")
        time.sleep(1)

    print(f"Opstijgen naar {target_altitude} meter...")
    thrust = 0.6  
    while True:
        altitude = vehicle.location.global_relative_frame.alt  
        print(f" Huidige hoogte: {altitude}")
        if altitude >= target_altitude * 0.95:
            print("Doelhoogte bereikt.")
            break
        send_velocity(vehicle, 0, 0, -thrust)  
        time.sleep(0.1)

# Functie om snelheid te sturen zonder GPS
def send_velocity(vehicle, vx, vy, vz, duration=1):
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0, mavutil.mavlink.MAV_FRAME_BODY_NED,
        0b0000111111000111,  
        0, 0, 0,  
        vx, vy, vz,  
        0, 0, 0,  
        0, 0
    )
    for _ in range(int(duration * 10)):  
        vehicle.send_mavlink(msg)
        time.sleep(0.1)

# Functie om de drone te laten draaien (yaw)
def yaw(vehicle, degrees, duration=2):
    is_clockwise = 1 if degrees > 0 else -1
    yaw_speed = 30 * is_clockwise  
    msg = vehicle.message_factory.command_long_encode(
        0, 0, mavutil.mavlink.MAV_CMD_CONDITION_YAW,
        0, degrees, yaw_speed, 1, 0, 0, 0, 0
    )
    vehicle.send_mavlink(msg)
    time.sleep(duration)

# Functie om de drone te laten landen
def land(vehicle):
    print("Landing...")
    vehicle.mode = VehicleMode("LAND")
    time.sleep(5)
    vehicle.armed = False
    print("Landed.")

# Hoofdprogramma
if __name__ == "__main__":
    vehicle = connectMyCopter()
    
    if vehicle:
        arm_and_takeoff(vehicle, 1)  
        yaw(vehicle, 90)  
        send_velocity(vehicle, 0.5, 0, 0, 2)  
        land(vehicle)  

        print("Verbinding met drone sluiten...")
        vehicle.close()
    else:
        print("Kon geen verbinding maken met de drone.")
