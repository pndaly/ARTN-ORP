#!/usr/bin/env python3.7


# +
# import(s)
# -
from astropy.coordinates import Angle
from astropy.coordinates import SkyCoord
from astropy.time import Time
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
# constant(s)
# -
ALPHABET_UC = {chr(_i): _i for _i in range(65, 91)}
ALPHABET_LC = {chr(_i): _i for _i in range(97, 123)}
ARTN_ALLOWED_HEADERS_V1 = ('username', 'telescope', 'instrument', 'object_name', 'ra', 'dec', 'filter', 'exp_time',
                           'num_exp', 'airmass', 'lunarphase', 'priority', 'photometric', 'guiding', 'non_sidereal',
                           'begin', 'end', 'binning', 'dither', 'cadence')
ARTN_ALLOWED_HEADERS_V2 = ('username', 'telescope', 'instrument', 'object_name', 'ra', 'dec', 'filter', 'exp_time',
                           'num_exp', 'airmass', 'lunarphase', 'priority', 'photometric', 'guiding', 'non_sidereal',
                           'begin', 'end', 'binning', 'dither', 'cadence', 'non_sidereal_json')
ARTN_BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ARTN_CHAR_8 = 8
ARTN_CHAR_16 = 16
ARTN_CHAR_24 = 24
ARTN_CHAR_32 = 32
ARTN_CHAR_64 = 64
ARTN_CHAR_128 = 128
ARTN_CHAR_256 = 256
ARTN_COMMENT_CHARS = r' #%!<>+-\/'
ARTN_DATA_DIRECTORY = '/data1/artn/rts2images/queue'
ARTN_DIR_DARKS = '/data1/artn/rts2images/YYYYMMDD/darks'
ARTN_DIR_FLATS = '/data1/artn/rts2images/queue/YYYYMMDD/C0'
ARTN_DIR_FOCUS = '/data1/artn/rts2images/queue/YYYYMMDD/C0/focus'
ARTN_DIR_OBJECTS = '/data1/artn/rts2images/queue/YYYYMMDD/C0'
ARTN_DIR_SKYFLATS = '/data1/artn/rts2images/YYYYMMDD/skyflats'
ARTN_DATE_PATTERN = "[0-9]{4}-[0-9]{2}-[0-9]{2}[ T?][0-9]{2}:[0-9]{2}:[0-9]{2}"
ARTN_DEC_PATTERN = "[+-]?[0-9]{2}:[0-9]{2}:[0-9]{2}"
ARTN_DECODE_DICT = {'.us.': '_', '.sq.': "'", '.ws.': ' ', '.bs.': '\\', '.at.': '@',
                    '.bg.': '!', '.dq.': '"', '.eq.': '='}
ARTN_ENCODE_DICT = {v: k for k, v in ARTN_DECODE_DICT.items()}
ARTN_ISO_FORMAT = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:09.6f}"
ARTN_ISO_NULL = '0000-00-00T00:00:00.000000'
ARTN_ISO_PATTERN = '[0-9]{4}-[0-9]{2}-[0-9]{2}[ T?][0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6}'
ARTN_ISO_PATTERN_2 = '[0-9]{4}-[0-9]{2}-[0-9]{2}[ T?][0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{2}'
ARTN_LOOKBACK_PERIOD = 365
ARTN_MJD_FORMAT = '{:26.20f}'
ARTN_MJD_PATTERN = '^[0-9]{5}.[0-9]{20}'
ARTN_RA_PATTERN = "[0-9]{2}:[0-9]{2}:[0-9]{2}"
ARTN_RESERVED_USERNAMES = ['darks', 'focus', 'skyflats', 'standard']
ARTN_RESULTS_PER_PAGE = 30
ARTN_SECRET_KEY = os.getenv("SECRET_KEY", "L10ngyfarch1adau")
ARTN_SUPPORTED_FILETYPES = ['csv', 'tgz', 'tsv']
ARTN_TIMEZONE = pytz.timezone('America/Phoenix')
ARTN_LOG_CLR_FORMAT = '%(log_color)s%(asctime)-20s %(levelname)-9s %(filename)-15s %(funcName)-15s ' \
                              'line:%(lineno)-5d Message: %(message)s'
