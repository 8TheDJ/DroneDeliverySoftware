# import libraries
from dronekit import *
import time
import socket
import argparse
import math
from pymavlink import mavutil

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
    rtl_altitude = 6  # Set to 6 meters
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