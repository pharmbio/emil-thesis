#!/usr/bin/env python3
import telnetlib
import time
import requests
from BuildProtocol import BuildProtocol
from datetime import datetime

class RoboRun:

    # Various device default paths
    DEFAULT_PATH = "/programs/FINAL/" # Path to URP-files on the robot computer
    WASHER_PATH = "http://washer.lab.pharmb.io:5000/execute_protocol/"
    DISPENSER_PATH = "http://dispenser.lab.pharmb.io:5001/execute_protocol/"
    SHAKER_PATH = ""

    def __init__(self):
        self.tn = -1
        self.pd = BuildProtocol()

    def start(self, telnet_connection, protocol, data_list, plate_id):
        self.tn = telnet_connection # Get the telnet connection to the robot computer
        self.protocol = protocol # Get the protocol list with the checkpoints
        self.hotel_spots = data_list[0]
        self.lid_spots = data_list[1]
        self.plate_id = plate_id

        self.run() # Run the robot and the devices
        
        # Pack and return modified spot lists
        data = [self.hotel_spots,self.lid_spots] 
        return data


    # Saves a string and time stemp to a file
    def log(self,str_):
        with open('log', 'a') as file:
            do = datetime.now()
            file.write(do.hour, ':', do.minute, ':', do.second, ' ',str_)


    # Runs the robot and the devices
    def run(self):

        # Handle protective stop
        # self.tn.write(b"safetystatus\n")
        # status = self.read_last()
        # if status == "PROTECTIVE_STOP":
        #     self.tn.write(b"unlock protective stop\n")

        # Executes each command in the protocol list
        for c in self.protocol:
            self.execute_protocol(c)

        # Stop
        #self.tn.write(b"quit\n")


    # Executes inputed command
    def execute_protocol(self, program):

        # Check type of command
        # (Could probably be organized better)
        if self.pd.washer_play in program: # Runs if current command is washer play. Etc..
            self.play_washer(program)
        elif self.pd.dispenser_play in program:
            self.play_dispenser(program)
        elif self.pd.shaker_play in program:
            self.play_shaker(program)
        # elif program == self.pd.washer_wait:
        #     while (not self.is_washer_ready()):
        #         time.sleep(1)
        # elif program == self.pd.dispenser_wait:
        #     while (not self.is_dispenser_ready()):
        #         time.sleep(1)
        # elif program == self.pd.shaker_wait:
        #     while (not self.is_shaker_ready()):
        #         time.sleep(1)
        else: # If the command is a command to the robot
            print("Loading: "+program)

            # Put together full command string with path and current command
            prog = "load " + self.DEFAULT_PATH + program + ".urp\n"
            # Send the data as bytes to thro the telnet connection
            self.tn.write(bytes(prog, 'ascii'))
            time.sleep(1)
            # Send the play command thro the telnet connection
            self.tn.write(b"play\n")
            time.sleep(1)

            self.log("Moving plate "+ str(self.plate_id) + " to " + str(program))

            has_played = False # Will stay at false if robots run status is never true
            while self.get_run_status() == "Program running: true\n": # Freeze roboRunner if arm is being used
                print("PLAYING")
                time.sleep(1)
                has_played = True

            # Free up lid spot after puting lid back on the plate
            if program in self.pd.sw_lidOn:
                spot = self.get_list_spot(self.plate_id,self.lid_spots)
                self.lid_spots[spot] = -1

            # Free up hotel spot after taking the plate from the hotel
            if program in self.pd.hg:
                spot = self.get_list_spot(self.plate_id,self.lid_spots)
                self.hotel_spots[spot] = -1

            if has_played:
                print("Finished: " + program)
                self.log("Succecfully moved plate "+ str(self.plate_id) + " to " + str(program))
            else:
                print("Failed: " + program)
                self.log("Failed moving plate "+ str(self.plate_id) + " to " + str(program))


    # Return a list index of a specific value
    # Including exception for non-existing
    def get_list_spot(self,plate_id,lista):
        try:
            return lista.index(plate_id)
        except ValueError:
            return -1

    # Play the various devices by sending the corresponding
    # get requests:
    def play_washer(self, protocol):
        time.sleep(1) # Give the arm time to move out of the way
        while (not self.is_washer_ready()):
            time.sleep(1)
            print("Waiting for washer to get ready")
        print("Starting Washer")
        p1, p2 = protocol.rsplit(": ")
        self.log("Starting washer: "+p2)
        requests.get(self.WASHER_PATH + p2)

    def play_dispenser(self, protocol):
        time.sleep(1) # Give the arm time to move out of the way
        while (not self.is_dispenser_ready()):
            time.sleep(1)
            print("Waiting for dispenser to get ready")
        print("Starting dispenser")
        p1, p2 = protocol.rsplit(": ")
        self.log("Starting dispenser: "+p2)
        requests.get(self.DISPENSER_PATH + p2)

    def play_shaker(self, protocol):
        time.sleep(1) # Give the arm time to move out of the way
        while (not self.is_shaker_ready()):
            time.sleep(1)
            print("Waiting for shaker to get ready")
        print("Starting shaker")
        p1, p2 = protocol.rsplit(": ")
        self.log("Starting shaker: "+p2)
        requests.get(self.SHAKER_PATH + p2)


    # Wait for the various devices by sending the corresponding
    # get requests:
    def is_dispenser_ready(self):
        r = requests.get('http://dispenser.lab.pharmb.io:5001/is_ready')
        r_dict = r.json()
        if str(r_dict['value']) == "True":
            print("Dispenser is ready")
            return True
        else:
            print("Dispenser is not ready")
            return False

    def is_washer_ready(self):
        r = requests.get('http://washer.lab.pharmb.io:5000/is_ready')
        r_dict = r.json()
        if str(r_dict['value']) == "True":
            print("Washer is ready")
            return True
        else:
            print("Washer is not ready")
            return False

    def is_shaker_ready(self):
        r = requests.get('http://shaker.lab.pharmb.io:5000/is_ready')
        r_dict = r.json()
        if str(r_dict['value']) == "True":
            print("Shaker is ready")
            return True
        else:
            print("Shaker is not ready")
            return False


    # Get last buffered item from telnet connection
    def read_last(self):
        #buffer = self.tn.read_eager().decode('ascii')
        buffer = self.tn.read_very_eager().decode('ascii')
        print(buffer)
        return buffer


    # Handles geting the last item from the telnet conection
    # by also removing junk.
    def get_run_status(self):
        junk = self.tn.read_very_eager()
        self.tn.write(b"running\n")
        time.sleep(1)
        status = self.read_last()
        #print("Run status: " + status)
        return status