ARTN_LOG_CNS_FORMAT = '%(asctime)-20s %(levelname)-9s %(filename)-15s %(funcName)-15s ' \
                              'line:%(lineno)-5d Message: %(message)s'
ARTN_LOG_FIL_FORMAT = '%(asctime)-20s %(levelname)-9s %(name)-15s %(filename)-15s %(funcName)-15s ' \
                           'line:%(lineno)-5d PID:%(process)-6d Message: %(message)s'
ARTN_MAX_BYTES = 9223372036854775807
ARTN_NODES = {
    'Bok': {
      'name': 'Bok',
      'aka': 'Bok 90-inch',
      'imperial': '90 inch',
      'metric': '2.3 metre',
      'latitude': '31.9629',
      'longitude': '-111.6004',
      'elevation': '2071.12 metres',
      'altitude': '6795 feet',
      'focal_length': '6.08 metres',
      'mount': 'equatorial',
      'imager': {
          'name': '90Prime',
          'binning': 'None, 1x1, 2x2, 3x3',
          'dither': 'None, NxM, n-RA, n-Dec',
          'filters': 'U, B, V, R, I, Clear'
      }
    },
    'Kuiper':  {
      'name': 'Kuiper',
      'aka': 'Kuiper 61-inch',
      'imperial': '61 inch',
      'metric': '1.54 metre',
      'latitude': '32.4165',
      'longitude': '-110.7345',
      'elevation': '2510.03 metres',
      'altitude': '8235 feet',
      'focal_length': '9.6 metres',
      'mount': 'equatorial',
      'imager': {
          'name': 'Mont4k',
          'binning': 'None, 1x1, 2x2, 3x3, 4x4',
          'dither': 'None, NxM, n-RA, n-Dec',
          'filters': 'U, B, V, R, I, Clear'
      }
    },
    'Vatt': {
      'name': 'Vatt',
      'aka': 'Vatt 1.8-metre',
      'imperial': '71 inch',
      'metric': '1.8 metre',
      'latitude': '32.7016',
      'longitude': '-109.8719',
      'elevation': '3190.95 metres',
      'altitude': '10469 feet',
      'focal_length': '16.48 metres',
      'mount': 'alt-az',
      'imager': {
          'name': 'Vatt4k',
          'binning': 'None, 1x1, 2x2, 3x3, 4x4',
          'dither': 'None, NxM, n-RA, n-Dec',
          'filters': 'U, B, V, R, I, Clear'
      }
    },
}

ASTROPLAN_IERS_URL = 'ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all'
ASTROPLAN_IERS_URL_ALTERNATE = 'https://datacenter.iers.org/data/9/finals2000A.all'

FALSE_VALUES = ['false', 'f', '0']
TRUE_VALUES = ['true', 't', '1']


# +
# credential(s)
# -
ARTN_DB_HOST = os.getenv("ARTN_DB_HOST", "localhost")
ARTN_DB_NAME = os.getenv("ARTN_DB_NAME", "artn")
ARTN_DB_PASS = os.getenv("ARTN_DB_PASS", "********")
ARTN_DB_PORT = os.getenv("ARTN_DB_PORT", 5432)
ARTN_DB_USER = os.getenv("ARTN_DB_USER", "artn")

ARTN_MAIL_SERVER = os.getenv('MAIL_SERVER', "smtp.googlemail.com")
ARTN_MAIL_PORT = os.getenv('MAIL_PORT', 587)
ARTN_MAIL_USE_TLS = bool(os.getenv('MAIL_USE_TLS', 1))
ARTN_MAIL_USE_SSL = bool(os.getenv('MAIL_USE_SSL', 1))
ARTN_MAIL_USERNAME = os.getenv('MAIL_USERNAME', "artn@dev.null")
ARTN_MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', "********")

