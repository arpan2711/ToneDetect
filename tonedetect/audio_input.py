"""Real-time audio capture, buffered through a thread-safe queue."""

import queue

import sounddevice as sd


def list_input_devices():
    """Return list of (index, name) for devices with at least one input channel."""
    devices = sd.query_devices()
    return [
        (i, d["name"])
        for i, d in enumerate(devices)
        if d["max_input_channels"] > 0
    ]


class AudioInput:
    def __init__(self, samplerate=44100, blocksize=4096, channels=1, device=None):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.channels = channels
        self.device = device
        self.q = queue.Queue(maxsize=4)
        self.stream = None

    def _callback(self, indata, frames, time_info, status):
        mono = indata[:, 0].copy()
        try:
            self.q.put_nowait(mono)
        except queue.Full:
            try:
                self.q.get_nowait()
            except queue.Empty:
                pass
            self.q.put_nowait(mono)

    def start(self):
        self.stop()
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            channels=self.channels,
            device=self.device,
            callback=self._callback,
        )
        self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def set_device(self, device):
        self.device = device
        self.start()
