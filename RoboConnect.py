import telnetlib
#import traceback

class RoboConnect:
    HOST = "cobot" # Robot computer IP, defined externally
    PORT = 29999 # Robot computer port

    def __init__(self):
        self.tn = -1

    # Connects to the robot computer with a telnet connection
    def connect(self):
        #try:
        print("Connecting to robot..")
        self.tn = telnetlib.Telnet(self.HOST, self.PORT)
        self.tn.read_until(b"Dashboard Server")
        # except Exception as e:
        #     print("No connection could be established..")
        #     #traceback.print_exc()
        print("Connected to robot successfully!")
        # self.tn.write('AT'+"\r")
        # if self.tn.read_until("OK"):
        #     print("Connection established!")


if __name__ == "__main__":
    r = RoboConnect()
    r.connect()
