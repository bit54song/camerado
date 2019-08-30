import time

import cv2


class VideoStream(object):

    def __init__(self, path='/dev/video0', size=(640, 480), fps=None):
        self.path = path
        self.size = size
        self.fps = fps
        self.cap = self._capture_stream()

    def __del__(self):
        cap = getattr(self, 'cap', None)

        if cap is not None:
            cap.release()

    def _capture_stream(self):
        cap = cv2.VideoCapture(self.path)

        if self.path.startswith('/dev/'):
            width, height = self.size
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

        return cap

    def grab(self):
        return self.cap.grab()

    def retrieve(self):
        success, frame = self.cap.retrieve()

        if not success:
            return

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def read(self, size=None, timeout=None):
        t_start = time.time()

        while True:
            t_fetch_start = time.time()
            success, frame = self.cap.read()
            t_elapsed = time.time() - t_start

            if timeout and t_elapsed > timeout:
                raise TimeoutError('Failed to read from {p}, timeout {t:.5f} '
                                   'exceeded!'.format(p=self.path, t=timeout))

            if not success:
                continue

            if self.fps is not None:
                t_fetch_elapsed = time.time() - t_fetch_start

                if t_fetch_elapsed < 0.25 / self.fps:
                    # It seems this is a buffered frame, try fetching again...
                    continue

            break

        if size is not None:
            frame = cv2.resize(frame, size)

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    @staticmethod
    def draw_box(frame, box, color=(0, 255, 0), thickness=2):
        xmin, ymin, xmax, ymax = box
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, thickness)

    @staticmethod
    def draw_text(frame, text, anchor=None, color=(0, 255, 0), thickness=1,
                  scale=1):

        if anchor is None:
            height = frame.shape[0]
            anchor = (5, height - 5)

        cv2.putText(frame, text, anchor,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    scale, color, thickness)

    @staticmethod
    def save(frame, filename, size=None):

        if size is not None:
            frame = cv2.resize(frame, size)

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(filename, frame)

    @staticmethod
    def show(frame, title=None):

        if frame is None:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.imshow(title, frame)

    @staticmethod
    def is_key_pressed(key):
        return cv2.waitKey(1) & 0xFF == ord(key)

    @staticmethod
    def close_windows():
        cv2.destroyAllWindows()

