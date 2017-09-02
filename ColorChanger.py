import time, signal, json, random
from Control import Control

signal.signal(signal.SIGINT, signal.SIG_DFL)
c = Control()

if __name__ == "__main__":

    with open("secure.txt", 'r') as f:
        c.find_controller_port(f.readline().strip('\n'))

    c.open_serial_port(9600)

    data = {
        'cmd' : 1,
        'mode' : 2,
    }

    c.write_serial_port(json.dumps(data))

    for i in xrange(0, 10):

        time.sleep(2.5)

        data = {
            'cmd' : 0,
            'r' : random.randint(0, 255),
            'g' : random.randint(0, 255),
            'b' : random.randint(0, 255),
        }

        print str(json.dumps(data))
        c.write_serial_port(json.dumps(data))