ARTN_DATE_RULE = re.compile("\d{4}-\d{2}-\d{2}[ T]?\d{2}:\d{2}:\d")
ARTN_PASSWORD_RULE = re.compile("(^(?=.*?[A-Z])(?=.*[a-z])(?=.*?[0-9]).{8,}$)")


# +
# ORP env(s) - edit as required
# -
ORP_APP_HOST = os.getenv("ORP_APP_HOST", "scopenet.as.arizona.edu")
ORP_APP_PORT = os.getenv("ORP_APP_PORT", 7500)
ORP_APP_URL = f'https://{ORP_APP_HOST}/orp'
ORP_HOME = os.getenv("ORP_HOME", ".")


# +
# other env(s)
# -
PYTHONPATH = os.getenv('PYTHONPATH', '.')


# +
# class: UtilsLogger() inherits from the object class
# -
class UtilsLogger(object):

    # +
    # method: __init__
    # -
    def __init__(self, name=''):
        """
            :param name: name of logger
            :return: None or object representing the logger
        """
        # get arguments(s)
        self.name = name

        # define some variables and initialize them
        self.__msg = None
        logname = '{}'.format(self.__name)

        # noinspection PyPep8,PyBroadException
        try:
            logfile = '{}/{}.log'.format(os.getenv("ARTN_LOGS"), logname)
        except Exception:
            logfile = '{}/{}.log'.format(os.getcwd(), logname)
        logconsole = '/tmp/console-{}.log'.format(logname)

        utils_logger_dictionary = {

            # logging version
            'version': 1,

            # do not disable any existing loggers
            'disable_existing_loggers': False,

            # use the same formatter for everything
            'formatters': {
                'UtilsColoredFormatter': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': ARTN_LOG_CLR_FORMAT,
                    'log_colors': {
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'white,bg_red',
                    }
                },
                'UtilsConsoleFormatter': {
                    'format': ARTN_LOG_CNS_FORMAT
                },
                'UtilsFileFormatter': {
                    'format': ARTN_LOG_FIL_FORMAT
                }
            },

            # define file and console handlers
            'handlers': {
                'colored': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'UtilsColoredFormatter',
                    'level': 'DEBUG',
                    # 'stream': 'ext://sys.stdout'
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'UtilsConsoleFormatter',
                    'level': 'DEBUG',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'backupCount': 10,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'UtilsFileFormatter',
                    'filename': logfile,
                    'level': 'DEBUG',
                    'maxBytes': ARTN_MAX_BYTES
                },
                'utils': {
                    'backupCount': 10,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'UtilsFileFormatter',
                    'filename': logconsole,
                    'level': 'DEBUG',
                    'maxBytes': ARTN_MAX_BYTES
                }
            },

            # make this logger use file and console handlers
            'loggers': {
                logname: {
                    # 'handlers': ['colored', 'file', 'utils'],
                    'handlers': ['colored', 'file'],
                    'level': 'DEBUG',
                    'propagate': True
                }
            }
        }

        # configure logger
        logging.config.dictConfig(utils_logger_dictionary)

        # get logger
        self.logger = logging.getLogger(logname)

    # +
    # Decorator(s)
    # -
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name=''):
        self.__name = name if (isinstance(name, str) and name.strip() != '') else os.getenv('USER')


# +
# function: get_astropy_coords()
# -
# noinspection PyBroadException
def get_astropy_coords(objectname=''):
    try:
        _obj = SkyCoord.from_name(objectname)
        return _obj.ra.value, _obj.dec.value
    except Exception:
        return math.nan, math.nan


# +
# function: get_date_time()
# -
def get_date_time(days=0):
    return datetime.now() + timedelta(days=days)


# +
# function: get_date_utctime()
# -
def get_date_utctime(days=0):
    return datetime.utcnow() + timedelta(days=days)


