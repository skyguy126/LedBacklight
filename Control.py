import pyaudio, serial
from ctypes import cdll

class Control:

    def __init__(self):
        self.controller_port = -1
        self.sound_card_port = -1
        self.serial_port = None
        self.brate = 0

    def wmicom(self, hardware_id):
        dll = cdll.LoadLibrary("wmicom3.dll")
        return dll.wmicom(hardware_id)

    def find_controller_port(self, hardware_id):
        self.controller_port = self.wmicom(hardware_id)
        assert self.controller_port >= 0

    def get_controller_port(self):
        return self.controller_port

    def find_sound_card_port(self, hardware_id):
        p = pyaudio.PyAudio()
        device_count = p.get_host_api_info_by_index(0).get('deviceCount')

        for i in xrange(0, device_count):
            device = p.get_device_info_by_host_api_device_index(0, i)
            device_input_channel_count = device.get('maxInputChannels')
            device_name = device.get('name')

            if device_input_channel_count > 0 and hardware_id in device_name:
                self.sound_card_port = i

        assert self.sound_card_port >= 0

    def get_sound_card_port(self):
        return self.sound_card_port

    def open_serial_port(self, brate):
        self.brate = brate
        com_port = "\\\\.\\COM" + str(self.controller_port)
        self.serial_port = serial.Serial(port=com_port, baudrate=self.brate)

        if self.serial_port.is_open: self.serial_port.close()
        self.serial_port.open()

    def close_serial_port(self):
        if self.serial_port.is_open: self.serial_port.close()

    def write_serial_port(self, payload):
        self.serial_port.write(payload + '\n')
        self.serial_port.flush()

    def read_line_serial_port(self):
        line = []

        while True:
            for c in self.serial_port.read():
                line.append(c)
                if c == '\n':
                    return "".join(line)
