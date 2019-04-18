import re
from pathlib import Path
from subprocess import Popen, TimeoutExpired, PIPE


class VideoDeviceSettings():

    def __init__(self, dev='/dev/video0', timeout=None):
        self.dev = dev
        self.timeout = timeout

    def get(self):

        try:
            set_str = self._exec_shell(['v4l2-ctl', '-d', self.dev, '-L'])
            set_list = self._str_to_list(set_str)
        except:
            raise RuntimeError('Failed to get device settings.')

        return set_list

    def get_resolutions(self):

        try:
            formats = self._exec_shell(
                ['v4l2-ctl', '-d', self.dev, '--list-formats-ext'])
        except:
            raise RuntimeError('Failed to get device resolutions.')

        str_list = re.findall(r'\s(\d+x\d+)', formats)
        str_list = list(set(str_list))
        res_list = []

        for s in str_list:
            w, h = s.split('x')
            res_list.append((int(w), int(h)))

        return sorted(res_list, key=lambda x: x[0])

    def reset_to_defaults(self):
        settings = self.get()

        for entry in settings:

            try:
                entry['value'] = entry['default']
            except KeyError:
                pass

        self.set(settings)

    def set(self, settings):
        bool_sets = []
        menu_sets = []
        other_sets = []

        for s_entry in settings:

            if s_entry.get('flags') == 'inactive':
                continue

            s_type = s_entry.get('type')

            if s_type == 'bool':
                bool_sets.append(s_entry)
            elif s_type == 'menu':
                menu_sets.append(s_entry)
            else:
                other_sets.append(s_entry)

        print('>> Device: {path}'.format(path=self.dev))
        # The order does matter. First apply bool settings, then menu settings,
        # and finally the other ones:

        for sets in (bool_sets, menu_sets, other_sets):

            if not sets:
                continue

            set_str = self._list_to_str(sets)
            print('!! Apply video settings: {s}'.format(s=set_str), flush=True)

            self._exec_shell(['v4l2-ctl', '-d', self.dev, '--set-ctrl', set_str])

    def _exec_shell(self, args):

        proc = Popen(args, stdout=PIPE, stderr=PIPE)

        try:
            outs, errs = proc.communicate(timeout=self.timeout)
        except TimeoutExpired:
            proc.kill()
            raise

        if errs:
            raise RuntimeError(errs.decode('utf-8'))

        return outs.decode('utf-8') or None

    def _str_to_list(self, set_str):
        set_list = []
        lines = [i.strip() for i in set_str.strip().split('\n')]

        for line in lines:
            # Check if menu entry:
            menu_entry = re.findall(r'^(\d+):\s(.+)$', line)

            if menu_entry:
                val, desc = menu_entry[0]

                menu = set_list[-1].get('menu', {})
                menu[int(val)] = desc

                set_list[-1]['menu'] = menu
            else:
                # Find parameter name and type (int, bool, or menu):
                name_type = re.findall(r'^(\w+)\s*.*\s\((\w+)\)', line)

                if not name_type:
                    continue

                name, param_type = name_type[0]

                param_entry = {
                    'name': name,
                    'type': param_type,
                }

                params = re.findall(r'(\w+)=(\S+)', line)

                for name, val in params:

                    try:
                        param_entry[name] = int(val)
                    except ValueError:
                        param_entry[name] = val

                set_list.append(param_entry)

        return sorted(set_list, key=lambda x: x['name'])

    def _list_to_str(self, set_list):
        toks = ['{n}={v}'.format(n=s['name'], v=s['value']) for s in set_list]

        return ','.join(toks)

    @staticmethod
    def device_list():
        return sorted([str(dev) for dev in Path('/dev').glob('video*')])

