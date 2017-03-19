# LedBacklight
Multicolor LED audio visualizer/backlight.

## Concept

*This will focus mostly on the software aspect of the project.*

Before I begin, here is [the excellent blog post](http://www.swharden.com/wp/2013-05-09-realtime-fft-audio-visualization-with-python/) which helped me start
this project.

##### 1. Identify the sound card

Implementing this was pretty straightforward, just needed to know some how Windows identifies the device.
The OS names the sound card "Stereo Mix" (this varies across different computers) and lists it as a microphone.
Simple, right? All I needed to do was to do was pull a list of all attached audio devices and see which one
matches the name.

Using [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/) I was able to implement this in very few lines.

```python
def find_sound_card():
    p = pyaudio.PyAudio()
    device_number = -1

    for i in xrange(0, p.get_host_api_info_by_index(0).get('deviceCount')): # loop through all the attached devices
        device = p.get_device_info_by_host_api_device_index(0, i)           # get the current device object
        device_input_channel_count = device.get('maxInputChannels')         # check to see if this device is indeed "real"
        device_name = device.get('name')                                    # get the device name

        if device_input_channel_count > 0 and "Stereo Mix" in device_name:  
            device_number = i

    return device_number                                                    # return the value of Stereo Mix
```

##### 2. Read PCM data from the sound card
[Pulse code modulation](https://en.wikipedia.org/wiki/Pulse-code_modulation) abbreviated PCM, is essentially the audio
waveform in a digital format (probably cutting a lot of corners here). Again using [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/) the process was very simple. Set up a few buffers (arrays) to
store the PCM data and pull data from the sound card every 0.01 seconds.

```python
def __init__(self, device_number):
    self.device_number = device_number  # sound card id from step 1
    self.rate = 48100                   # standard sampling rate
    self.buffer_size = 1024             # buffer size (1024 worked best)
    self.record_time = 0.01
    self.run = True
    self.lock = threading.Lock()

def setup(self):
    self.num_buffers = int(self.rate * self.record_time / self.buffer_size)
    if self.num_buffers == 0: self.num_buffers = 1
    self.audio = numpy.empty((self.num_buffers * self.buffer_size), dtype=numpy.int16)

    # setup the pyaudio input stream for reading

    self.p = pyaudio.PyAudio()
    self.input_stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.rate, input=True,
        frames_per_buffer=self.buffer_size, input_device_index=self.device_number)
```

This process was done on a separate thread to avoid timing issues later (this way there is always fresh data in the buffer
no matter if a function slowed the rest of the program down, which is very important for real-time processing).

```python
def get_audio(self):
    audio_string = self.input_stream.read(self.buffer_size)
    return numpy.fromstring(audio_string, dtype=numpy.int16)

def record(self):
    while self.run:
        self.lock.acquire() # to ensure thread safety (reading the data while this thread is writing would cause a crash)
        for i in xrange(self.num_buffers):
            # read the PCM data and store in the buffer
            self.audio[i * self.buffer_size : (i+1) * self.buffer_size] = self.get_audio()
        self.lock.release()
```

Additionally, a few basic start and stop controls were added to the recording class.

##### 3. Process the PCM data

The key component here was the fast-fourier-transform (abbreviated fft), or better known as the
discrete-fourier-transform. The concept essentially states that any audio (signal) waveform (a complex trigonometric wave)
can be broken down into elementary sine and cosine functions of varying frequencies. We know that low frequency waves
associate to the low frequencies in the audio playing (same concept for mid and high frequencies).

Read [this](http://practicalcryptography.com/miscellaneous/machine-learning/intuitive-guide-discrete-fourier-transform/)
for an excellent introduction to the math behind the algorithm.

```python
def get_pcm(self):
    self.lock.acquire()
    data = self.audio.flatten() # prevent thread conflicts by acquiring the lock
    self.lock.release()
    return data

def get_fft(self):
    data = self.get_pcm()

    fft = numpy.abs(numpy.fft.fft(data * numpy.blackman(self.buffer_size)))
    fft = numpy.divide(fft, 1000)
    freq = numpy.fft.fftfreq(self.buffer_size, 1.0 / self.rate)

    return freq[:int(len(freq)/2)], fft[:int(len(fft)/2)]
```

Here we apply the fft to the raw PCM data which is first multiplied by a
[window function](http://dsp.stackexchange.com/questions/37925/signal-processing-fft-gives-very-high-magnitudes-for-low-frequencies),
to eliminate signal noise. The data is then scaled down by a factor of 1000 and the associated frequencies are calculated
using another handy numpy function. Note only half of the buffer is returned due to the fact that the other half mirrors
the values in the first half (there is a mathematical explanation behind this but just returning half the array suits the
purpose without over-complicating things).

##### 4. Afterword

The final step was simply to find and connect to the Arduino board over serial. The fft data was post-processed a little more:
linearly interpolated to eliminate choppiness, downscaled, and finally used to create threshold percentages. This data was sent over serial to the Arduino, which modified the PWM of the red, green, and blue LEDs based on the values.

###### TLDR

1. A separate thread reads data from the sound card every 0.01 seconds and stores it in a thread-safe buffer.
2. When the main loop requests frequency data from the other thread, the program performs a fast-fourier-transform
on the raw data and returns the array to the main thread.
3. The main thread dampens, scales, and interpolates this array based on some pre-determined factors.
4. Using the modified data, the program calculates the percentage of the magnitude of a set of frequencies in a
pre-determined threshold.
5. Frequency data is packed into a JSON buffer and is sent over serial to the Arduino board.
6. The Arduino reads these values and uses them as PWM values to control the brightness and RGB loop speed of the
LEDS.

## Resources
- [Google Material Icons ](https://material.io/icons/)
- A HSV to RGB algorithm which I forgot where I got from, but will update as soon as I find the source.
