# PythonAnywhere WSGI configuration for SpendWise.
#
# On PythonAnywhere: Web tab -> "WSGI configuration file" link -> replace the
# ENTIRE contents of that file with the code below, then edit USERNAME and the
# SECRET_KEY value. Click "Reload" when done.

import os
import sys

# 1. Point Python at your uploaded project folder (must contain app.py).
project_home = "/home/USERNAME/spendwise"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 2. Set a long random secret (generate with:
#    python -c "import secrets; print(secrets.token_urlsafe(48))")
os.environ["SECRET_KEY"] = "PASTE-YOUR-LONG-RANDOM-SECRET-KEY-HERE"

# 3. PythonAnywhere looks for a variable named `application`.
from app import app as application
