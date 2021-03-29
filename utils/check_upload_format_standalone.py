#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.time import Time
from datetime import datetime
from datetime import timedelta

import argparse
import csv
import json
import os
import re


# +
# __doc__ string
# -
__doc__ = """

  % python3 check_upload_format_standalone.py --help

"""


# +
# constant(s)
# -
ARTN_ALLOWED_HEADERS_V1 = ('username', 'telescope', 'instrument', 'object_name', 'ra', 'dec', 'filter', 'exp_time',
                           'num_exp', 'airmass', 'lunarphase', 'priority', 'photometric', 'guiding', 'non_sidereal',
                           'begin', 'end', 'binning', 'dither', 'cadence')
ARTN_ALLOWED_HEADERS_V2 = ('username', 'telescope', 'instrument', 'object_name', 'ra', 'dec', 'filter', 'exp_time',
                           'num_exp', 'airmass', 'lunarphase', 'priority', 'photometric', 'guiding', 'non_sidereal',
                           'begin', 'end', 'binning', 'dither', 'cadence', 'non_sidereal_json')
ARTN_DATE_RULE = re.compile("\d{4}-\d{2}-\d{2}[ T]?\d{2}:\d{2}:\d")
ARTN_DECODE_DICT = {
    '.us.': '_', '.sq.': "'", '.ws.': ' ', '.bs.': '\\', '.at.': '@', '.bg.': '!', '.dq.': '"', '.eq.': '='
}
ARTN_ENCODE_DICT = {v: k for k, v in ARTN_DECODE_DICT.items()}
FALSE_VALUES = ['false', 'f', '0']
TRUE_VALUES = ['true', 't', '1']


# +
# dictionary(s)
# -
def get_date_time(days=0):
    return datetime.now() + timedelta(days=days)


ARTN_JSON_SCHEMA = {
    'ObjectRate': {'min': -10.0, 'max': 10.0},
    'RA_BiasRate': {'min': -10.0, 'max': 10.0},
    'Dec_BiasRate': {'min': -10.0, 'max': 10.0},
    'PositionAngle': {'min': -360.0, 'max': 360.0},
    'UTC_At_Position': {'min': get_date_time(-365).isoformat(), 'max': get_date_time(365).isoformat()} 
}


# +
# function(s)
# -
def decode_verboten(_str='', decode=None):
    if isinstance(_str, str) and _str.strip() != '' and isinstance(decode, dict) and decode is not {}:
        for c in decode.keys():
            if c in _str:
                _str = _str.replace(c, decode[c])
    return _str


def encode_verboten(_str='', encode=None):
    if isinstance(_str, str) and _str != '' and isinstance(encode, dict) and encode is not {}:
        for c in encode.keys():
            if c in _str:
                _str = _str.replace(c, encode[c])
    return _str


def is_json(_json=''):
    # noinspection PyBroadException
    try:
        json.loads(_json)
    except Exception:
        return False
    return True


def check_json(_json='', refresh=True):

    # update date(s), if required
    if refresh:
        # noinspection PyTypeChecker
        ARTN_JSON_SCHEMA['UTC_At_Position']['min'] = get_date_time(-180).isoformat()
        # noinspection PyTypeChecker
        ARTN_JSON_SCHEMA['UTC_At_Position']['max'] = get_date_time(+180).isoformat()

    # convert single quotes to double quotes throughout
    _json = encode_verboten(_json, ARTN_ENCODE_DICT)
    _json = _json.replace("sq", "dq")
    _json = decode_verboten(_json, ARTN_DECODE_DICT)

    # if it's not JSON, return
    if not is_json(_json):
        print(f"ERROR: _json={_json} is not correctly formed json")
        return False

    # check element(s) against min, max value(s)
    _json_dict = json.loads(_json)
    for _k in ARTN_JSON_SCHEMA:
        if _k not in _json_dict:
            print(f"ERROR: key {_k} not found")
            return False
        _val = _json_dict[_k]
        _max = ARTN_JSON_SCHEMA[_k]['max']
        _min = ARTN_JSON_SCHEMA[_k]['min']
        if isinstance(_max, float) and isinstance(_min, float):
            if not (_min <= float(_val) <= _max):
                print(f"ERROR: {_k} value {_val} not in range {_min}:{_max}")
                return False 
        elif isinstance(_max, int) and isinstance(_min, int):
            if not (_min <= int(_val) <= _max):
                print(f"ERROR: {_k} value {_val} not in range {_min}:{_max}")
                return False 
        elif isinstance(_max, str) and isinstance(_min, str):
            if re.match(ARTN_DATE_RULE, f'{_val}') is None:
                print(f"ERROR: {_k} value {_val} no match for rule {ARTN_DATE_RULE}")
                return False 
            _max_jd = float(Time(_max, format='isot').mjd)
            _min_jd = float(Time(_min, format='isot').mjd)
            _val_jd = float(Time(_val, format='isot').mjd)
            if not (_min_jd <= _val_jd <= _max_jd):
                print(f"ERROR: {_k} value {_val_jd} not in range {_min_jd}:{_max_jd}")
                return False 
        else:
            return False

    # passed all checks ok
    return True


