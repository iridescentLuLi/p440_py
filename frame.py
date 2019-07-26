import numpy as np
import struct

FRAME_SIZE = 1326
SIGNAL_LENGTH = 640
POS_CHANNEL = 8
POS_SIGNAL = 10

class Frame():
    '''
    This class is used to parse a frame of returned data from FPGA
    '''
    
    def __init__(self, data_bytes):

        #public properties
        self.data_bytes = data_bytes
        self.channel = None
        self.temp = None
        self.monitor_type = None #0 1 2 3 4 5
        self.monitor_value = None 
        self.data = None #numpy array

        #init
        if len(data_bytes) != FRAME_SIZE:
            raise Exception("data length not correct")
        if self.data_bytes[0] != 0x7e or self.data_bytes[1] != 0x5a or \
            self.data_bytes[-2] != 0x33 or self.data_bytes[-1] != 0x33:
            raise Exception("frame flag not correct")

        self.channel = self.data_bytes[POS_CHANNEL]
        temp_bytes = self.data_bytes[4:6]
        self.temp = (struct.unpack('h', temp_bytes)[0] >> 3) * 0.0625
        temp_bytes = self.data_bytes[2:4]
        monitor_data = struct.unpack('H', temp_bytes)[0]
        self.monitor_type = monitor_data >> 12
        self.monitor_value = monitor_data & 0x0ffff

        if self.monitor_type == 0: # 12V
            self.monitor_value = 3.0 * 5.0 * self.monitor_value / 4096.0
        if self.monitor_type == 1: # 5V
            self.monitor_value = 5.0 * self.monitor_value / 4096.0
        if self.monitor_type == 2: # 3.3V
            self.monitor_value = 5.0 * self.monitor_value / 4096.0
        if self.monitor_type == 3: # 2A
            self.monitor_value = self.monitor_value / 4096.0
        if self.monitor_type == 4: # 0.02A
            self.monitor_value = 5 * self.monitor_value / 6 / 4096.0
        if self.monitor_type == 5: # 3A
            self.monitor_value = 5 * self.monitor_value / 4 / 4096.0
        self.data = np.array(struct.unpack('640h', self.data_bytes[POS_SIGNAL:POS_SIGNAL + SIGNAL_LENGTH * 2]))

if __name__ == '__main__':

    f = open('test.dat', 'rb')
    bytes_arr = f.read(1326)
    frame1 = Frame(bytes_arr)
    bytes_arr = f.read(1326)
    frame2 = Frame(bytes_arr)
    pass