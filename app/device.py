import tkinter as tk
from functools import partial
from tkinter import messagebox


class DeviceSettingsFrame(tk.Frame):

    def __init__(self, settings, master=None):
        super().__init__(master)
        self.settings = settings
        self.create_widgets()

    def create_widgets(self):
        # Settings:
        set_list = self.settings.get()
        self.controls = {}

        for s in set_list:

            if s.get('flags', '') == 'inactive':
                continue

            label_text = s['name'].replace('_', ' ')
            frame = tk.LabelFrame(self.master, text=label_text)
            frame.pack(fill='both', expand=True, padx=5)

            if s['type'] == 'int':
                var = tk.IntVar(self.master, value=s['value'])
                self.controls[s['name']] = {'settings': s, 'variable': var}

                res = s.get('step') or 1
                command = partial(self.update_settings, s['name'])

                tk.Scale(frame, from_=s['min'], to=s['max'],
                    orient='horizontal', variable=var, showvalue=False,
                    resolution=res, command=command).pack(
                    side='left', fill='both', expand=True, padx=2)

                entry = tk.Entry(frame, textvariable=var, width=5)
                entry.bind('<Return>', lambda event, name=s['name']:
                    self.update_settings(name, value=None))
                entry.pack(
                    side='left', padx=2)

            elif s['type'] == 'bool':
                var = tk.IntVar(self.master, value=s['value'])
                self.controls[s['name']] = {'settings': s, 'variable': var}

                command = partial(self.update_settings, s['name'], None)

                tk.Checkbutton(frame, text='on/off toggle', variable=var,
                    command=command).pack(side='left')

            else:
                menu_entry = s['menu'][s['value']]
                var = tk.StringVar(self.master, value=menu_entry)

                self.controls[s['name']] = {
                    'settings': s,
                    'variable': var,
                    'val_name_map': s['menu'],
                    'name_val_map': {v: k for k, v in s['menu'].items()}
                }

                command = partial(self.update_settings, s['name'])
                menu_entries = list(s['menu'].values())

                tk.OptionMenu(frame, var, menu_entry, *menu_entries,
                    command=command).pack(side='left')

        # Reset to defaults button:
        tk.Button(self.master, text='Default Settings',
            command=self.reset_to_defaults).pack(
            side='right', padx=5, pady=5)

        # Update controls button:
        tk.Button(self.master, text='Update Controls',
            command=self.update_controls).pack(
            side='right', padx=5, pady=5)

    def reset_to_defaults(self):
        set_list = self.settings.get()

        for s in set_list:
            s['value'] = s['default']
            ctr = self.controls.get(s['name'])

            if ctr is None:
                continue

            if ctr['settings']['type'] in ('int', 'bool'):
                ctr['variable'].set(s['default'])
            else:
                menu_entry = ctr['val_name_map'][s['default']]
                ctr['variable'].set(menu_entry)

        self.set_settings(set_list)

    def update_controls(self):

        for widget in self.master.pack_slaves():
            widget.destroy()

        self.create_widgets()

    def update_settings(self, name, value):
        ctr = self.controls[name]

        if value is None:
            value = ctr['variable'].get()
        else:

            if ctr['settings']['type'] == 'menu':
                value = ctr['name_val_map'][value]

        ctr['settings']['value'] = value
        self.set_settings([ctr['settings']])

    def set_settings(self, vals):

        try:
            self.settings.set(vals)
        except Exception as e:
            messagebox.showerror('Error', str(e))

