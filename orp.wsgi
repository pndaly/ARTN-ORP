#!/usr/bin/env python3.7


# +
# import(s)
# -
import os
import hashlib
import sys


# +
# code base
# -
BASE = "/var/www/ARTN-ORP"
RTS2 = "/var/www/ARTN-ORP/src/rts2solib"
KEY = hashlib.sha256(BASE.encode('utf-8')).hexdigest()


# +
# path(s)
# -
os.environ["ARTN_LOGS"] = f'{BASE}/logs'
os.environ["PYTHONPATH"] = f'{RTS2}:{BASE}:{BASE}/src'
os.environ["RTS2SOLIBPATH"] = f'{BASE}/src/telescopes'
os.environ["RTS2SOLIBSRC"] = f'{RTS2}'
sys.path.insert(0, f'{BASE}')
sys.path.append(f'{BASE}/src')


# +
# start
# -
from src.orp import app as application
application.secret_key = KEY
