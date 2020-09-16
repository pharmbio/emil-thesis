# robot_control_system
UR cobot controller  
  author: emil.kammarbo@gmail.com  
  current: wesley.schaal@farmbio.uu.se  

How to add a new device/main spot:
- Add the device_get position in Plate.add_paths()
- Add the device in BuildProtocol.__ini__() with new_pos
    - (As the washer/dispenser/shaker are added at the bottom)
- Also add in BuildProtocol.__ini__(), the new checkpoints needed to the new device.
    - (The string needs to have the exact same name [without .urp] as it has on the robot computer.
- In BuildProtocol.build_protocol(), add the proper checkpoints between a new s and sn check, as prevously done.
- Add new device to Prioritizer.get_prio_plate()
- Add new device URL at the top in RobotRun
- Add new play/is_ready command for the new device as done with the previous
    (This step could probably be simplified/organized better)

