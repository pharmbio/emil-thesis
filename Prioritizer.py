from BuildProtocol import BuildProtocol
from RoboRun import RoboRun

class Prioritizer:
    def __init__(self):
        self.build_checkpoints = BuildProtocol()
        self.robot_run = RoboRun()
    

    # Return a plate based on set conditions.
    # Currently priotizes plate in the order they
    # where added to the system, and if they are currently
    # in a running device.
    def get_prio_plate(self,plate_list,hotel_spots,lid_spots):

        for plate in plate_list: # Prioritises plates in added order
            cur_step = plate.path[plate.cur_step] # Get the current plats destination

            if self.build_checkpoints.w_get in cur_step: # Is current destination washer?
                if self.robot_run.is_washer_ready(): # Check if the washer is ready
                    return plate # Return this plate for running
                else:
                    continue # Continue and check if the next plate can be moved
            elif self.build_checkpoints.d_get in cur_step:
                if self.robot_run.is_dispenser_ready(): # Set a min time for readines
                    return plate
                else:
                    continue
            elif self.build_checkpoints.hg in cur_step:
                if self.robot_run.is_shaker_ready(): # Set a min time for readines
                    return plate
                else:
                   continue
            elif self.build_checkpoints.hp in cur_step: # Return plate to hotel
                # Reservs a hotel spot before returning plate to hotel
                fs = self.get_free_spot(hotel_spots)
                if fs != -1:
                    hotel_spots[fs] = plate.id
                    return plate
                else:
                    continue # Should not work in case robot is already holding a plate
            elif self.build_checkpoints.hg in cur_step: # Get plate from hotel
                # Reserv lid spot
                fs = self.get_free_spot(lid_spots)
                if fs != -1:
                    lid_spots[fs] = plate.id # Add lid spots directly to plate object?
                    return plate
                else:
                    continue # Should not work in case robot is already holding a plate
            else: # If last spot was not to a device
                return plate

        # if plate has no more paths, add h_put to free spot

        return -1

    # Get the index of a spot with the value -1 (a free spot)
    def get_free_spot(self,lista):
        index = 0
        for x in lista:
            if x == -1:
                return index
        return -1