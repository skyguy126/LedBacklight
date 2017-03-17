import pyaudio, sys, time, signal, numpy, json, serial
from AudioCapture import AudioCapture
from Tkinter import *
import pyqtgraph as pg
from ctypes import *

signal.signal(signal.SIGINT, signal.SIG_DFL)

def find_sound_card():
    p = pyaudio.PyAudio()
    device_number = -1

    for i in xrange(0, p.get_host_api_info_by_index(0).get('deviceCount')):
        device = p.get_device_info_by_host_api_device_index(0, i)
        device_input_channel_count = device.get('maxInputChannels')
        device_name = device.get('name')

        if device_input_channel_count > 0 and "Stereo Mix" in device_name:
            device_number = i

    return device_number

def find_controller(id):
    dll = cdll.LoadLibrary("wmicom3.dll")
    return dll.wmicom(id)

def calc_threshold(data, low, high, b1, b2):

    sqrsum = 0.0

    for i in xrange(low, high):
        sqrsum += y[i]**2

    threshold = numpy.sqrt(sqrsum)

    if threshold <= b1:
        return 0.0, threshold
    elif threshold > b2:
        return 1.0, threshold
    else:
        return get_scaled_val(((threshold - b1) / (b2 - b1))), threshold

def get_scaled_val(x):
    return numpy.exp(5.5 * (x - 1))

def exit(destroy=False):
    print "exiting..."
    if destroy: root.destroy()
    if ser.is_open: ser.close()
    a.stop()
    sys.exit(-1)

if __name__ == "__main__":

    sound_card_port = find_sound_card()
    assert sound_card_port > -1
    print "Stereo Mix ID: " + str(sound_card_port)

    with open("secure.txt", 'r') as f:
        controller_port = "\\\\.\\COM" + str(find_controller(f.readline().strip('\n')))
        print "Controller port: " + str(controller_port)

    ser = serial.Serial(port=controller_port, baudrate=9600)
    if ser.is_open: ser.close()
    ser.open()

    a = AudioCapture(sound_card_port)
    a.setup()
    a.start()

    low_b1 = 750.0
    low_b2 = 1000.0

    mid_b1 = 95.0
    mid_b2 = 120.0

    # TKINTER

    root = Tk()
    root.wm_title("Audio Visualizer")
    root.iconbitmap(r'favicon.ico')

    text_id = Text(root, height=1, width=35)
    text_percent = Text(root, height=1, width=35)
    text_raw = Text(root, height=1, width=35)

    text_id.pack()
    text_percent.pack()
    text_raw.pack()

    text_id_text = "low\tmid\thigh"
    text_id.delete(1.0, END)
    text_id.insert(END, text_id_text)

    root.update_idletasks()
    root.update()

    # LOOP

    low_interp = numpy.zeros((3), dtype=numpy.float32)

    while True:
        x, y = a.get_fft()

        low_percent, low_sum = calc_threshold(y, 0, 11, low_b1, low_b2)
        mid_percent, mid_sum = calc_threshold(y, 34, 100, mid_b1, mid_b2)

        low_interp = numpy.roll(low_interp, 1)
        low_interp[0] = low_percent
        low_percent = numpy.average(low_interp)

        text_percent_text = str(round(low_percent, 2) * 100) + "%\t" + str(round(mid_percent, 2) * 100) + "%"
        text_raw_text = str(int(low_sum)) + "\t" + str(int(mid_sum))

        try:
            text_percent.delete(1.0, END)
            text_raw.delete(1.0, END)

            text_percent.insert(END, text_percent_text)
            text_raw.insert(END, text_raw_text)

            root.update_idletasks()
            root.update()
        except:
            print "window closed, exiting..."
            exit()

        data = {
            'l' : 1 - low_percent.item(),
            'm' : mid_percent,
        }

        try:
            ser.write(json.dumps(data) + '\n')
            ser.flush()
        except:
            exit(destroy=True)

        time.sleep(0.01)

    # PLOT (disabled for now)

    '''
    pw = pg.plot()
    pw.setRange(xRange=[0,22000], yRange=[0,1000])
    while True:
        try:
            x, y = a.get_fft()
            pw.plot(x, y, clear=True)
            pg.QtGui.QApplication.processEvents()
            time.sleep(0.01)
        except KeyboardInterrupt:
            print "exiting..."
            a.stop()
            sys.exit(0)
    '''
    '''

    root.update_idletasks()
    root.update()

    x, y = a.get_fft()
    with open("fft.txt", 'w') as target:
        target.truncate()
        for i in xrange(0, len(x)):
            target.write(str(i) + "\t" + str(x[i]) + "\n")

    '''
