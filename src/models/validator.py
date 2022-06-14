#!/usr/bin/env python3


# +
# import(s)
# -
from src import *
from astropy.coordinates import Angle
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy import units as u
from datetime import timedelta
from datetime import datetime

import base64
import hashlib
import logging
import logging.config
import json
import math
import os
import pytz
import re


# +
# function: ra_to_decimal()
# -
# noinspection PyBroadException
def _ra_to_decimal(_ra=''):

    # check input(s)
    if not isinstance(_ra, str) or _ra.strip() == '':
        return None

    # convert
    try:
        if 'hours' not in _ra.lower():
            _ra = f'{_ra} hours'
        return float(Angle(_ra).degree)
    except Exception:
        return None


# +
# function: ra_to_hms()
# -
# noinspection PyBroadException,PyPep8,PyUnresolvedReferences
def _ra_to_hms(ra=math.nan):
    """ return RA from decimal to H:M:S """
    try:
        _c = Angle(ra, unit=u.degree).hms
        _h, _m, _s = int(_c.h), int(_c.m), _c.s
        return f'{_h:02d}:{_m:02d}:{_s:06.3f}'
    except:
        return None


# +
# function: dec_to_decimal()
# -
# noinspection PyBroadException
def _dec_to_decimal(_dec=''):

    # check input(s)
    if not isinstance(_dec, str) or _dec.strip() == '':
        return None

    # convert
    try:
        if 'degrees' not in _dec.lower():
            _dec = f'{_dec} degrees'
        return float(Angle(_dec).degree)
    except Exception:
        return None


# +
# function: dec_to_dms()
# -
# noinspection PyBroadException,PyPep8,PyUnresolvedReferences
def _dec_to_dms(dec=math.nan):
    """ return Dec from decimal to d:m:s """
    try:
        _c = Angle(dec, unit=u.degree).signed_dms
        _d, _m, _s = int(_c.d), int(_c.m), _c.s
        _sign = '+' if _c.sign == 1.0 else '-'
        return f'{_sign}{_d:02d}:{_m:02d}:{_s:06.3f}'
    except:
        return None


def validate_ra(ra):
    valid = False
    ra_decimal = None
    ra_hms = None

    if isinstance(ra, float):
        ra_decimal = ra
        ra_hms = _ra_to_hms(ra_decimal)
    else:
        try:
            ra_decimal = float(ra)
            ra_hms = _ra_to_hms(ra_decimal)
        except:
            pass

    if isinstance(ra, str):
        r = re.compile('.{2}:.{2}:.{2}\.*')
        if r.match(ra):
            ra_hms = ra
            ra_decimal = _ra_to_decimal(ra)

    valid = all(x != None for x in [ra_decimal, ra_hms])
    return ra_decimal, ra_hms, valid


def validate_dec(dec):
    valid = False
    dec_decimal = None
    dec_dms = None

    if isinstance(dec, float):
        dec_decimal = dec
        dec_dms = _dec_to_dms(dec_decimal)
    else:
        try:
            dec_decimal = float(dec)
            dec_dms = _dec_to_dms(dec_decimal)
        except:
            pass

    if isinstance(dec, str):
        r = re.compile('.{2}:.{2}:.{2}\.*')
        isNeg = dec.startswith('-')
        if '-' in dec:
            dec = dec.split('-')[1]
        if '+' in dec:
            dec = dec.split('+')[1]
        if r.match(dec):
            dec = '-' + dec if isNeg else '+' + dec
            dec_dms = dec
            dec_decimal = _dec_to_decimal(dec)

    valid = all(x != None for x in [dec_decimal, dec_dms])
    return dec_decimal, dec_dms, valid


def validate_payload_field(payload, key, ftype, fmt=None):
    value = payload[key]
    try:
        if fmt is not None:
            try:
                retval = ftype.strptime(value, fmt)
                return retval, True, ''
            except:
                return None, False, 'Error parsing {} \'{}\'. Required format: {}'.format(ftype, key, fmt)
        else:
            retval = ftype(value)
            return retval, True, ''
    except:
        return None, False, 'Field: \'{}\'. Value: \'{}\'. Value Type: \'{}\'. Intended Type: \'{}\''.format(key, value, type(value), ftype) 


def validate_payload_field_inlist(payload, key, values):
    value = payload[key]
    if value in values:
        return True, ''
    else:
        return False, 'Field \'{}\' is invalid. Must be in \'{}\''.format(key, values)


def isvalidInstance(value, ftype, fmt=None):
    tehee=True
    try:
        if fmt is not None:
            try:
                retval = ftype.strptime(value, fmt)
                tehee = True
            except:
                tehee = False
        else:
            retval = ftype(value)
            tehee = True
    except:
        tehee = False
        
    return tehee