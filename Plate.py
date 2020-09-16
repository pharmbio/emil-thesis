import re


class Plate:

    def __init__(self,id_,path):
        self.id = id_ # The plates unique id
        self.cur_step = 0 # The plates current step in the path
        self.path = path # The plates full path

        self.get_num = re.findall(r'[0-9]+',self.path[0]) # Collect number from first protocol spot (hotel spot)
        self.path[0] = "h_get" + self.get_num[0] # Turn user input start position into protocol name
        self.add_paths() # Directly add some specific needed paths
        self.path.append("h_put") # Add hotel return as last command
        #print(self.path)


    # Add some specific needed paths outside of protocol builder
    def add_paths(self):

        for i in range(len(self.path)+1):
      
            # Device get commands needs to be added here,
            # after there respective device play command
            if "washer" in self.path[i]:
                self.path.insert(i+1 , "w_get")
            elif "dispenser" in self.path[i]:
                self.path.insert(i+1 , "d_get")
            elif "shaker" in self.path[i]:
                self.path.insert(i+1 , "s_get")
            

    # Iterates plates current step
    # (In case of more advanced step features in the future)
    def step(self): 
        self.cur_step +=1
