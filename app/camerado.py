import os
import time
import json
import tkinter as tk
from threading import Lock
from tkinter import messagebox, filedialog

from PIL import Image, ImageTk

from .device import DeviceSettingsFrame
from video import VideoStream, VideoDeviceSettings


class CameradoApplication(tk.Tk):

    MAX_ROI = 10
    UPDATE_DELAY = 50
    STREAM_CLOSE_DELAY = 2
    CANVAS_SIZE = (640, 480)
    DEFAULT_RESOLUTIONS = [(640, 480), (800, 600), (1024, 768), (1600, 1200)]

    def __init__(self):
        super().__init__()
        self.title('Camera Setup Application')

        self.device_settings_frame = None
        self.device_path = tk.StringVar(self, value='')
        self.resolution = tk.StringVar(self, value='')
        self.roi_spinbox_num = tk.StringVar(self, value='')
        self.create_widgets()

        self.stream_lock = Lock()
        self.roi_lock = Lock()
        self.reset_stream()

        self.update_device_menu()
        self.update_canvas()

        self.last_dir = None
        self.home_dir = os.path.expanduser('~')

    def reset_stream(self):

        with self.stream_lock:
            self.stream = None

        with self.roi_lock:
            self.roi_list = [None] * self.MAX_ROI
            self.roi_tmp = None
            self.roi_is_updating = False

    def create_widgets(self):
        # Menu:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=0)

        file_menu.add_command(label='Load', accelerator='<Ctrl-L>',
                              command=self.load_settings)
        file_menu.add_command(label='Save', accelerator='<Ctrl-S>',
                              command=self.save_settings)
        file_menu.add_separator()
        file_menu.add_command(label='Quit', accelerator='<Alt-F4>',
                              command=self.destroy)

        menu.add_cascade(label='File', menu=file_menu)
        self.config(menu=menu)

        # Key bindings:
        self.bind('<Control-l>', func=lambda _: self.load_settings())
        self.bind('<Control-s>', func=lambda _: self.save_settings())
        self.bind('<Alt-F4>', func=lambda _: self.destroy())

        # Video canvas:
        w, h = self.CANVAS_SIZE
        self.canvas = tk.Canvas(self, width=w, height=h, bg='gray')
        self.canvas.pack(
            side='left', fill='both', expand=True, padx=5, pady=5)
        self.canvas.bind('<Button-1>', self.mouse_click)
        self.canvas.bind('<B1-Motion>', self.mouse_drag)

        # Right panel:
        panel = tk.Frame(self)
        panel.pack(fill='x', padx=5, pady=5)

        # Device section:
        device = tk.LabelFrame(panel, text='Device')
        device.pack(fill='x', expand=True, padx=5, pady=5)

        # Path:
        entry = tk.Entry(device, textvariable=self.device_path)
        entry.bind('<Return>', self.open_device_path)
        entry.grid(
            row=0, column=0, padx=5, pady=1, sticky='ew')
        self.open_path_button = tk.Button(device, text='Open',
            command=self.open_device_path)
        self.open_path_button.grid(
            row=0, column=1, padx=5, pady=1, sticky='ew')
        tk.Button(device, text='Close', command=self.close_device_path).grid(
            row=0, column=2, padx=5, pady=1, sticky='ew')

        # Device list:
        self.device_menu = tk.OptionMenu(device, self.device_path, value='')
        self.device_menu.configure(width='15', anchor='w')
        self.device_menu.grid(
            row=1, column=0, padx=5, pady=1, sticky='ew')
        tk.Button(device, text='Update', command=self.update_device_menu).grid(
            row=1, column=1, padx=5, pady=1, sticky='ew')

        # Resolution:
        self.resolution_menu = tk.OptionMenu(device, self.resolution, value='')
        self.resolution_menu.configure(anchor='w')
        self.resolution_menu.grid(
            row=2, column=0, padx=5, sticky='we')
        tk.Button(device, text='Update', command=self.update_resolution).grid(
            row=2, column=1, padx=5, sticky='w')

        # Settings section:
        settings = tk.LabelFrame(panel, text='Device Settings')
        settings.pack(fill='x', expand=True, padx=5, pady=5)

        tk.Button(settings, text='Load', command=self.load_settings).pack(
            fill='x', padx=5, pady=2)
        tk.Button(settings, text='Save', command=self.save_settings).pack(
            fill='x', padx=5, pady=1)
        tk.Button(settings, text='Settings', command=self.settings_frame).pack(
            fill='x', padx=5, pady=1)

        # ROI section:
        roi = tk.LabelFrame(panel, text='ROI')
        roi.pack(fill='x', expand=True, padx=5, pady=5)

        tk.Label(roi, text='Box').pack(
            side='left', padx=2, pady=2)
        self.roi_spinbox_num.set('1')
        self.roi_spinbox = tk.Spinbox(roi, from_=1, to=self.MAX_ROI, width=2,
            textvariable=self.roi_spinbox_num)
        self.roi_spinbox.pack(
            side='left', padx=2, pady=2)
        self.roi_button = tk.Button(roi, text='Update',
            command=self.roi_list_update)
        self.roi_button.pack(
            side='left', padx=2, pady=2)
        tk.Button(roi, text='Rearrange',
            command=self.roi_list_rearrange).pack(
            side='left', padx=2, pady=2)

        # Snapshot button:
        tk.Button(panel, text='Snapshot', command=self.snapshot).pack(
            fill='x', padx=5, pady=5)

    def current_canvas_size(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        return (w, h)

    def update_canvas(self):

        if self.stream is not None:
            size = self.current_canvas_size()

            with self.stream_lock:
                frame = self.stream.read(size)

            if frame is not None:
                img = Image.fromarray(frame)
                self.photo = ImageTk.PhotoImage(img)
                self.canvas.create_image(0, 0, image=self.photo, anchor='nw')

                width, height = self.stream.size
                self.canvas.create_text(
                    15, 15, fill='yellow', font='Helvetica 10', anchor='w',
                    text='Res. {w}x{h}'.format(w=width, h=height))

                self.draw_roi_boxes()

        self.after(self.UPDATE_DELAY, self.update_canvas)

    def draw_roi_boxes(self):
        update_i = int(self.roi_spinbox_num.get())
        w, h = self.current_canvas_size()

        with self.roi_lock:

            for i, roi in enumerate(self.roi_list, start=1):

                if roi is None:
                    continue

                roi = [roi[0] * w, roi[1] * h, roi[2] * w, roi[3] * h]

                if self.roi_is_updating and i == update_i:
                    color = 'red'
                    self.canvas.create_rectangle(roi,
                                                 outline=color,
                                                 dash=(4, 4),
                                                 width=2)
                else:
                    color = 'blue'
                    self.canvas.create_rectangle(roi,
                                                 outline=color,
                                                 width=2)

                self.canvas.create_text(roi[0], roi[1] - 10,
                    fill=color, font='Helvetica 10', anchor='w',
                    text='ROI {i}'.format(i=i))

            if self.roi_tmp is not None:
                self.canvas.create_rectangle(self.roi_tmp,
                                             outline='blue',
                                             width=2)

    def roi_list_update(self):

        if self.stream is None:
            return

        update_i = int(self.roi_spinbox_num.get()) - 1
        w, h = self.current_canvas_size()

        with self.roi_lock:
            self.roi_is_updating = not self.roi_is_updating

            if self.roi_is_updating:
                self.roi_button['text'] = 'Finish Update'
                self.roi_spinbox.config(state='disabled')
            else:

                if self.roi_tmp is None:
                    self.roi_list[update_i] = None
                else:
                    roi = self.roi_tmp
                    x_start, y_start, x, y = roi

                    if x < x_start:
                        x_start, x = x, x_start

                    if y < y_start:
                        y_start, y = y, y_start

                    roi = [x_start, y_start, x, y]
                    roi = [roi[0] / w, roi[1] / h, roi[2] / w, roi[3] / h]
                    self.roi_list[update_i] = roi
                    self.roi_tmp = None

                self.roi_button['text'] = 'Update'
                self.roi_spinbox.config(state='normal')

    def roi_list_rearrange(self):

        if self.stream is None or self.roi_is_updating:
            return

        with self.roi_lock:
            roi = [roi for roi in self.roi_list if roi]
            self.roi_list = [None] * self.MAX_ROI

            for i, r in enumerate(roi):
                self.roi_list[i] = r

    def get_camera_roi(self):

        with self.roi_lock:
            roi_list = [roi for roi in self.roi_list if roi]

        return roi_list

    def set_camera_roi(self, roi_list):

        with self.roi_lock:
            self.roi_list = [None] * self.MAX_ROI

            for i, roi in enumerate(roi_list):
                self.roi_list[i] = roi

    def update_device_menu(self):
        menu = self.device_menu['menu']
        menu.delete(0, 'end')

        dev_list = VideoDeviceSettings.device_list()

        if dev_list:

            for dev in dev_list:
                menu.add_command(
                    label=dev,
                    command=lambda val=dev: self.device_path.set(val))

            self.device_path.set(dev_list[0])

    def update_resolution_menu(self):
        menu = self.resolution_menu['menu']
        menu.delete(0, 'end')

        if self.stream is None:
            return

        if self.settings is None:
            res_list = self.DEFAULT_RESOLUTIONS
        else:
            res_list = self.settings.get_resolutions()

        res_names = ['{w}x{h}'.format(w=w, h=h) for w, h in res_list]

        for res in res_names:
            menu.add_command(
                label=res,
                command=lambda val=res: self.resolution.set(val))

    def update_resolution(self):

        if self.stream is None:
            return

        res = self.resolution.get()

        if not res:
            return

        w, h = res.split('x')
        size = (int(w), int(h))
        self.create_stream(self.stream.path, size)

    def create_stream(self, path, size):

        try:

            with self.stream_lock:
                self.stream = None
                time.sleep(self.STREAM_CLOSE_DELAY)
                self.stream = VideoStream(path, size)

            if self.stream.path.startswith('/dev/'):
                self.settings = VideoDeviceSettings(path)
            else:
                self.settings = None

            self.update_resolution_menu()

        except Exception as e:
            messagebox.showerror('Error', str(e))

            with self.stream_lock:
                self.stream = None

            self.settings = None

    def load_settings(self):

        filename = filedialog.askopenfilename(
            initialdir=self.last_dir or self.home_dir,
            title='Open file',
            filetypes=[('json', '*.json')])

        if not filename:
            self.last_dir = None
            return

        print('Load settings from', filename)
        self.last_dir = os.path.dirname(filename)

        with open(filename, 'r') as f:
            cfg = json.load(f)

        self.close_device_settings_frame()
        self.create_stream(cfg['path'], tuple(cfg['resolution']))
        self.device_path.set(cfg['path'])

        if cfg['settings'] is not None:
            self.settings.set(cfg['settings'])

        if cfg['roi'] is not None:
            self.set_camera_roi(cfg['roi'])

    def save_settings(self):

        if self.stream is None:
            messagebox.showinfo('Info', 'Please open a video stream first.')
            return

        self.roi_list_rearrange()

        cfg = {
            'path': self.stream.path,
            'resolution': self.stream.size,
            'settings': self.settings.get() if self.settings else None,
            'roi': self.get_camera_roi()
        }

        filename = filedialog.asksaveasfilename(
            initialdir=self.last_dir or self.home_dir,
            title='Save file',
            filetypes=[('json', '*.json')])

        if not filename:
            self.last_dir = None
            return

        print('Save settings to', filename)
        self.last_dir = os.path.dirname(filename)

        with open(filename, 'w') as f:
            json.dump(cfg, f, indent=2)

    def settings_frame(self):

        if self.stream is None:
            return

        if not self.stream.path.startswith('/dev/'):
            messagebox.showinfo('Info', 'No settings for current device.')
            return

        if self.device_settings_frame is None:
            self.device_settings_frame = tk.Toplevel(self)

            self.device_settings_frame.title('Video Device Settings')
            self.device_settings_frame.protocol(
                'WM_DELETE_WINDOW', self.close_device_settings_frame)

            try:

                DeviceSettingsFrame(self.settings, self.device_settings_frame)

            except Exception as e:
                self.close_device_settings_frame()
                messagebox.showerror('Error', str(e))
        else:
            self.device_settings_frame.focus()

    def close_device_settings_frame(self):

        if self.device_settings_frame is not None:
            self.device_settings_frame.destroy()
            self.device_settings_frame = None

    def open_device_path(self, event=None):
        path = self.device_path.get()

        if not path:
            return

        self.create_stream(path, self.CANVAS_SIZE)
        self.open_path_button.config(state='disabled')

    def close_device_path(self):
        self.canvas.delete('all')
        self.open_path_button.config(state='normal')
        self.close_device_settings_frame()
        self.reset_stream()
        self.update_resolution_menu()
        self.resolution.set('')

    def snapshot(self):

        if self.stream is None:
            return

        with self.stream_lock:
            frame = self.stream.read()

        if frame is None:
            return

        filename = filedialog.asksaveasfilename(
            initialdir=self.last_dir or self.home_dir,
            title='Save file',
            filetypes=[('jpeg', '*.jpg'), ('png', '*.png')])

        if not filename:
            self.last_dir = None
            return

        self.last_dir = os.path.dirname(filename)

        self.roi_list_rearrange()
        roi_list = self.get_camera_roi()

        for i, roi in enumerate(roi_list, start=1):
            h, w = frame.shape[:2]
            roi = [int(roi[0] * w), int(roi[1] * h),
                   int(roi[2] * w), int(roi[3] * h)]
            VideoStream.draw_box(frame, roi)
            VideoStream.draw_text(frame, text='ROI {i}'.format(i=i),
                anchor=(roi[0], roi[1] - 5), scale=0.5)

        VideoStream.save(frame, filename)

    def mouse_click(self, event):

        if self.roi_is_updating:
            self.x_start = int(self.canvas.canvasx(event.x))
            self.y_start = int(self.canvas.canvasy(event.y))

    def mouse_drag(self, event):

        if self.roi_is_updating:
            x = int(self.canvas.canvasx(event.x))
            y = int(self.canvas.canvasy(event.y))

            with self.roi_lock:
                self.roi_tmp = [self.x_start, self.y_start, x, y]

