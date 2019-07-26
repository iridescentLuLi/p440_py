import sys
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QMessageBox
from PyQt5 import Qt, QtCore
from main_window import Ui_MainWindow
import serial
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
import utils
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import threading
from scipy.signal import hilbert, chirp
import socket
from struct import *
from threading import Thread, Condition, Lock
import p440_config
import datetime

queue = []
lock = Lock()
count = 200

ip = '192.168.1.110'
port = 21210
portx = "/dev/tty.usbmodem101"
bps = 115200
timex = 0.5
ser = serial.Serial(portx,bps,timeout=timex)
# global status
update_figure_q = False
producer_thread_running_q = False

image_row = 200
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

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.set_callback()
        # self.set_up_ports()
        # self.set_up_gains()
        #self.showFullScreen()
        self.show()

        # #set signal
        # self.ui.com_btn.clicked.connect(self.com_btn_clicked)
        # #global variables
        # self.gain_map = None
        # self.serial_port = None

        #setup matplotlib
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui.figure_layout.addWidget(self.toolbar)
        self.ui.figure_layout.addWidget(self.canvas)
        self.ax1 = self.figure.add_subplot(111)
        #ax1.plot(np.sin(np.arange(1,100,0.1)))
        #ax2 = self.figure.add_subplot(212)
        #ax2.plot(np.cos(np.arange(1,100,0.1)))       
        plt.tight_layout()
        self.canvas.draw()

        #setup timer
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_canvas)
        timer.start(50)

        self.producer = ProducerThread().start()

        self.data_arr = []
        self.iter = 0
    
    def set_callback(self):
        self.ui.btn_read_config.clicked.connect(self.read_config)
        self.ui.btn_write_config.clicked.connect(self.wrtie_config)
        self.ui.btn_close.mouseReleaseEvent = lambda self, event: app.quit()
        self.ui.pushButton_run_stop.clicked.connect(self.run_stop)
        self.ui.pushButton_clear.clicked.connect(self.clear)
        self.ui.pushButton_save_data.clicked.connect(self.save_data)

        self.ui.btn_0.clicked.connect(lambda x:self.write_number(0))
        self.ui.btn_1.clicked.connect(lambda x:self.write_number(1))
        self.ui.btn_2.clicked.connect(lambda x:self.write_number(2))
        self.ui.btn_3.clicked.connect(lambda x:self.write_number(3))
        self.ui.btn_4.clicked.connect(lambda x:self.write_number(4))
        self.ui.btn_5.clicked.connect(lambda x:self.write_number(5))
        self.ui.btn_6.clicked.connect(lambda x:self.write_number(6))
        self.ui.btn_7.clicked.connect(lambda x:self.write_number(7))
        self.ui.btn_8.clicked.connect(lambda x:self.write_number(8))
        self.ui.btn_9.clicked.connect(lambda x:self.write_number(9))
        self.ui.btn_dot.clicked.connect(lambda x:self.write_number(-1))
        self.ui.btn_del.clicked.connect(lambda x:self.write_number(-2))

    def read_config(self):
        #ser = serial.Serial(portx,bps,timeout=timex)
        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #set operation mode
        # s.sendto(pack('>HHI', 0xf003, 0, 1), (ip, port))
        # confirm_message, addr = s.recvfrom(1500)
        # if confirm_message[0:2] == b'\xf1\x03':
        #     print('successful')
        # else:
        #     print('error')
        #     return
        packet_get_config = pack('>HHHH', 0xA5A5, 4, 0x1002, 0)
        ser.write(packet_get_config)
        #s.sendto(packet_get_config, (ip, port))
        #config_message, addr = s.recvfrom(1500)
        config_message = ser.read(1500)
        self.current_config = p440_config.Config(config_message)
        print('current_config.pckt_len is : ')
        print(self.current_config.pckt_len)
        #set gui
        
        self.ui.lineEdit_distance_start.setText(str(p440_config.ps2m(self.current_config.scan_start)))
        self.ui.lineEdit_distance_end.setText(str(p440_config.ps2m(self.current_config.scan_end)))

        self.ui.lineEdit_integration_index.setText(str(self.current_config.base_int_index))
        self.ui.lineEdit_gain.setText(str(self.current_config.transmit_gain))

    def wrtie_config(self):

        #print('write config clicked')
        T1, T2 = p440_config.m2ps(float(self.ui.lineEdit_distance_start.text()), float(self.ui.lineEdit_distance_end.text()))
        self.current_config.scan_start = T1
        self.current_config.scan_end = T2
        self.current_config.transmit_gain = int(self.ui.lineEdit_gain.text())
        self.current_config.base_int_index = int(self.ui.lineEdit_integration_index.text())

        #ser = serial.Serial(portx,bps,timeout=timex)
        ser.write(self.current_config.to_bytes())
        print(ser.isOpen)
        confirm_message = ser.read(1500)
        print('antenna_mode = ')
        print(self.current_config.antenna_mode)

    
        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.sendto(self.current_config.to_bytes(), (ip, port))
        #confirm_message, addr = s.recvfrom(1500)
        
        sync_pat, pckt_len, messtype, messid, status = unpack('>HHHHI', confirm_message)
        
        if messtype == 0x1101 and status == 0:
            self.show_message('写入成功')
        else:
            self.show_message('写入失败')
            
        

    def update_canvas(self):

        if not update_figure_q:
            return
        global queue
        if queue:
            lock.acquire()
            for line in queue:
                self.arr_original.add(line)
                if len(self.data_previous) == 0:
                    self.data_previous = line
                else:
                    # envelop = np.abs(hilbert(self.data_previous)) #- line))
                    # envelop = np.clip(np.round(63 * envelop / 10e3) + 1, -1e5, 64)
                    # self.arr_processed.add(envelop)
                    self.data_previous = line
            self.ax1.clear()
            n_last = self.arr_original.get_array_last_n(image_row + 1)
            envelop = np.abs(hilbert(n_last[0:-1] - n_last[1:]))
            envelop = np.clip(np.round(63 * envelop / 10e3) + 1, -1e5, 64)
            # self.ax1.imshow(self.arr_processed.get_array_last_n(image_row), aspect = 'auto')
            self.ax1.imshow(envelop, aspect = 'auto')
            self.canvas.draw()
            queue = []
            lock.release()
    
    def run_stop(self):

        global producer_thread_running_q
        global update_figure_q
        if producer_thread_running_q:
            producer_thread_running_q = False
            update_figure_q = False
            self.ui.pushButton_run_stop.setText('开始')
        else:
            self.arr_original = utils.SignalArray()
            self.arr_processed = utils.SignalArray()
            self.data_previous = []
            producer_thread_running_q = True
            update_figure_q = True
            self.ui.pushButton_run_stop.setText('结束')
        pass

    def clear(self):
        
        self.arr_original.clear()
        self.arr_processed.clear()
        self.update_canvas()
        pass

    def write_number(self, number):
        '''
            0 - 9
            -1 for '.'
            -2 for backsapce
        '''
        all_line_edits = [
            self.ui.lineEdit_distance_start,
            self.ui.lineEdit_distance_end,
            self.ui.lineEdit_interval,
            self.ui.lineEdit_integration_index,
            self.ui.lineEdit_gain
        ]
        for edit in all_line_edits:
            if edit.hasFocus():
                focused = edit
                break
        
        if not focused:
            return 

        if number <= 9 and number >= 0:
            input_char = str(number)

        elif number == -1:
            input_char = '.'

        current_text = focused.text()
        
        if number == -2:
            if current_text:
                current_text = current_text[0:-1]
        
        else:
            current_text = current_text + input_char
        
        edit.setText(current_text)

    def save_data(self):

        f_name = str(datetime.datetime.now()).replace(" ","_").replace(":","_").replace(".", "_").replace("-", "_")

        np.save(f_name, self.arr_original.get_array())
        self.show_message(f_name + " 已保存")

    def show_message(self, text):

        msg = QMessageBox()
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        ret = msg.exec_()
        


    # def set_up_ports(self):
    #     ports = list(serial.tools.list_ports.comports())
    #     for port in ports:
    #         self.ui.com_selector.addItem(port[0])

    # def set_up_gains(self):
    #     self.gain_map = {}
    #     gain_list = utils.load_gain_data()
    #     for item in gain_list:
    #         self.ui.gain_selector.addItem(item[0])
    #         self.gain_map[item[0]] = item[1]
    
    #callbacks
    # def com_btn_clicked(self, e):
    #     if (not self.serial_port) or (not self.serial_port.isOpen()):
    #         index_com = self.ui.com_selector.currentIndex()
    #         index_baud = self.ui.baud_selector.currentIndex()
    #         com = self.ui.com_selector.itemText(index_com)
    #         baud = self.ui.baud_selector.itemText(index_baud)
    #         #try:
    #         self.serial_port = serial.Serial(com)
    #         self.serial_port.baudrate = int(baud)
    #         self.ui.com_btn.setStyleSheet('background-color:green;color:white;')
    #         self.ui.com_btn.setText('关闭串口')
    #         #except:
    #             #QMessageBox.about(self, 'Warning', 'Failed to open port!')
    #         self.StartThread()
    #     else:
    #         if self.serial_port.isOpen():
    #             self.StopThread()
    #             self.serial_port.close()
    #         self.ui.com_btn.setStyleSheet('color:black;')
    #         self.ui.com_btn.setText('打开串口')

