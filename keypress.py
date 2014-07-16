from __future__ import division
import sys
import termios
import tty
import select


class Keypress:
    def __init__(self):
        self.termios = termios
        self.sys = sys
        self.old_settings = self.termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    def _getkey(self):
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)

    def __call__(self):
        return self._getkey()

    def __str__(self):
        return str(self._getkey())

    def __del__(self):
        print("__del__")
        self.termios.tcsetattr(self.sys.stdin, self.termios.TCSADRAIN, self.old_settings)

    def __exit__(self):
        print("__exit__")
        self.__del__()

try:
    import msvcrt

    Keypress._getkey = msvcrt.getch
except ImportError:
    pass

