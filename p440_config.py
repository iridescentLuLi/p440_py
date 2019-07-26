from struct import *
import math
class Config:

    '''
    message_type    uint16
    message_id      uint16
    node_id         uint32
    scan_start      int32
    scan_end        int32
    scan_resolution uint16
    base_int_index  uint16
    seg1            uint16
    seg2            uint16
    seg3            uint16
    seg4            uint16
    seg1_int        uint8
    seg2_int        uint8
    seg3_int        uint8
    seg4_int        uint8
    antenna_mode    uint8
    transmit_gain   uint8
    code_channel    uint8
    persist_flag    uint8
    '''
    def __init__(self, frame_bytes):
        '''
            frame_bytes is confirm message
        '''
        struct_pattern = '>HHHHIiiHHHHHHBBBBBBBBII'
        (self.sync_pat, self.pckt_len, self.message_type, self.message_id, self.node_id, self.scan_start, self.scan_end,
        self.scan_resolution, self.base_int_index, self.seg1, self.seg2,
        self.seg3, self.seg4, self.seg1_int, self.seg2_int, self.seg3_int,
        self.seg4_int, self.antenna_mode, self.transmit_gain,
        self.code_channel, self.persist_flag, self.time_stamp, self.status) = unpack(struct_pattern, frame_bytes)

    def to_bytes(self):
        '''
            return config set message
        '''
        self.persist_flag = 1
        self.message_type = 0x1001
        self.node_id = 100
        self.scan_resolution = 32
        self.pckt_len = 36
        struct_pattern = '>HHHHIiiHHHHHHBBBBBBBB'
        return pack(
            struct_pattern,
            self.sync_pat, self.pckt_len, self.message_type, self.message_id, self.node_id, self.scan_start, self.scan_end,
        self.scan_resolution, self.base_int_index, self.seg1, self.seg2,
        self.seg3, self.seg4, self.seg1_int, self.seg2_int, self.seg3_int,
        self.seg4_int, self.antenna_mode, self.transmit_gain,
        self.code_channel, self.persist_flag
        )

def m2ps(m1, m2):

    c = 0.29979
    dTmin = 1/ (512 * 1.024)
    Tbin = 32 * dTmin
    dNBin = 96
    dT0 = 10 #ns related to antenna
    T1 = 2 * m1 / c + dT0
    T2 = 2 * m2 / c + dT0

    Nbin = (T2 - T1) / Tbin
    Nseg = math.ceil(Nbin / dNBin)
    Nbin = dNBin * Nseg

    T1 = math.floor(1000*dTmin* math.floor(T1/dTmin)) # in ps
    T2 = math.floor(1000*dTmin* math.floor(T2/dTmin)) # in ps
    return T1, T2

def ps2m(ps):

    c = 0.29979
    dT0 = 10
    return round(c * (ps / 1000 - dT0) / 2, 2)

if __name__ == '__main__':

    print(m2ps(0,5))



    

