#!/usr/bin/env python3.7


# +
# import(s)
# -
from src import *
from src.models.Models import ObsReq, User, user_filters
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import argparse
import csv
import json
import random


# +
# __doc__ string
# -
__doc__ = """

  % python3 upload_from_file.py --help

"""


# +
# constant(s)
# -
TRUE_VALUES = ['true', 't', '1']
FALSE_VALUES = ['false', 'f', '0']


# +
# function: upload_from_file()
# -
def upload_from_file(_infil='', _from_cli=False, _verbose=False):

    # check input(s)
    if _infil == '':
        raise Exception(f'Invalid argument, infil={_infil}')
    if not isinstance(_from_cli, bool):
        _from_cli = False
    if _verbose:
        print(f"Executing> upload_from_file(_infil={_infil}, _from_cli={_from_cli}, _verbose={_verbose})")

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

    # connect to database
    if _from_cli:
        try:
            if _verbose:
                print(f"Connecting to database {ARTN_DB_NAME}")
            engine = create_engine(f'postgresql+psycopg2://{ARTN_DB_USER}:{ARTN_DB_PASS}@'
                                   f'{ARTN_DB_HOST}:{ARTN_DB_PORT}/{ARTN_DB_NAME}')
            get_session = sessionmaker(bind=engine)
            session = get_session()
            if _verbose:
                print(f"Connected to database {ARTN_DB_NAME}")

        except Exception:
            if _verbose:
                print(f"<ERROR> failed connecting to database {ARTN_DB_NAME}")
            raise Exception('Failed to connect to database')
    else:
        engine, get_session, session = None, None, None

    for _i in range(0, _num):
        if _verbose:
            print(f"Creating object {_columns['object_name'][_i]} for {_columns['username'][_i]}")

        # get data
        _username = _columns['username'][_i]
        _telescope = _columns['telescope'][_i]
        _instrument = _columns['instrument'][_i]
        _object_name = _columns['object_name'][_i]
        _ra_hms = _columns['ra'][_i]
        _dec_dms = _columns['dec'][_i]
        _filter_name = _columns['filter'][_i]
        _exp_time = _columns['exp_time'][_i]
        _num_exp = _columns['num_exp'][_i]
        _airmass = _columns['airmass'][_i]
        _lunarphase = _columns['lunarphase'][_i]
        _priority = _columns['priority'][_i]
        _photometric = _columns['photometric'][_i]
        _photometric = True if str(_photometric).lower() in TRUE_VALUES else False
        _guiding = _columns['guiding'][_i]
        _guiding = True if str(_guiding).lower() in TRUE_VALUES else False
        _non_sidereal = _columns['non_sidereal'][_i]
        _non_sidereal = True if str(_non_sidereal).lower() in TRUE_VALUES else False
        _begin_iso = _columns['begin'][_i]
        _end_iso = _columns['end'][_i]
        _binning = _columns['binning'][_i]
        _dither = _columns['dither'][_i]
        _cadence = _columns['cadence'][_i]
        # noinspection PyBroadException
        try:
            _non_sidereal_json = _columns['non_sidereal_json'][_i]
        except Exception:
            _non_sidereal_json = '{}'

        # filter users
        if _from_cli:
            try:
                _u = session.query(User)
                _u = user_filters(_u, {'username': f"{_columns['username'][_i]}"})
                _u = _u.first()
            except Exception as e:
                raise Exception(f'Failed to execute query, error={e}')
        else:
            _u = User.query.filter_by(username=f"{_columns['username'][_i]}").first()

        # set default(s)
        if _non_sidereal:
            _str = _columns['non_sidereal_json'][_i]
            _str_start = _str.find('{')
            _str_end = _str.rfind('}') + 1
            _json = f"{_str[_str_start:_str_end]}"
            _non_sidereal_json = json.loads(_json)
        else:
            _non_sidereal_json = json.loads('{}')

        _iso = get_iso()
        _mjd = iso_to_mjd(_iso)
        _priority = _columns['priority'][_i]
        _begin_mjd = iso_to_mjd(_begin_iso)
        _end_mjd = iso_to_mjd(_end_iso)
        _sign = -1.0 if random.uniform(-1.0, 1.0) < 0.0 else 1.0
        if _lunarphase == 'dark':
            _moonphase = _sign * random.uniform(0.0, 5.5)
        elif _lunarphase == 'grey':
            _moonphase = _sign * random.uniform(5.5, 8.5)
        else:
            _moonphase = _sign * random.uniform(8.5, 15.0)
        _priority_value = -_mjd if _priority == 'urgent' else _mjd

        _queued_iso = ARTN_ZERO_ISO
        _queued_mjd = ARTN_ZERO_MJD
        _completed_iso = ARTN_ZERO_ISO
        _completed_mjd = ARTN_ZERO_MJD

        # create obsreq object
        if _verbose:
            print(f"Instantiating ObsReq(username={_username}, pi=f'{_u.firstname} {_u.lastname}, {_u.affiliation}', "
                  f"created_iso={_iso}, created_mjd={_mjd}, group_id={get_unique_hash()}, "
                  f"observation_id={get_unique_hash()}, priority={_priority}, priority_value={_priority_value}, "
                  f"object_name={_object_name}, ra_hms={_ra_hms}, ra_deg={ra_to_deg(_ra_hms)}, dec_dms={_dec_dms}, "
                  f"dec_deg={dec_to_deg(_dec_dms)}, begin_iso={_begin_iso}, begin_mjd={_begin_mjd}, "
                  f"end_iso={_end_iso}, end_mjd={_end_mjd}, airmass={_airmass}, lunarphase={_lunarphase}, "
                  f"moonphase={_moonphase}, photometric={_photometric}, guiding={_guiding}, "
                  f"non_sidereal={_non_sidereal}, filter_name={_filter_name}, exp_time={_exp_time}, "
                  f"num_exp={_num_exp}, binning={_binning}, dither={_dither}, cadence={_cadence}, "
                  f"telescope={_telescope}, instrument={_instrument}, rts2_doc='<>', rts2_id=-1, queued=False, "
                  f"queued_iso={_queued_iso}, queued_mjd={_queued_mjd}, completed_iso={_completed_iso}, completed_mjd={_completed_mjd}, "
                  f"completed=False, non_sidereal_json={_non_sidereal_json}, author={_u.__str__()})")
        _or = None
        try:
            # noinspection PyArgumentList
            _or = ObsReq(username=_username, pi=f'{_u.firstname} {_u.lastname}, {_u.affiliation}', created_iso=_iso,
                         created_mjd=_mjd, group_id=get_unique_hash(), observation_id=get_unique_hash(),
                         priority=_priority, priority_value=_priority_value, object_name=_object_name, ra_hms=_ra_hms,
                         ra_deg=ra_to_deg(_ra_hms), dec_dms=_dec_dms, dec_deg=dec_to_deg(_dec_dms),
                         begin_iso=_begin_iso, begin_mjd=_begin_mjd, end_iso=_end_iso, end_mjd=_end_mjd,
                         airmass=_airmass, lunarphase=_lunarphase, moonphase=_moonphase, photometric=_photometric,
                         guiding=_guiding, non_sidereal=_non_sidereal, filter_name=_filter_name, exp_time=_exp_time,
                         num_exp=_num_exp, binning=_binning, dither=_dither, cadence=_cadence, telescope=_telescope,
                         instrument=_instrument, rts2_doc='{}', rts2_id=-1, queued=False, completed=False,
                         queued_iso=_queued_iso, queued_mjd=_queued_mjd, completed_iso=_completed_iso, completed_mjd=_completed_mjd,
                         non_sidereal_json=_non_sidereal_json, author=_u)
        except Exception as e:
            if _verbose:
                print(f"<ERROR> failed instantiating ObsReq(), error={e}")
        else:
            if _verbose:
                print(f"Instantiated ObsReq() OK")
                print(f"Created object {_columns['object_name'][_i]} for {_columns['username'][_i]}")

        # noinspection PyBroadException
        try:
            if _verbose:
                print(f"Commiting ObsReq() to {ARTN_DB_NAME} database")
            session.add(_or)
            session.commit()
            if _verbose:
                print(f"Commited ObsReq() to {ARTN_DB_NAME} database")
        except Exception:
            if _verbose:
                print(f"<ERROR> failed commiting ObsReq() to {ARTN_DB_NAME} database")
            session.rollback()


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Read Database File', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--file', default='', help=f'input file')
    _p.add_argument(f'--verbose', default=False, action='store_true', help=f'if present, produce more verbose output')
    args = _p.parse_args()
    upload_from_file(args.file, _from_cli=True, _verbose=bool(args.verbose))
