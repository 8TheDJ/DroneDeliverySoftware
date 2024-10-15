# import libraries
from dronekit import *
import time
import socket
import argparse
import math
from pymavlink import mavutil

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

# Kill switch function to disarm the drone
def kill_switch(vehicle):
    print("Kill switch activated! Landing the drone.")
    vehicle.mode = VehicleMode("LAND")  # Alternatively, disarm directly with vehicle.armed = False
    while vehicle.armed:
        print(" Waiting for disarming...")
        time.sleep(1)
        timeslept=+ 1
        if timeslept> 15:
            vehicle.armed= False
            print("drone forcefully disarmed.")
    print("Drone disarmed.")

def land_switch():
    while vehicle.gps_0.fix_type < 2:  # Wait for at least 2D GPS fix
        print("Waiting for GPS fix...")
        time.sleep(1)

    print("GPS fix acquired")

    # Check the home position
    if vehicle.home_location is None:
        print("Waiting for home location to be set...")
        while not vehicle.home_location:
            cmds = vehicle.commands
            cmds.download()
            cmds.wait_ready()
            if vehicle.home_location:
                print(f"Home location set to: {vehicle.home_location}")

    # Set RTL altitude
    rtl_altitude = 20  # in meters
    vehicle.parameters['RTL_ALT'] = rtl_altitude * 100  # RTL_ALT is in centimeters
    print(f"RTL altitude set to {rtl_altitude} meters")

    # Safety checks before RTL
    if vehicle.battery.voltage < 10.5:
        print("Warning: Low battery voltage!")
    else:
        print("Battery voltage OK.")

    # Ensure the drone is flying
    if vehicle.armed and vehicle.location.global_relative_frame.alt > 1:
        print("Drone is flying, switching to RTL...")
        vehicle.mode = VehicleMode("RTL")
    else:
        print("Drone is not flying, cannot execute RTL.")

    # Monitor altitude until the drone lands
    while vehicle.location.global_relative_frame.alt > 0.1:
        print(f"Altitude: {vehicle.location.global_relative_frame.alt}")
        time.sleep(1)

    print("Drone has landed.")

# Close the vehicle connection

# Function to listen for user input (emergency stop)
def listen_for_kill(vehicle):
    while True:
        command = input("Type 'KILL' to trigger the kill switch: ").strip().upper()
        if command == "KILL":
            kill_switch(vehicle)
            break  # Stop listening after the kill switch is activated

# Main program
if __name__ == "__main__":
    vehicle = connectMyCopter()
    
    if vehicle:
        # Start a thread to listen for the kill switch command in parallel
        kill_thread = threading.Thread(target=listen_for_kill, args=(vehicle,))
        kill_thread.daemon = True  # Ensures thread will exit when the main program exits
        kill_thread.start()

        vehicle.mav.command_long_send(
        vehicle.target_system,  # Target system
        vehicle.target_component,  # Target component
        mavutil.mavlink.MAV_CMD_DO_SET_HOME,  # MAVLink command to set home
        1,  # Set 1 to use current position as home
        0, 0, 0, 0, 0, 0, 0  # Parameters for lat, lon, alt (not needed when using current position)
        )
        # Arm the drone and take off to 4 meters
        arm_and_takeoff(vehicle, 4)

        # Set airspeed after takeoff
        vehicle.airspeed = 3
        print(f"Airspeed set to {vehicle.airspeed} m/s.")

        # Go to a specified location (example: same spot for now, customize as needed)
        print("Going to location1...")
        location1 = LocationGlobalRelative(52.2873594988193, 4.85433965921402, 4)
        vehicle.simple_goto(location1)
        location2 = LocationGlobalRelative(52.2873594988193, 4.85433965921402, 0.5)
        vehicle.simple_goto(location2)

        # Stay at the location for some time (this can be adjusted)
        time.sleep(10)

        #landswitch()
        # Returning to launch location (RTL)
        print("Returning to basecamp (RTL)...")
        vehicle.mode = VehicleMode("RTL")

        # Wait for landing or timeout after 2000 seconds
        time.sleep(10)

        # Close the connection
        print("Closing vehicle connection...")
        vehicle.close()

    else:
        print("Failed to connect to the drone.")
