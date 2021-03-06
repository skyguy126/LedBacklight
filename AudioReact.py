import sys, time, signal, numpy, json
from AudioCapture import AudioCapture
from Control import Control
from Tkinter import *
import pyqtgraph as pg

signal.signal(signal.SIGINT, signal.SIG_DFL)
c = Control()

low_b1 = 750.0
low_b2 = 1000.0

mid_b1 = 95.0
mid_b2 = 120.0

update_threshold = 1
update_counter = 1

def toggle_slow_mode():
    global update_threshold
    if slow_mode_var.get():
        update_threshold = 5
    else:
        update_threshold = 1

def low_slider1_func(val):
    global low_b1
    low_b1 = int(val)

def low_slider2_func(val):
    global low_b2
    low_b2 = int(val)

def mid_slider1_func(val):
    global mid_b1
    mid_b1 = int(val)

def mid_slider2_func(val):
    global mid_b2
    mid_b2 = int(val)

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
    c.close_serial_port()
    a.stop()
    sys.exit(-1)

if __name__ == "__main__":

    with open("secure.txt", 'r') as f:
        c.find_controller_port(f.readline().strip('\n'))

    c.find_sound_card_port("Stereo Mix")
    c.open_serial_port(9600)

    a = AudioCapture(c.get_sound_card_port())
    a.setup()
    a.start()

    # TKINTER

    root = Tk()
    root.wm_title("Audio Visualizer")
    root.iconbitmap(r'favicon.ico')
    root.resizable(0, 0)

    fr0 = Frame(root)

    text_id_label = Label(fr0, text="Range")
    text_percent_label = Label(fr0, text="Threshold")
    text_raw_label = Label(fr0, text="Raw")

    text_id = Text(fr0, height=1, width=20)
    text_percent = Text(fr0, height=1, width=20)
    text_raw = Text(fr0, height=1, width=20)

    text_id_label.grid(row=0, column=0)
    text_percent_label.grid(row=1, column=0)
    text_raw_label.grid(row=2, column=0)

    text_id.grid(row=0, column=1)
    text_percent.grid(row=1, column=1)
    text_raw.grid(row=2, column=1)

    text_id_text = "low\tmid"
    text_id.delete(1.0, END)
    text_id.insert(END, text_id_text)

    fr0.pack()

    fr1 = Frame(root)

    low_slider1_label = Label(fr1, text="low_l")
    low_slider2_label = Label(fr1, text="low_h")
    mid_slider1_label = Label(fr1, text="mid_l")
    mid_slider2_label = Label(fr1, text="mid_h")

    low_slider1 = Scale(fr1, resolution=10, length=300, orient=VERTICAL, from_=2500, to=25, command=low_slider1_func)
    low_slider2 = Scale(fr1, resolution=10, length=300, orient=VERTICAL, from_=2500, to=25, command=low_slider2_func)
    mid_slider1 = Scale(fr1, resolution=10, length=300, orient=VERTICAL, from_=500, to=25, command=mid_slider1_func)
    mid_slider2 = Scale(fr1, resolution=10, length=300, orient=VERTICAL, from_=500, to=25, command=mid_slider2_func)

    low_slider1.set(750)
    low_slider2.set(1000)
    mid_slider1.set(95)
    mid_slider2.set(120)

    low_slider1.grid(row=0, column=0)
    low_slider2.grid(row=0, column=1)
    mid_slider1.grid(row=0, column=2)
    mid_slider2.grid(row=0, column=3)

    low_slider1_label.grid(row=1, column=0)
    low_slider2_label.grid(row=1, column=1)
    mid_slider1_label.grid(row=1, column=2)
    mid_slider2_label.grid(row=1, column=3)

    fr1.pack()

    fr2 = Frame(root)

    slow_mode_var = IntVar()
    react_mode_var = IntVar()

    slow_mode_check_button = Checkbutton(fr2, text="Enable slow mode", variable=slow_mode_var, command=toggle_slow_mode)
    react_mode_check_button = Checkbutton(fr2, text="Disable audio react", variable=react_mode_var)

    slow_mode_check_button.grid(row=0, column=0)
    react_mode_check_button.grid(row=1, column=0)

    fr2.pack()

    root.update_idletasks()
    root.update()

    # Set mode to audio react

    data = {
        'cmd' : 1,
        'mode' : 1,
    }

    try:
        c.write_serial_port(json.dumps(data))
    except:
        exit(destroy=True)

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
            if update_counter >= update_threshold:
                text_percent.delete(1.0, END)
                text_raw.delete(1.0, END)

                text_percent.insert(END, text_percent_text)
                text_raw.insert(END, text_raw_text)

                update_counter = 1
            else:
                update_counter += 1

            root.update_idletasks()
            root.update()
        except:
            print "window closed, exiting..."
            exit()

        data = {
            'cmd' : 0,
            'low' : 1 - low_percent.item() if react_mode_var.get() != 1 else 1,
            'med' : mid_percent if react_mode_var.get() != 1 else 1,
        }

        try:
            c.write_serial_port(json.dumps(data))
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
