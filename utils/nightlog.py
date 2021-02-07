#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.io import fits
from datetime import datetime
from datetime import timedelta

import argparse
import itertools
import os
import re


# +
# constant(s)
# -
ARTN_DATA_DIR = '/rts2data'
ARTN_FITS_HEADERS = ['AIRMASS', 'ARTNGID', 'ARTNOID', 'AZIMUTH', 'BINNING', 'CAMTEMP', 'DATE-OBS', 'DEC',
                     'DETSIZE', 'DEWTEMP', 'ELEVAT', 'EPOCH', 'EXPTIME', 'FILTER', 'FOCUS', 'IMAGETYP', 'INSTRUME',
                     'JULIAN', 'OBJECT', 'RA', 'ROTANGLE', 'TIME-OBS']
ARTN_HEADER = "File                       | Obseravation Date       |  Object     | RA          | Dec         | Epoch  | Filter     | ExpTime | Observation  | Airmass | Az    | El    | RotAng | TelFoc | Instrument | Bin | Camera   | Dewar    | DetSize   | Size     | Owner   "
ARTN_OBSERVATIONS = ['all', 'bias', 'calibration', 'dark', 'flat', 'focus', 'object', 'skyflat', 'standard']
ARTN_UNITS = "                           | (UT)                    |  Type       | (HH:MM:SS)  | (\u00b1dd:mm:ss) |        |            | (s)     | Type         | (secZ)  | (\u00b0)   | (\u00b0)   | (\u00b0)    |        |            |     | (\u00b0C)     | (\u00b0C)     |           | (Bytes)  |         "

FORMAT_HRULE = f'-'*260


# +
# supported system(s)
# -
ARTN_NODES = {'Bok': ['BCSpec', '90Prime'], 'Kuiper': ['Mont4k'], 'MMT': ['BinoSpec'], 'Vatt': ['Vatt4k']}
ARTN_TELESCOPES = [_k for _k in ARTN_NODES]
ARTN_INSTRUMENTS = list(itertools.chain.from_iterable([_v for _k, _v in ARTN_NODES.items()]))


# +
# function: nlog_get_date_time()
# -
# noinspection PyBroadException
def nlog_get_date_time(days=0):
    try:
        return (datetime.now() + timedelta(days=days)).isoformat()
    except Exception:
        return None


# +
# function: nlog_seek_files()
# -
# noinspection PyBroadException
def nlog_seek_files(_path=os.getcwd()):

    # get input(s)
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))

    # generator code
    _fw = (
        os.path.join(_root, _file)
        for _root, _dirs, _files in os.walk(_path)
        for _file in _files
    )

    # get file(s)
    try:
        return {f'{_k}': int(os.stat(f'{_k}').st_size)
                for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                  _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2)}
    except Exception:
        return {}


# +
# function: nlog_get_fits_headers()
# -
# noinspection PyBroadException,PyUnresolvedReferences
def nlog_get_fits_headers(_in=None):

    # check input(s)
    if _in is None or not isinstance(_in, dict) or _in is {}:
        return []

    # get fits data
    _l_out = []
    for _k, _v in _in.items():
        _d_out = {'file': os.path.basename(_k), 'directory': os.path.dirname(_k), 'size': _v}
        with fits.open(_k) as _hdul:
            for _h in ARTN_FITS_HEADERS:
                try:
                    _d_out[_h.replace('-', '')] = str(_hdul[0].header[_h]).strip()
                except Exception:
                    _d_out[_h] = ''

        # who requested it?
        try:
            if _d_out['ARTNGID'].strip() != '' and _d_out['ARTNOID'].strip() != '':
                # noinspection PyUnresolvedReferences
                query = db.session.query(ObsReq)
                query = obsreq_filters(query, {'group_id': f"{_d_out['ARTNGID']}"})
                query = obsreq_filters(query, {'observation_id': f"{_d_out['ARTNOID']}"})
                _d_out['OWNER'] = query.first().username
            else:
                _d_out['OWNER'] = ''
        except Exception:
            _d_out['OWNER'] = ''

        # append new record
        _l_out.append(_d_out)

    # return list sorted by Julian date key
    return sorted(_l_out, key=lambda _i: _i['JULIAN'])