# +
# function: get_iso()
# -
def get_iso():
    return Time.now().to_datetime(ARTN_TIMEZONE).isoformat()[:26]


# +
# function: iso_to_mjd()
# -
# noinspection PyBroadException,PyPep8
def iso_to_mjd(iso=''):
    try:
        return ARTN_MJD_FORMAT.format(Time(iso).mjd).strip()
    except Exception:
        return ARTN_MJD_FORMAT.format(-1.0).strip()


# +
# function: get_mjd()
# -
def get_mjd():
    return iso_to_mjd(get_iso())


# +
# function: mjd_to_iso()
# -
def mjd_to_iso(mjd=''):
    if not isinstance(mjd, str) or mjd.strip() == '' or not re.search(ARTN_MJD_PATTERN, mjd):
        return ARTN_ISO_NULL
    else:
        return Time(float(mjd) + 2400000.5, format='jd', precision=6).iso[:26].strip()


# +
# function: get_jd()
# -
def get_jd():
    return iso_to_jd(get_iso())


# +
# function: iso_to_jd()
# -
# noinspection PyBroadException
def iso_to_jd(_iso=''):
    try:
        return float(Time(_iso).mjd)+2400000.5
    except Exception:
        return float(math.nan)


# +
# function: jd_to_iso()
# -
# noinspection PyBroadException
def jd_to_iso(_jd=0.0):
    try:
        return Time(_jd, format='jd', precision=6).isot
    except Exception:
        return None


# +
# get_unique_hash()
# -
def get_unique_hash():
    return hashlib.sha256(get_iso().encode('utf-8')).hexdigest()


# +
# function: ra_to_deg()
# -
# noinspection PyBroadException
def ra_to_deg(_ra=''):

    # check input(s)
    if not isinstance(_ra, str) or _ra.strip() == '':
        return float('nan')

    # convert
    try:
        if 'hours' not in _ra.lower():
            _ra = '{} hours'.format(_ra)
        return float(Angle(_ra).degree)
    except Exception:
        return float('nan')


# +
# function: dec_to_deg()
# -
# noinspection PyBroadException
def dec_to_deg(_dec=''):

    # check input(s)
    if not isinstance(_dec, str) or _dec.strip() == '':
        return float('nan')

    # convert
    try:
        if 'degrees' not in _dec.lower():
            _dec = '{} degrees'.format(_dec)
        return float(Angle(_dec).degree)
    except Exception:
        return float('nan')


# +
# function: decode_verboten():
# -
def decode_verboten(_str='', decode=None):
    if decode is None:
        decode = ARTN_DECODE_DICT
    if isinstance(_str, str) and _str.strip() != '' and isinstance(decode, dict) and decode is not {}:
        for c in decode.keys():
            if c in _str:
                _str = _str.replace(c, decode[c])
    return _str


# +
# function: encode_verboten():
# -
def encode_verboten(_str='', encode=None):
    if encode is None:
        encode = ARTN_ENCODE_DICT
    if isinstance(_str, str) and _str != '' and isinstance(encode, dict) and encode is not {}:
        for c in encode.keys():
            if c in _str:
                _str = _str.replace(c, encode[c])
    return _str


# +
# dictionary(s)
# -
ARTN_JSON_SCHEMA = {
    'ObjectRate': {'min': -10.0, 'max': 10.0},
    'RA_BiasRate': {'min': -10.0, 'max': 10.0},
    'Dec_BiasRate': {'min': -10.0, 'max': 10.0},
    'PositionAngle': {'min': -360.0, 'max': 360.0},
    'UTC_At_Position': {
        'min': get_date_time(-ARTN_LOOKBACK_PERIOD).isoformat(),
        'max': get_date_time(ARTN_LOOKBACK_PERIOD).isoformat()
    }
}


# +
# function: is_json():
# -
# noinspection PyBroadException
def is_json(_json=''):
    try:
        json.loads(_json)
    except Exception:
        return False
    return True


