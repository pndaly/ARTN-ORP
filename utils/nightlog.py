#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.io import fits
from datetime import datetime
from datetime import timedelta

import argparse
import os
import random
import re
import sys


# +
# constant(s)
# -
ARTN_FITS_HEADERS = ['AIRMASS', 'ARTNGID', 'ARTNOID', 'AZIMUTH', 'BINNING', 'CAMTEMP', 'DATE-OBS', 'DEC',
                     'DETSIZE', 'DEWTEMP', 'ELEVAT', 'EPOCH', 'EXPTIME', 'FILTER', 'FOCUS', 'IMAGETYP', 'INSTRUME',
                     'JULIAN', 'OBJECT', 'RA', 'ROTANGLE', 'TIME-OBS']
ARTN_NODES = {'Bok': ['BCSpec', '90Prime'], 'Kuiper': ['Mont4k'], 'Vatt': ['Vatt4k']}
ARTN_OBSERVATIONS = ['all', 'bias', 'calibration', 'dark', 'flat', 'focus', 'object', 'standard', 'skyflat', 'test']
ARTN_TELESCOPES = [_k for _k in ARTN_NODES]
ARTN_INSTRUMENTS = [_k for _k in ARTN_NODES.items()]


# +
# (global) variable(s)
# -
ARTN_DIR_BIAS = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/bias'
ARTN_DIR_CALIBRATION = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/calibration'
ARTN_DIR_DARK = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/dark'
ARTN_DIR_FLAT = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/flat'
ARTN_DIR_FOCUS = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/focus'
ARTN_DIR_OBJECT = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/object'
ARTN_DIR_SKYFLAT = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/skyflat'
ARTN_DIR_STANDARD = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/standard'
ARTN_DIR_TEST = '/rts2data/<TELESCOPE>/<INSTRUMENT>/<YYYYMMDD>/test'
ARTN_HEADER = "File                       | Obseravation Date       |  Object     | RA          | Dec         | Epoch  | Filter     | ExpTime | Observation  | Airmass | Az    | El    | RotAng | TelFoc | Instrument | Bin | Camera   | Dewar    | DetSize   | Size     | Owner   "
ARTN_UNITS  = "                           | (UT)                    |  Type       | (HH:MM:SS)  | (\u00b1dd:mm:ss) |        |            | (s)     | Type         | (secZ)  | (\u00b0)   | (\u00b0)   | (\u00b0)    |        |            |     | (\u00b0C)     | (\u00b0C)     |           | (Bytes)  |         "

# temporary over-rides
ARTN_DIR_DARK = '/data1/artn/rts2images/<YYYYMMDD>/darks'
ARTN_DIR_SKYFLAT = '/data1/artn/rts2images/<YYYYMMDD>/skyflats'



# +
# function: get_date_time()
# -
def get_date_time(days=0):
    return (datetime.now() + timedelta(days=days)).isoformat()


# +
# function: seek_files()
# -
# noinspection PyBroadException
def seek_files(_path=os.getcwd()):

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
# function: get_fits_headers()
# -
# noinspection PyBroadException
def get_fits_headers(_in=None):

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
# default(s)
# -
DEFAULT_DATE = get_date_time().split('T')[0].replace('-', '').strip()
DEFAULT_OBSERVATION = random.choice(ARTN_OBSERVATIONS)
DEFAULT_TELESCOPE = random.choice(ARTN_TELESCOPES)
DEFAULT_INSTRUMENT = random.choice(ARTN_NODES[DEFAULT_TELESCOPE])


