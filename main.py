import os
import sys

# Fix TCL/TK paths for Windows
_dirs_to_check = [
    os.path.dirname(sys.executable),
    os.path.join(os.path.dirname(sys.executable), "..", ".."),
    r"C:\Users\Володя\AppData\Local\Programs\Python\Python313",
]
for _base in _dirs_to_check:
    _tcl = os.path.join(_base, "tcl", "tcl8.6")
    _tk  = os.path.join(_base, "tcl", "tk8.6")
    if os.path.isdir(_tcl) and os.path.isdir(_tk):
        os.environ.setdefault("TCL_LIBRARY", _tcl)
        os.environ.setdefault("TK_LIBRARY",  _tk)
        break

from app.ui.app_window import AppWindow

if __name__ == "__main__":
    AppWindow().mainloop()
