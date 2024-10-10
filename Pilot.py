from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException
import time
import socket
import argparse
import math

# Function to connect to the drone
def connectMyCopter():
    parser = argparse.ArgumentParser(description='commands')
    parser.add_argument('--connect', default='/dev/ttyAMA0', help='Vehicle connection target string. E.g., /dev/ttyAMA0')
    args = parser.parse_args()

    connection_string = args.connect
    baud_rate = 57600

    try:
        print(f"Connecting to drone on: {connection_string} with baud rate {baud_rate}")
        vehicle = connect(connection_string, baud=baud_rate, wait_ready=True, heartbeat_timeout=60)
        print("Connected to drone.")
    except APIException as e:
        print(f"APIException: {e}")
        return None
    except socket.error as e:
        print(f"Socket error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    return vehicle

# Function to arm the vehicle and take off to a target altitude
def arm_and_takeoff(vehicle, target_altitude):
    print("Performing pre-arm checks...")
    while not vehicle.is_armable:
        print(" Waiting for vehicle to become armable...")
        time.sleep(1)

    print("Arming motors...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print(f"Taking off to {target_altitude} meters...")
    vehicle.simple_takeoff(target_altitude)  # Take off to target altitude

    while True:
        altitude = vehicle.location.global_relative_frame.alt
        print(f" Current altitude: {altitude}")

        if altitude >= target_altitude - 1:
            print("Target altitude reached.")
            break
        time.sleep(1)


# Main program
if __name__ == "__main__":
    vehicle = connectMyCopter()
    
    if vehicle:
        # Keep radio alive if necessary (optional)
        # keep_radio_alive(vehicle)

        # Arm the drone and take off to 10 meters
        arm_and_takeoff(vehicle, 4)

        # Set airspeed after takeoff
        vehicle.airspeed = 7
        print(f"Airspeed set to {vehicle.airspeed} m/s.")

        # Go to a specified location (example: same spot for now, customize as needed)
        print("Going to location1...")
        location1 = LocationGlobalRelative(52.2873594988193, 4.85433965921402, 1)
        vehicle.simple_goto(location1)

        # Stay at the location for some time (this can be adjusted)
        time.sleep(5000)

        # Returning to launch location (RTL)
        print("Returning to basecamp (RTL)...")
        vehicle.mode = VehicleMode("RTL")

        # Wait for landing or timeout after 2000 seconds
        time.sleep(2000)

        # Close the connection
        print("Closing vehicle connection...")
        vehicle.close()

    else:
        print("Failed to connect to the drone.")