# +
# function: check_json():
# -
def check_json(_json='', refresh=True):

    # get logger
    _json_log = UtilsLogger('JSON-Logger').logger

    # update date(s), if required
    if refresh:
        # noinspection PyTypeChecker
        ARTN_JSON_SCHEMA['UTC_At_Position']['min'] = get_date_time(-180).isoformat()
        # noinspection PyTypeChecker
        ARTN_JSON_SCHEMA['UTC_At_Position']['max'] = get_date_time(+180).isoformat()
    _json_log.debug(f"schema={ARTN_JSON_SCHEMA}")

    # convert single quotes to double quotes throughout
    _json = encode_verboten(_json, ARTN_ENCODE_DICT)
    _json = _json.replace("sq", "dq")
    _json = decode_verboten(_json, ARTN_DECODE_DICT)

    # if it's not JSON, return
    if not is_json(_json):
        _json_log.error(f"_json={_json} is not correctly formed json")
        return False
    _json_log.debug(f"_json={_json} is OK")

    # check element(s) against min, max value(s)
    _json_dict = json.loads(_json)
    _json_log.debug(f"_json_dict={_json_dict}")
    for _k in ARTN_JSON_SCHEMA:
        if _k not in _json_dict:
            _json_log.error(f"key {_k} not found")
            return False
        _val = _json_dict[_k]
        _max = ARTN_JSON_SCHEMA[_k]['max']
        _min = ARTN_JSON_SCHEMA[_k]['min']
        if isinstance(_max, float) and isinstance(_min, float):
            if not (_min <= float(_val) <= _max):
                _json_log.error(f"{_k} value {_val} not in range {_min}:{_max}")
                return False 
        elif isinstance(_max, int) and isinstance(_min, int):
            if not (_min <= int(_val) <= _max):
                _json_log.error(f"{_k} value {_val} not in range {_min}:{_max}")
                return False 
        elif isinstance(_max, str) and isinstance(_min, str):
            if re.match(ARTN_DATE_RULE, f'{_val}') is None:
                _json_log.error(f"{_k} value {_val} no match for rule {ARTN_DATE_RULE}")
                return False 
            _max_jd = float(Time(_max, format='isot').mjd)
            _min_jd = float(Time(_min, format='isot').mjd)
            _val_jd = float(Time(_val, format='isot').mjd)
            if not (_min_jd <= _val_jd <= _max_jd):
                _json_log.error(f"{_k} value {_val_jd} not in range {_min_jd}:{_max_jd}")
                return False 
        else:
            return False

    # passed all checks ok
    _json_log.debug(f"_json={_json} validated OK")
    return True


# +
# function: read_png():
# -
def read_png(_file=f'{ARTN_BASE_DIR}/static/img/ObservationExpired.png'):
    with open(os.path.abspath(os.path.expanduser(_file)), "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"


ARTN_OBSERVATION_EXPIRED = read_png()


# +
# function: get_iers():
# -
# noinspection PyBroadException
def get_iers(_url=ASTROPLAN_IERS_URL):

    # get logger
    _iers_log = UtilsLogger('IERS-Logger').logger

    try:
        # try astroplan download
        _iers_log.info("1: from astroplan import download_IERS_A")
        from astroplan import download_IERS_A
        _iers_log.info("1: download_IERS_A()")
        download_IERS_A()
    except Exception:
        # try alternate download
        _iers_log.info("2: from astroplan import download_IERS_A")
        from astroplan import download_IERS_A
        _iers_log.info("2: from astropy.utils import iers")
        from astropy.utils import iers
        _iers_log.info("2: from astropy.utils.data import clear_download_cache")
        from astropy.utils.data import clear_download_cache
        _iers_log.info("2: clear_download_cache()")
        clear_download_cache()
        _iers_log.info(f"2: iers.IERS_A_URL = {_url}")
        iers.IERS_A_URL = f'{_url}'
        _iers_log.info("2: download_IERS_A()")
        download_IERS_A()
