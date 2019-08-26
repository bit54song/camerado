import time


class VideoFrameCounter(object):

    def __init__(self):
        self.stream = None
        self.fps = None

    def start(self):
        self.stream = {}
        self.fps = None
        self.t_start = time.time()

    def update(self, name):
        self.stream[name] = self.stream.get(name, 0) + 1

    def stop(self):

        if self.stream is None:
            return

        t_elapsed = time.time() - self.t_start
        self.fps = {}

        for name, frames in self.stream.items():
            self.fps[name] = round(frames / t_elapsed, 2)

        self.stream = None

