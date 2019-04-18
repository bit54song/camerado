from threading import Thread, Event, Lock

import cv2

from .stream import VideoStream


class VideoStreamFetcher(Thread):

    def __init__(self, path='/dev/video0', size=(640, 480),
                 save_file=None, save_fps=30):
        Thread.__init__(self)
        self._stream = VideoStream(path, size, save_file, save_fps)
        self._stop_event = Event()
        self._frame_lock = Lock()
        self._frame = None

    @property
    def size(self):
        return self._stream.size

    @property
    def path(self):
        return self._stream.path

    def read(self, size=None):

        with self._frame_lock:
            frame = self._frame

        if frame is not None and size is not None:
            frame = cv2.resize(frame, size)

        return frame

    def write(self, frame, size=None):
        self._stream.write(frame, size)

    def run(self):

        while not self._stop_event.is_set():
            frame = self._stream.read()

            with self._frame_lock:
                self._frame = frame

    def stop(self, timeout=None):
        self._stop_event.set()
        super().join(timeout)