# +
# function: nightlog()
# -
# noinspection PyBroadException
def nightlog(_date=DEFAULT_DATE, _telescope=DEFAULT_TELESCOPE, _instrument=DEFAULT_INSTRUMENT, _observation_type=DEFAULT_OBSERVATION):

    # get input(s)
    _date = _date if (re.match('^(\d{8})$', _date) is not None) else DEFAULT_DATE
    _telescope = _telescope if (_telescope in [_l for _l in ARTN_TELESCOPES]) else DEFAULT_TELESCOPE
    _instrument = _instrument if (_instrument in [_l for _l in ARTN_NODES[_telescope]]) else DEFAULT_INSTRUMENT
    _observation_type = _observation_type if (_observation_type in [_l for _l in ARTN_OBSERVATIONS]) else DEFAULT_OBSERVATION

    # set default(s)
    _d_bias, _d_calibration, _d_dark, _d_flat, _d_focus, _d_object, _d_skyflat, _d_standard, _d_test= '', '', '', '', '', '', '', '', ''
    _f_bias, _f_calibration, _f_dark, _f_flat, _f_focus, _f_object, _f_skyflat, _f_standard, _f_test= {}, {}, {}, {}, {}, {}, {}, {}, {}
    _h_bias, _h_calibration, _h_dark, _h_flat, _h_focus, _h_object, _h_skyflat, _h_standard, _h_test= [], [], [], [], [], [], [], [], []
    _f_all, _num_obs = {}, 0

    # get directory(s)
    _d_bias = ARTN_DIR_BIAS.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_calibration = ARTN_DIR_CALIBRATION.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_dark = ARTN_DIR_DARK.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_flat = ARTN_DIR_FLAT.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_focus = ARTN_DIR_FOCUS.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_object = ARTN_DIR_OBJECT.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_skyflat = ARTN_DIR_SKYFLAT.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_standard = ARTN_DIR_STANDARD.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)
    _d_test = ARTN_DIR_TEST.replace("<TELESCOPE>", _telescope).replace("<INSTRUMENT>", _instrument).replace("<YYYYMMDD>", _date)

    # get file(s)
    if _observation_type == 'all' or _observation_type ==  'bias':
        _f_bias = seek_files(_d_bias)
        _num_obs = len(_f_bias)
    if _observation_type == 'all' or _observation_type ==  'calibration':
        _f_calibration = seek_files(_d_calibration)
        _num_obs = len(_f_calibration)
    if _observation_type == 'all' or _observation_type ==  'dark':
        _f_dark = seek_files(_d_dark)
        _num_obs = len(_f_dark)
    if _observation_type == 'all' or _observation_type ==  'flat':
        _f_flat = seek_files(_d_flat)
        _num_obs = len(_f_flat)
    if _observation_type == 'all' or _observation_type ==  'focus':
        _f_focus = seek_files(_d_focus)
        _num_obs = len(_f_focus)
    if _observation_type == 'all' or _observation_type ==  'object':
        _f_object = seek_files(_d_object)
        _num_obs = len(_f_object)
    if _observation_type == 'all' or _observation_type ==  'skyflat':
        _f_skyflat = seek_files(_d_skyflat)
        _num_obs = len(_f_skyflat)
    if _observation_type == 'all' or _observation_type ==  'standard':
        _f_standard = seek_files(_d_standard)
        _num_obs = len(_f_standard)
    if _observation_type == 'all' or _observation_type ==  'test':
        _f_test = seek_files(_d_test)
        _num_obs = len(_f_test)

    # adjust for all
    if _observation_type == 'all':
        _f_all = {**_f_bias, **_f_calibration, **_f_dark, **_f_flat, **_f_focus, **_f_object, **_f_skyflat, **_f_standard, **_f_test}
        _num_obs = len(_f_all)

    # get fits header(s)
    if _observation_type == 'all' or _observation_type ==  'bias':
        _h_bias = get_fits_headers(_f_bias)
    if _observation_type == 'all' or _observation_type ==  'calibration':
        _h_calibration = get_fits_headers(_f_calibration)
    if _observation_type == 'all' or _observation_type ==  'dark':
        _h_dark = get_fits_headers(_f_dark)
    if _observation_type == 'all' or _observation_type ==  'flat':
        _h_flat = get_fits_headers(_f_flat)
    if _observation_type == 'all' or _observation_type ==  'focus':
        _h_focus = get_fits_headers(_f_focus)
    if _observation_type == 'all' or _observation_type ==  'object':
        _h_object = get_fits_headers(_f_object)
    if _observation_type == 'all' or _observation_type ==  'skyflat':
        _h_skyflat = get_fits_headers(_f_skyflat)
    if _observation_type == 'all' or _observation_type ==  'standard':
        _h_standard = get_fits_headers(_f_standard)
    if _observation_type == 'all' or _observation_type ==  'test':
        _h_test = get_fits_headers(_f_test)

    # print header
    _hrule = f'-'*260
    _title = f"{_telescope.upper()} TELESCOPE OBSERVATION LOG"
    _sub_title = f"\u24B6\u205f {_date} \u24c7\u205f ARTN Operator \u24c9\u205f {_num_obs} Observations \u24c3"
    print(f"+{_hrule:^260}+\n|{_title:^260}|\n|{_hrule:^260}|\n|{_sub_title:^260}|")

    # print section(s)
    if _observation_type == 'all' or _observation_type ==  'bias':
        _hdr = f"{len(_f_bias)} BIAS observations on server scopenet.as.arizona.edu in directory {_d_bias}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_bias:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'calibration':
        _hdr = f"{len(_f_calibration)} CALIBRATION observations on server scopenet.as.arizona.edu in directory {_d_calibration}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_calibration:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'dark':
        _hdr = f"{len(_f_dark)} DARK observations on server scopenet.as.arizona.edu in directory {_d_dark}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_dark:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'flat':
        _hdr = f"{len(_f_flat)} FLAT observations on server scopenet.as.arizona.edu in directory {_d_flat}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_flat:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'focus':
        _hdr = f"{len(_f_focus)} FOCUS observations on server scopenet.as.arizona.edu in directory {_d_focus}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_focus:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'object':
        _hdr = f"{len(_f_object)} OBJECT observations on server scopenet.as.arizona.edu in directory {_d_object}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_object:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'skyflat':
        _hdr = f"{len(_f_skyflat)} SKYFLAT observations on server scopenet.as.arizona.edu in directory {_d_skyflat}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_skyflat:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'standard':
        _hdr = f"{len(_f_standard)} STANDARD observations on server scopenet.as.arizona.edu in directory {_d_standard}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_standard:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")

    if _observation_type == 'all' or _observation_type ==  'test':
        _hdr = f"{len(_f_test)} TEST observations on server scopenet.as.arizona.edu in directory {_d_test}"
        print(f"+{_hrule:^260}+\n|{_hdr:^260}|\n+{_hrule:^260}+\n|{ARTN_HEADER:^259}|\n|{ARTN_UNITS:^259}|\n+{_hrule:^260}+")
        for _e in _h_test:
            print(f"|{_e['file']:<25} | {_e['DATEOBS']:>10}T{_e['TIMEOBS']:<12} | {_e['OBJECT']:^11} | {_e['RA']:^11} | {_e['DEC']:^11} | {_e['EPOCH']:^6} | {_e['FILTER']:^10} | {_e['EXPTIME']:^7} | {_e['IMAGETYP']:^12} | {_e['AIRMASS']:>7} | {_e['AZIMUTH']:^5} | {_e['ELEVAT']:^5} | {_e['ROTANGLE']:^6} | {_e['FOCUS']:>6} | {_e['INSTRUME']:^10} | {_e['BINNING']:^3} | {_e['CAMTEMP']:^8} | {_e['DEWTEMP']:^8} | {_e['DETSIZE'].replace('[','').replace(']','').replace('1:','').replace(',','x'):^9} | {_e['size']:^8} | {_e['OWNER']:^8}|")
        print(f"+{_hrule:^260}+")


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Generate Night Log', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--date', default=DEFAULT_DATE, help="""Date, default=%(default)s""")
    _p.add_argument(f'--instrument', default=DEFAULT_INSTRUMENT, help="""Instrument, default='%(default)s'""")
    _p.add_argument(f'--observation-type', default=DEFAULT_OBSERVATION, help="""Observation type, default='%(default)s'""")
    _p.add_argument(f'--telescope', default=DEFAULT_TELESCOPE, help="""Telescope, default='%(default)s'""")
    args = _p.parse_args()
    nightlog(_date=args.date, _telescope=args.telescope, _instrument=args.instrument, _observation_type=args.observation_type)

