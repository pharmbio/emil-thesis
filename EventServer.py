#!/usr/bin/env python3

import socket
import threading
import time
import pickle
import re
from datetime import datetime

from Plate import Plate
from RoboConnect import RoboConnect
from BuildProtocol import BuildProtocol
from RoboRun import RoboRun
from Prioritizer import Prioritizer


class EventServer:

    def __init__(self,ip = '127.0.0.1',port = 65432):
        self.host = ip # IP to run input server on
        self.port = port # Port to run input server on
        self.Running = True # For debuging: Run robot and devices

        self.plate_list = [] # List to collect all added plates
        self.lid_spots = [-1]*3 # Amount of lid spots, -1 means the spot is free
        self.hotel_spots = [0]*14 # Amount of hotel spots

        self.current_global_position = "h_get" # Current system position (default h_get)
        self.build_checkpoints = BuildProtocol()
        self.robot_connection = RoboConnect()
        self.robot_run = RoboRun()
        self.prioritizer = Prioritizer()

        self.connect_to_robot = True # For debugging: Connecting to robot


    # Run the different threads
    # - Get key inputs
    # - Plate input server
    # - Robot and device running
    def run_server(self):

        # Start connection to robot server
        if self.connect_to_robot:
            self.robot_connection.connect()

         # Thread: Get key inputs
        key_input_manager = threading.Thread(target=self.get_input, args=('Message',))
        key_input_manager.start()

        # Thread: Get new plate inputs, protocol files or single commmands
        input_server = threading.Thread(target=self.plate_inputs)
        input_server.start()

        # Thread: Run robot and device system
        input_server = threading.Thread(target=self.system_runner)
        input_server.start()


    # Saves a string and time stamp to a file
    def log(self,str_):
        with open('log', 'a') as file:
            do = datetime.now()
            file.write(do.hour, ':', do.minute, ':', do.second, ' ',str_)


    # Run the robot and devices by picking
    # what plate to move next with the priorotizer.
    def system_runner(self):

        while True: # Loop forever
            # Don't run if the plate list is empty
            if len(self.plate_list) == 0:
                time.sleep(2)
                continue

            # Perform the next move. (Robot / Device)
            # Add threading here for overlapping movment
            self.move_next()


    # Performs the actions needed to advance the system
    # - Sets up where to move from and to (with the help of the priorotizer)
    # - Uses the checkpoint builder to get checkpoints between these points
    # - Uses the telnet connection to the robot computer to issue the commands
    # When reached target, change current to dest and move on etc.
    def move_next(self): # Do the next moves
        move_from = self.current_global_position # The position to move from
        plateToMove = self.prioritizer.get_prio_plate(self.plate_list,self.hotel_spots,self.lid_spots) # Get what plate should be moved
        move_to = plateToMove.path[plateToMove.cur_step] # Where to move this plate
        movment = [move_from,move_to] # Pack it into a list for convenience (and in case longer movements will be done in the futuure)
        self.log("Deciding to move plate " +str(plateToMove.id)) 

        data_list = [self.hotel_spots,self.lid_spots] # Get the current hotel and lid spot statuses and pack it to a list
        movement_with_cp = self.build_checkpoints.build_protocol(movment,plateToMove.id, data_list) # Build checkpoints

        # Run system between the 2 steps including checkpoints
        if self.connect_to_robot:
            updated_lists = self.robot_run.start(self.robot_connection.tn, movement_with_cp,data_list,plateToMove) # Holds this thread until the run is done, might want to split

            self.hotel_spots = updated_lists[0]
            self.lid_spots = updated_lists[1]

            self.current_global_position = move_to # Set the systems current global position to where it just moved
            self.plate_list[self.get_plate_list_index(plateToMove)].step() # Advance plate to next step in path
            
        else: # For debugging
            time.sleep(20)


    # Establish TCP-connection to accept protocol on 
    def plate_inputs(self):
        # Adress family - IPv4; Socket type - TCP;
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # To force socket rebinding
            s.bind((self.host, self.port)) # Associate socket with specific network interface nad port
            s.listen() # Enables server to accept connections / Makes it a listening socket
            print('Protocol server started successfully!')


            while self.Running:

                conn, addr = s.accept() # New connection creates new s. Touple (ip,port)
                with conn: # With the new connection

                    # Add new plate
                    print('New entry by', addr)
                    data = pickle.loads(conn.recv(4096)) # Reads what client sends
                    plate_number = len(self.plate_list)+1 # Currently assigns the plate numbers (id) with +1, this should be changed

                    h_spot = re.findall(r'[0-9]+',data[0]) # Get the hotel spot to take the plate from
                    self.hotel_spots[int(h_spot[0])-1] = plate_number # Book that hotel spot in the list

                    newPlate = Plate(plate_number,data) # Create a new plate object

                    self.plate_list.append(newPlate)
                    self.log("New plate added with id: "+str(plate_number) + " ,at spot:" + str(h_spot))
                    print('Current amount of plates: ' +str(len(self.plate_list)))

                    conn.send(bytes("Entry successfully added!","ascii"))
        #s.close()


    # Check for inputs 
    # (This gets a bit messy to run at the server because of
    # all the outputs in the terminal.
    # There should probably be a input client or something
    # instead.)
    def get_input(self,s):
        while True:
            s = input()
            time.sleep(0.5)

            if "plate" in s:
                if self.is_num(s):
                    num = int(s[len(s)-1])
                    if len(self.plate_list) >= num:
                        self.get_plate_info(num-1)
                    else:
                        print("Plate not found")
            elif "check plates" in s:
                self.check_plates()

            elif "check hotel" in s:
                self.check_hotel()
            elif "check lid" in s:
                self.check_lid()

    # Print and log hotel spot status
    def check_hotel(self):
        i = 0
        for cur_spot in self.hotel_spots:
            if cur_spot == 0:
                check = "empty"
            else:
                check = "{Plate id: " +str(cur_spot) + "}"

            str_ = "Hotel spot " + str(i+1) + ": " + check
            print(str_)
            self.log("str_")
            i += 1

    # Print and log lid spot status
    def check_lid(self):
        i = 0
        for cur_spot in self.lid_spots:
            if cur_spot == -1:
                check = "empty"
            else:
                check = "{Plate id: " +str(cur_spot) + "}"

            str_ = "Lid spot " + str(i+1) + ": " + check
            print(str_)
            self.log(str_)
            i += 1

    # Print and log plates in the system
    def check_plates(self):
        for cur_plate in self.plate_list:
            str_ = "Plate id: " + str(cur_plate.id)
            print(str_)
            self.log(str_)

    # Print info about certain plate
    def get_plate_info(self,plate_num):
        plate = self.plate_list[plate_num]
        print("Plate id: {0}, status:".format(plate.id))
        print("Current position: {0}".format(plate.path[plate.cur_step]))
        # Check if not at last
        print("Destination: {0}".format(plate.path[plate.cur_step+1]))

    # Helper to check for digit
    def is_num(self,string):
        return any(i.isdigit() for i in string)


    # Return a list index of a specific value
    # Including exception for non-existing
    def get_plate_list_index(self,id):
        i = 0
        for p in self.plate_list:
            if p.id == id:
                return i
            i+=1

    # Get the index of a spot with the value -1 (a free spot)
    def get_list_spot(self,plate_id,lista):
        try:
            return lista.index(plate_id)
        except ValueError:
            return -1




if __name__ == "__main__":
    e = EventServer("127.0.0.1",65432)
    e.run_server()
