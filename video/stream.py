import cv2


class VideoStream(object):

    def __init__(self, path='/dev/video0', size=(640, 480),
                 save_file=None, save_fps=30):
        self.path = path
        self.size = size
        self.save_file = save_file
        self.save_fps = save_fps
        self._capture_stream()

    def __del__(self):
        self.release()

    def release(self):

        try:
            self.cap.release()

            if self.save_file is not None:
                self.out.release()

        except:
            pass

    def _capture_stream(self):
        self.cap = cv2.VideoCapture(self.path)

        if self.path.startswith('/dev/'):
            width, height = self.size
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        if self.save_file is not None:
            self.out = cv2.VideoWriter(self.save_file,
                                       cv2.VideoWriter_fourcc(*'DIVX'),
                                       self.save_fps,
                                       self.size)

    def read(self, size=None):
        recv, frame = self.cap.read()

        if not recv:
            return

        if size is not None:
            frame = cv2.resize(frame, size)

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def write(self, frame, size=None):

        if self.save_file is None:
            return

        if size is not None:
            frame = cv2.resize(frame, size)

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self.out.write(frame)

    @staticmethod
    def draw_box(frame, box, color=(0, 255, 0), thickness=2):
        xmin, ymin, xmax, ymax = box
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, thickness)

    @staticmethod
    def draw_text(frame, text, anchor=None, color=(0, 255, 0), scale=1,
                  thickness=1):

        if anchor is None:
            height = frame.shape[0]
            anchor = (5, height - 5)

        cv2.putText(frame, text, anchor, cv2.FONT_HERSHEY_SIMPLEX,
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

