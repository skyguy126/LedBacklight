import numpy, pyaudio, threading

class AudioCapture:

    def __init__(self, device_number):
        self.device_number = device_number
        self.rate = 48100
        self.buffer_size = 1024
        self.record_time = 0.01
        self.run = True
        self.lock = threading.Lock()

    def setup(self):
        self.num_buffers = int(self.rate * self.record_time / self.buffer_size)
        if self.num_buffers == 0: self.num_buffers = 1
        self.audio = numpy.empty((self.num_buffers * self.buffer_size), dtype=numpy.int16)

        self.p = pyaudio.PyAudio()
        self.input_stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.rate, input=True,
            frames_per_buffer=self.buffer_size, input_device_index=self.device_number)

    # AUDIO

    def get_audio(self):
        audio_string = self.input_stream.read(self.buffer_size)
        return numpy.fromstring(audio_string, dtype=numpy.int16)

    def record(self):
        while self.run:
            self.lock.acquire()
            for i in xrange(self.num_buffers):
                self.audio[i * self.buffer_size : (i+1) * self.buffer_size] = self.get_audio()
            self.lock.release()

    # CONTROL

    def start(self):
        self.t = threading.Thread(target=self.record)
        self.t.start()

    def stop(self):
        self.run = False
        self.t.join()
        self.p.close(self.input_stream)

    # MATH

    def get_pcm(self):
        self.lock.acquire()
        data = self.audio.flatten()
        self.lock.release()
        return data

    def get_fft(self):
        data = self.get_pcm()

        fft = numpy.abs(numpy.fft.fft(data * numpy.blackman(self.buffer_size)))
        fft = numpy.divide(fft, 1000)
        freq = numpy.fft.fftfreq(self.buffer_size, 1.0 / self.rate)

        return freq[:int(len(freq)/2)], fft[:int(len(fft)/2)]
