#!/usr/bin/env python3
import sys

from app import CameradoApplication


def main():
    app = CameradoApplication()
    app.mainloop()


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print('Unexpected error:', e, file=sys.stderr)
        sys.exit(1)

