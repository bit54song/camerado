from threading import Thread, Event, Lock

import cv2

from .stream import VideoStream


class VideoStreamThread(Thread):

    def __init__(self, path='/dev/video0', size=(640, 480)):
        self._stream = VideoStream(path, size)
        self._stop_event = Event()
        self._lock = Lock()
        self._frame = None
        super().__init__()

    @property
    def size(self):
        return self._stream.size

    @property
    def path(self):
        return self._stream.path

    def read(self, size=None):

        with self._lock:
            frame = self._frame

        if frame is not None and size is not None:
            frame = cv2.resize(frame, size)

        return frame

    def run(self):

        while not self._stop_event.is_set():

            with self._lock:
                self._frame = self._stream.read()

    def join(self, timeout=None):
        self._stop_event.set()
        super().join(timeout)