# +
# function: check_upload_format()
# -
def check_upload_format(_infil='', _verbose=False, _json=True):

    # check input(s)
    if _infil == '':
        raise Exception(f'Invalid argument, infil={_infil}')
    if _verbose:
        print(f"Executing> upload_from_file(_infil={_infil}, _verbose={_verbose})")

    # does infil file exist?
    _file = os.path.abspath(os.path.expanduser(_infil))
    if not os.path.isfile(_file):
        raise Exception(f'File not found, _file={_file}')
    if _verbose:
        print(f"Found _file={_file}")

    # get number of lines in file
    _num = 0
    with open(_file, 'r') as _fd:
        _num = sum(1 for _l in _fd if (_l.strip() != '' and _l.strip()[0] not in r'#%!<>+\/'))
    if _verbose:
        print(f"File {_file} has {_num} non-comment entries")

    # check file type is supported
    _delimiter = ''
    if _file.lower().endswith('csv'):
        _delimiter = ','
        if _verbose:
            print(f"File {_file} has {_num} non-comment entries in CSV format")
    elif _file.lower().endswith('tsv'):
        _delimiter = '\t'
        if _verbose:
            print(f"File {_file} has {_num} non-comment entries in TSV format")
    else:
        raise Exception(f'Unsupported file type (not .csv, .tsv)')

    # read the file
    _columns = {}
    with open(_file, 'r') as _fd:
        _r = csv.reader(_fd, delimiter=_delimiter)
        _headers = next(_r, None)
        # separate header line into column headings
        for _h in _headers:
            _columns[_h] = []
        # read rest of file into lists associated with each column heading
        for _row in _r:
            # ignore comment rows
            if _row[0][0] != '' and _row[0][0] in r'#%!<>+\/':
                continue
            # load valid rows
            for _h, _v in zip(_headers, _row):
                _columns[_h].append(_v.strip())

    # sanity check
    if len(_columns)*_num != sum([len(_v) for _v in _columns.values()]):
        raise Exception(f'Irregular number of elements in {_file}, please check {_file}')
    if _verbose:
        print(f"File {_file} has passed the sanity check")

    # change the dictionary keys to remove unwanted characters
    for _k in list(_columns.keys()):
        _columns[_k.translate({ord(i): None for i in ' !@#$'})] = _columns.pop(_k)

    # check we got all the allowed headers
    if all(_k in _columns for _k in ARTN_ALLOWED_HEADERS_V2):
        if _verbose:
            print(f"File {_file} supports V2 format (non-sidereal enabled)")
    elif all(_k in _columns for _k in ARTN_ALLOWED_HEADERS_V1):
        if _verbose:
            print(f"File {_file} supports V1 format (non-sidereal disabled)")
    else:
        raise Exception(f'Failed to get all allowed headers, please check {_file}')
    print(f"File {_file} passed header checks OK")

    # check the json
    if _json and 'non_sidereal_json' in _columns:
        _nsj = _columns['non_sidereal_json']
        for _e in _nsj:
            _e = _e.replace("'", "")
            if _verbose:
                print(f"Checking {_e}")
            if "{}" in _e:
                continue
            else:
                if not check_json(f"{_e}",  False):
                    print(f"ERROR: there is an error on JSON string:\n{_e}")
                else:
                    print(f"File {_file} passed JSON checks OK")


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Check CSV/TSV File Format',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--file', default='', help=f'input file')
    _p.add_argument(f'--verbose', default=False, action='store_true', help=f'if present, produce more verbose output')
    _p.add_argument(f'--json', default=True, action='store_true', help=f'if present, check JSON')
    args = _p.parse_args()
    check_upload_format(args.file, _verbose=bool(args.verbose), _json=bool(args.json))
