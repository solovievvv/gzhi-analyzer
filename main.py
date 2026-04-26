import os
import sys

# Фикс путей TCL/TK для Windows (когда Python установлен без них в PATH)
_python_dir = os.path.dirname(sys.executable)
_tcl_dir = os.path.join(_python_dir, "tcl")
if os.path.isdir(_tcl_dir):
    os.environ.setdefault("TCL_LIBRARY", os.path.join(_tcl_dir, "tcl8.6"))
    os.environ.setdefault("TK_LIBRARY", os.path.join(_tcl_dir, "tk8.6"))

from app.ui.app_window import AppWindow

if __name__ == "__main__":
    AppWindow().mainloop()
