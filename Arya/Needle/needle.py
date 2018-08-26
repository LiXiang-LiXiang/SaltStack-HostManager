
import sys,os
from .core import main

if __name__ == "__main__":
    BASEDIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(BASEDIR)
    main.CommandManagement(sys.argv)
