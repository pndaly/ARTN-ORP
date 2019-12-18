#!/usr/bin/env python3.7


# +
# import(s)
# -
from src import *
from flask import flash


# +
# variable(s)
# -
TEL_LOG = UtilsLogger('Tel-Logger').logger


# +
# function: tel_log()
# -
def tel_log(_text='', _logger_msg=True, _flash_msg=True):
    if _logger_msg:
        TEL_LOG.debug(_text)
    if _flash_msg:
        flash(_text)
