#!/usr/bin/env python3


# +
# import(s)
# -
from src import *

import argparse
import csv


# +
# __doc__ string
# -
__doc__ = """
  % python3 check_upload_format.py --help
"""


# +
# constant(s)
# -
TRUE_VALUES = ['true', 't', '1']
FALSE_VALUES = ['false', 'f', '0']


# +
# function: check_upload_format()
# -
def check_upload_format(_infil='', _verbose=False, _json=True):

    # check input(s)
    _file = os.path.abspath(os.path.expanduser(_infil))
    if not os.path.isfile(_file):
        raise Exception(f'Invalid argument, _file={_file}')
    if _verbose:
        print(f"Executing> upload_from_file(_file={_file}, _verbose={_verbose})")

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

    # read the file, expect columns:
    #   v1: username, telescope, instrument, object_name, ra, dec, filter, exp_time, num_exp, airmass, lunarphase,
    #   priority, photometric, guiding, non_sidereal, begin, end, binning, dither, cadence
    #   v2: username, telescope, instrument, object_name, ra, dec, filter, exp_time, num_exp, airmass, lunarphase,
    #   priority, photometric, guiding, non_sidereal, begin, end, binning, dither, cadence, non_sidereal_json
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
    _p = argparse.ArgumentParser(description=f'Read Database File', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--file', default='', help=f'input file')
    _p.add_argument(f'--verbose', default=False, action='store_true', help=f'if present, produce more verbose output')
    _p.add_argument(f'--json', default=True, action='store_true', help=f'if present, check JSON')
    args = _p.parse_args()
    check_upload_format(args.file, _verbose=bool(args.verbose), _json=bool(args.json))
