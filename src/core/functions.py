# src/core/functions.py

import sys
import pickle
import builtins
import types
from datetime import timedelta, time

from core.Responses import *
from core.database.Database import Database, DBError, DBConnectionError
from Log import log
from BasicFunctions import now, today
from Query import Query
from Embeddeb_OpenOrange import *

# variable globales
messages_queue = {}
modules_index = None
__langdict = None

# Guardamos el import orginal
__standart_import__ = builtins.__import__

# Hack de importción dinámica (modernizado)
def __redefined_import__(name, globals=None, locals=None, fromlist=None, level=0):
    if modules_index and name in modules_index:
        try:
            return __standart_import__(modules_index[name][-1], globals, locals, fromlist, level)
        except Exception:
            return __standart_import__(name, globals, locals, fromlist, level)
    return __standart_import__(name, globals, locals, fromlist, level)

# Reemplazamos el import de Python

    