class ProducerThread(Thread):
    def run(self):
        ip = '192.168.1.110'
        port = 21210

        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ser = serial.Serial(portx,bps,timeout=timex)
        #s.settimeout(1.0)
        #s.connect((ip, port))
        count = 200
        #packet_get_config = pack('>HHHHI', 0x1003, 0, count, 0, 150 * 1000)
        #packet_get_config = pack('>HHHHI', 0x1003, 0, count, 0, 0)
        #s.sendto(packet_get_config, (ip, port))

        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s1.bind((ip, port))
        start_of_number_of_samples = 4 * 2 + 4 * 6 + 4 * 2 + 2 + 4 
        USBpfxNbyte = 4
        Confirm_msgLen = 8

        dt = np.dtype(int)
        dt = dt.newbyteorder('>')
        global queue
        global producer_thread_running_q

        i = 0
        while True:
            if not producer_thread_running_q:
                continue
            #print('received' + str(len(data)))
            #print(data[0:2])
            #print(data, addr)
            packet_get_config = pack('>HHHHHHI', 0xA5A5, 12, 0x1003, 0, 1, 0, 0)

            #s.sendto(packet_get_config, (ip, port))
            ser.write(packet_get_config)
            control_confirmMsg = ser.read(12)
            if control_confirmMsg[4:6] == b'\x11\x03':
                print('Data Received')
            while True:
                #data, addr = s.recvfrom(2000)
                data = ser.read(1456)
                #data = data[17:]
                #print(data)
                #print(len(data))
                if data[4:6] == b'\xf2\x01':

                    this_len, total_len, this_index, total_index = unpack('>HIHH', data[start_of_number_of_samples:start_of_number_of_samples + 10])
                    #print(this_len, total_len)
                    if this_index == 0:
                        binary_buff = b''
                    temp = data[start_of_number_of_samples + 10: start_of_number_of_samples + 10 + this_len * 4]
                    binary_buff = binary_buff + temp
                    if this_index == total_index - 1:
                        #print('binarybuff ' + str(i))
                        #print(binary_buff)
                        new_signal = np.frombuffer(binary_buff, dtype = dt)
                        lock.acquire()
                        queue.append(new_signal)
                        lock.release()
                        break

app = QApplication(sys.argv)
w = AppWindow()
w.show()
sys.exit(app.exec_())
