from dronekit import *
import time
import socket
import argparse
import math

#Doel om het starten van de drone te testen, dus hij moet gewoon zijn rotoren aanzetten en weer loslaten, zodat we kleine modules bouwen die je bij mekaar kan doen
#https://www.youtube.com/watch?v=TFDWs_DG2QY
#https://dronekit-python.readthedocs.io/en/latest/guide/taking_off.html

#connect drone
parser=argparse.ArgumentParser(description="commands")
parser.add_argument('--connect')
args=parser.parse_args()

connection_string=args.connect
print(f"Connection to drone {connection_string}")
vehicle = connect(connection_string, wait_ready=True)

def arm_and_takeoff(target_altitude):
    print("arming motors")
    while not vehicle.is_armable:
        time.sleep(1)
    vehicle.mode= VehicleMode("GUIDED")
    vehicle.armed=True
    while not vehicle.armed:
        print("waiting for arming...")
        time.sleep(1)
    print("Ready for takeoff")
    vehicle.simple_takeoff(target_altitude)

    while True:
        altitude = vehicle.location.global_relative_frame.alt

        if altitude >= target_altitude -1:
            print("Target altitude reached")
            break
        time.sleep(1)
#main programm
arm_and_takeoff(10)    
#set default airspeed
vehicle.airspeed = 7
# go to
print("going to Location1")
location1= LocationGlobalRelative()
vehicle.simple_goto(location1)
#Hier can de rest
time.sleep(50)
#terugkomen
print("Coming back to basecamp")
vehicle.mode= VehicleMode("RTL")
time.sleep(2000)
#close connection
vehicle.close()
