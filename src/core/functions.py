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