# +
# function: nlog_print_data()
# -
def nlog_print_data(_header='', _data=None):
    if _data is not None:
        if _header.strip() != '':
            print(f"+{FORMAT_HRULE:^260}+\n|{_header:^260}|\n+{FORMAT_HRULE:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{FORMAT_HRULE:^260}+")
        for _e in _data:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        if _header.strip() != '':
            print(f"+{FORMAT_HRULE:^260}+")


# +
# default(s)
# -
DEFAULT_ISO = nlog_get_date_time().split('T')[0].replace('-', '').strip()
DEFAULT_OBSERVATION = 'all'
DEFAULT_TELESCOPE = 'Kuiper'
DEFAULT_INSTRUMENT = 'Mont4k'


# +
# function: nightlog()
# -
# noinspection PyBroadException,PyPep8Naming
def nightlog(_instrument=DEFAULT_INSTRUMENT, _iso=DEFAULT_ISO, _observation=DEFAULT_OBSERVATION, _telescope=DEFAULT_TELESCOPE):

    # get input(s)
    _instrument = _instrument if (_instrument in [_l for _l in ARTN_NODES[_telescope]]) else DEFAULT_INSTRUMENT
    _iso = _iso if (re.match('^(\d{8})$', _iso) is not None) else DEFAULT_ISO
    _observation = _observation if (_observation in [_l for _l in ARTN_OBSERVATIONS]) else DEFAULT_OBSERVATION
    _telescope = _telescope if (_telescope in [_l for _l in ARTN_TELESCOPES]) else DEFAULT_TELESCOPE

    # set default(s)
    _d_bias, _d_calibration, _d_dark, _d_flat, _d_focus, _d_object, _d_skyflat, _d_standard = '', '', '', '', '', '', '', ''
    _f_bias, _f_calibration, _f_dark, _f_flat, _f_focus, _f_object, _f_skyflat, _f_standard = {}, {}, {}, {}, {}, {}, {}, {}
    _h_bias, _h_calibration, _h_dark, _h_flat, _h_focus, _h_object, _h_skyflat, _h_standard = [], [], [], [], [], [], [], []
    _n_bias, _n_calibration, _n_dark, _n_flat, _n_focus, _n_object, _n_skyflat, _n_standard = 0, 0, 0, 0, 0, 0, 0, 0
    _s_bias, _s_calibration, _s_dark, _s_flat, _s_focus, _s_object, _s_skyflat, _s_standard = '', '', '', '', '', '', '', ''
    _f_all, _n_all = {}, 0

    # scrape data
    if _observation == 'all' or _observation == 'bias':
        _d_bias = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/bias"
        _f_bias = nlog_seek_files(_d_bias)
        _h_bias = nlog_get_fits_headers(_f_bias)
        _n_bias = len(_f_bias)
        _s_bias = f"{len(_f_bias)} BIAS observations on server scopenet.as.arizona.edu in directory {_d_bias}"
    if _observation == 'all' or _observation == 'calibration':
        _d_calibration = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/calibration"
        _f_calibration = nlog_seek_files(_d_calibration)
        _h_calibration = nlog_get_fits_headers(_f_calibration)
        _n_calibration = len(_f_calibration)
        _s_calibration = f"{len(_f_calibration)} CALIBRATION observations on server scopenet.as.arizona.edu in directory {_d_calibration}"
    if _observation == 'all' or _observation == 'dark':
        _d_dark = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/dark"
        _f_dark = nlog_seek_files(_d_dark)
        _h_dark = nlog_get_fits_headers(_f_dark)
        _n_dark = len(_f_dark)
        _s_dark = f"{len(_f_dark)} DARK observations on server scopenet.as.arizona.edu in directory {_d_dark}"
    if _observation == 'all' or _observation == 'flat':
        _d_flat = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/flat"
        _f_flat = nlog_seek_files(_d_flat)
        _h_flat = nlog_get_fits_headers(_f_flat)
        _n_flat = len(_f_flat)
        _s_flat = f"{len(_f_flat)} FLAT observations on server scopenet.as.arizona.edu in directory {_d_flat}"
    if _observation == 'all' or _observation == 'focus':
        _d_focus = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/focus"
        _f_focus = nlog_seek_files(_d_focus)
        _h_focus = nlog_get_fits_headers(_f_focus)
        _n_focus = len(_f_focus)
        _s_focus = f"{len(_f_focus)} FOCUS observations on server scopenet.as.arizona.edu in directory {_d_focus}"
    if _observation == 'all' or _observation == 'object':
        _d_object = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/object"
        _f_object = nlog_seek_files(_d_object)
        _h_object = nlog_get_fits_headers(_f_object)
        _n_object = len(_f_object)
        _s_object = f"{len(_f_object)} OBJECT observations on server scopenet.as.arizona.edu in directory {_d_object}"
    if _observation == 'all' or _observation == 'skyflat':
        _d_skyflat = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/skyflat"
        _f_skyflat = nlog_seek_files(_d_skyflat)
        _h_skyflat = nlog_get_fits_headers(_f_skyflat)
        _n_skyflat = len(_f_skyflat)
        _s_skyflat = f"{len(_f_skyflat)} SKYFLAT observations on server scopenet.as.arizona.edu in directory {_d_skyflat}"
    if _observation == 'all' or _observation == 'standard':
        _d_standard = f"{ARTN_DATA_DIR}/{_telescope}/{_instrument}/{_iso}/standard"
        _f_standard = nlog_seek_files(_d_standard)
        _h_standard = nlog_get_fits_headers(_f_standard)
        _n_standard = len(_f_standard)
        _s_standard = f"{len(_f_standard)} STANDARD observations on server scopenet.as.arizona.edu in directory {_d_standard}"

    # amalgamate
    _f_all = {**_f_bias, **_f_calibration, **_f_dark, **_f_flat, **_f_focus, **_f_object, **_f_skyflat, **_f_standard}
    _n_all = len(_f_all)

    # print header
    FORMAT_TITLE = f"{_telescope.upper()} TELESCOPE OBSERVATION LOG"
    # noinspection PyPep8Naming
    FORMAT_SUBTITLE = f"\u24B6\u205f {_iso} \u24c7\u205f ARTN Operator \u24c9\u205f {_n_all} Observations \u24c3"
    print(f"+{FORMAT_HRULE:^260}+\n|{FORMAT_TITLE:^260}|\n|{FORMAT_HRULE:^260}|\n|{FORMAT_SUBTITLE:^260}|")

    # print section(s)
    if (_observation == 'all' or _observation == 'bias') and _h_bias:
        nlog_print_data(_s_bias, _h_bias)
    if (_observation == 'all' or _observation == 'calibration') and _h_calibration:
        nlog_print_data(_s_calibration, _h_calibration)
    if (_observation == 'all' or _observation == 'dark') and _h_dark:
        nlog_print_data(_s_dark, _h_dark)
    if (_observation == 'all' or _observation == 'flat') and _h_flat:
        nlog_print_data(_s_flat, _h_flat)
    if (_observation == 'all' or _observation == 'focus') and _h_focus:
        nlog_print_data(_s_focus, _h_focus)
    if (_observation == 'all' or _observation == 'object') and _h_object:
        nlog_print_data(_s_object, _h_object)
    if (_observation == 'all' or _observation == 'skyflat') and _h_skyflat:
        nlog_print_data(_s_skyflat, _h_skyflat)
    if (_observation == 'all' or _observation == 'standard') and _h_standard:
        nlog_print_data(_s_standard, _h_standard)


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Generate Night Log', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--iso', default=DEFAULT_ISO, help="""Date, default=%(default)s""")
    _p.add_argument(f'--instrument', default=f'{DEFAULT_INSTRUMENT}',
                    help=f"""Instrument, defaults to '%(default)s'\nchoose from: {ARTN_INSTRUMENTS}""")
    _p.add_argument(f'--observation', default=DEFAULT_OBSERVATION, 
                    help=f"""Observation, default='%(default)s'\nchoose from: {ARTN_OBSERVATIONS}""")
    _p.add_argument(f'--telescope', default=f'{DEFAULT_TELESCOPE}',
                    help=f"""Telescope, defaults to '%(default)s'\nchoose from: {ARTN_TELESCOPES}""")
    args = _p.parse_args()
    nightlog(_instrument=args.instrument, _iso=args.iso, _observation=args.observation, _telescope=args.telescope)
