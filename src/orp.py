#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.io import fits
from flask import Flask, jsonify, copy_current_request_context, request, \
    render_template, redirect, send_from_directory, url_for, make_response, \
    jsonify, Response
from flask_bootstrap import Bootstrap
from flask_mail import Mail, Message
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_paginate import Pagination, get_page_args
from operator import itemgetter, attrgetter
from hashlib import md5
from src.orp_history import *
from threading import Thread
from urllib.parse import urlencode
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from src.forms.Forms import ConfirmDeleteForm, ConfirmRegistrationForm, FeedbackForm, \
    LoginForm, OldUserHistoryForm, NightLogForm, OldNightLogForm, ObsReqForm, ProfileForm, \
    RegistrationForm, ResetPasswordForm, ResetPasswordRequestForm, UpdateObsReqForm, UploadForm, \
    UserHistoryForm, OBSERVATION_TYPES
from src.models.Models import db, obsreq_filters, ObsReq, User, user_filters
from src.models.Models import obsreq2_filters, ObsReq2, ObsExposure, NightlyQueue, NightlyQueueExposure
from src.telescopes.factory import *
from src.telescopes.bok import *
from src.telescopes.kuiper import *
from src.telescopes.vatt import *
from src.telescopes.artn_scheduler import *
from rts2solib import rts2comm

from src import *

import csv
import glob
import itertools
import json
import pdfkit
import random
import time
import datetime
import astropy
import signal
import urllib.parse


# +
# logging
# -
logger = UtilsLogger('ORP-Logger').logger
logger.info(f'PYTHONPATH = {PYTHONPATH}')
logger.info(f'ARTN_DB_HOST = {ARTN_DB_HOST}')
logger.info(f'ARTN_DB_NAME = {ARTN_DB_NAME}')
logger.info(f'ARTN_DB_PASS = {ARTN_DB_PASS}')
logger.info(f'ARTN_DB_PORT = {ARTN_DB_PORT}')
logger.info(f'ARTN_DB_USER = {ARTN_DB_USER}')
logger.info(f'ARTN_MAIL_SERVER = {ARTN_MAIL_SERVER}')
logger.info(f'ARTN_MAIL_PORT = {ARTN_MAIL_PORT}')
logger.info(f'ARTN_MAIL_USE_TLS = {ARTN_MAIL_USE_TLS}')
logger.info(f'ARTN_MAIL_USE_SSL = {ARTN_MAIL_USE_SSL}')
logger.info(f'ARTN_MAIL_USERNAME = {ARTN_MAIL_USERNAME}')
logger.info(f'ARTN_MAIL_PASSWORD = {ARTN_MAIL_PASSWORD}')
logger.info(f'ORP_APP_HOST = {ORP_APP_HOST}')
logger.info(f'ORP_APP_PORT = {ORP_APP_PORT}')
logger.info(f'ORP_APP_URL = {ORP_APP_URL}')
logger.info(f'ORP_HOME = {ORP_HOME}')


# +
# supported system(s)
# -
ARTN_SUPPORTED_NODES = {'Bok': ['BCSpec', '90Prime'], 'Kuiper': ['Mont4k'], 'MMT': ['BinoSpec'], 'Vatt': ['Vatt4k']}
ARTN_SUPPORTED_TELESCOPES = [_k for _k in ARTN_SUPPORTED_NODES]
ARTN_SUPPORTED_INSTRUMENTS = list(itertools.chain.from_iterable([_v for _k, _v in ARTN_SUPPORTED_NODES.items()]))


# +
# telescope(s)
# 
TELESCOPES = {
    'bok': Telescope(name='bok'),
    'kuiper': Telescope(name='kuiper'),
    'mmt': Telescope(name='mmt'),
    'vatt': Telescope(name='vatt')
}
TELESCOPES['bok'].observe = bok_observe
#TELESCOPES['kuiper'].observe = kuiper_observe
TELESCOPES['kuiper'].observe = kuiper_observe2
TELESCOPES['vatt'].observe = vatt_observe


# +
# initialize
# -
app = Flask(__name__)
app.config['SECRET_KEY'] = ARTN_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f'postgresql+psycopg2://{ARTN_DB_USER}:{ARTN_DB_PASS}@{ARTN_DB_HOST}:{ARTN_DB_PORT}/{ARTN_DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = ARTN_MAIL_SERVER
app.config['MAIL_PORT'] = int(ARTN_MAIL_PORT)
app.config['MAIL_USE_TLS'] = ARTN_MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = ARTN_MAIL_USERNAME
app.config['MAIL_PASSWORD'] = ARTN_MAIL_PASSWORD
app.config['SCRIPTS_BASH'] = f'{os.getenv("ORP_BIN")}'
app.config['SCRIPTS_PYTHON'] = f'{os.getenv("ORP_UTILS")}'


# +
# initialize bootstrap
# -
bootstrap = Bootstrap(app)


# +
# initialize mail
# -
mail = Mail(app)


# +
# initialize api
# -
from . import api


def create_gmail(subject='', sender='', recipients=None, text_body='', html_body=''):
    if not isinstance(subject, str) or subject.strip() == '':
        raise Exception(f'Invalid input, subject={subject}')
    if not isinstance(sender, str) or sender.strip() == '':
        raise Exception(f'Invalid input, sender={sender}')
    if recipients is None or not isinstance(recipients, list) or recipients is []:
        raise Exception(f'Invalid input, recipient={recipients}')

    # return message object
    logger.info(f"create_gmail(subject='{subject}', sender='{sender}', recipients='{recipients}', "
                f"text_body='{text_body}', html_body='{html_body}'")
    return Message(subject=subject, sender=sender, recipients=recipients, body=text_body, html=html_body)


def send_gmail_async(_msg=None):
    @copy_current_request_context
    def send_gmail_in_thread(_msg):
        mail.send(_msg)

    if _msg is not None:
        logger.info(f'Calling asynchronous mail.send()')
        Thread(name='gmail_send_async', target=send_gmail_in_thread, args=(_msg,)).start()


def send_gmail(_msg=None):
    if _msg is not None:
        logger.info(f'Calling synchronous mail.send()')
        mail.send(_msg)


# +
# initialize login
# -
login = LoginManager(app)
login.login_view = 'orp_login'


@login.user_loader
def load_user(_id=''):
    return User.query.get(int(_id))


# +
# initialize sqlalchemy
# -
with app.app_context():
    db.init_app(app)


# +
# (utility) function(s)
# -
def request_wants_json():
    if request.args.get('format', 'html', type=str) == 'json':
        return True
    else:
        best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
        return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def msg_out(_text='', _logger_msg=True, _flash_msg=True):
    if _logger_msg:
        logger.debug(_text)
    if _flash_msg:
        flash(_text)


def get_client_ip(_request=None):
    if _request is not None:
        forwarded_ips = _request.headers.getlist('X-Forwarded-For')
        client_ip = forwarded_ips[0].split(',')[0] if len(forwarded_ips) >= 1 else ''
        msg_out(f'Incoming request from client_ip="{client_ip}"', True, False)
        msg_out(f'Incoming request with request_args="{_request.args}"', True, False)
        msg_out(f"Server address={request.remote_addr}", True, False)
        msg_out(f"Client address={request.environ['REMOTE_ADDR']}", True, False)


### +
### since the introduction is ObsReq2, this is broken??!!!
### -
def check_upload_format(_infil=''):
    # check input(s)
    if not isinstance(_infil, str) or _infil.strip() == '':
        msg_out(f'ERROR: Invalid argument, infil={_infil}', True, True)
        return -1, {}
    msg_out(f"check_upload_format> entry, _infil={_infil}", True, False)

    # does infil file exist?
    _file = os.path.abspath(os.path.expanduser(_infil))
    if not os.path.isfile(_file):
        msg_out(f'ERROR: File not found, _file={_file}', True, True)
        return -1, {}
    msg_out(f"check_upload_format> found _file={_file}", True, False)

    # get number of lines in file
    _num = 0
    with open(_file, 'r') as _fd:
        _num = sum(1 for _l in _fd if (_l.strip() != '' and _l.strip()[0] not in r'#%!<>+\/'))
    msg_out(f"check_upload_format> file {_file} has {_num} non-comment entries", True, False)

    # check file type is supported
    _delimiter = ''
    if _file.lower().endswith('csv'):
        _delimiter = ','
        msg_out(f"check_upload_format> file {_file} has {_num} non-comment entries in CSV format", True, False)
    elif _file.lower().endswith('tsv'):
        _delimiter = '\t'
        msg_out(f"check_upload_format> file {_file} has {_num} non-comment entries in TSV format", True, False)
    else:
        msg_out(f'ERROR: Unsupported file type (not .csv, .tsv)', True, True)
        return -1, {}

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
        msg_out(f'ERROR: Irregular number of elements in {_file}, please check {_file}', True, True)
        return -1, {}
    msg_out(f"check_upload_format> file {_file} has passed the sanity check", True, False)

    # change the dictionary keys to remove unwanted characters
    for _k in list(_columns.keys()):
        _columns[_k.translate({ord(i): None for i in ' !@#$'})] = _columns.pop(_k)

    # check V2 headers and JSON
    if all(_k in _columns for _k in ARTN_ALLOWED_HEADERS_V2):
        msg_out(f"check_upload_format> File {_file} supports V2 format (non-sidereal enabled)", True, False)
        msg_out(f"check_upload_format> _num={_num}, _columns={_columns}", True, False)

    # check V1 headers and JSON
    elif all(_k in _columns for _k in ARTN_ALLOWED_HEADERS_V1):
        msg_out(f"check_upload_format> File {_file} supports V1 format (non-sidereal disabled)", True, False)
        msg_out(f"check_upload_format> _num={_num}, _columns={_columns}", True, False)
        return _num, _columns

    # invalid headers
    else:
        msg_out(f'ERROR: Failed to get all allowed headers, please check {_file}', True, True)
        return -1, {}

    # check the json
    if 'non_sidereal_json' in _columns:
        _nsj = _columns['non_sidereal_json']
        msg_out(f'_nsj = {_nsj}', True, False)

        for _e in _nsj:
            _e = _e.replace("'", "")
            msg_out(f'checking for valid JSON in {_nsj}', True, False)
            if "{}" in _e:
                continue
            else:
                if not check_json(f"{_e}",  True):
                    msg_out(f'ERROR: Failed to validate JSON, please check {_file}', True, True)
                    return -1, {}
                else:
                    msg_out(f'JSON is validated in {_nsj}', True, False)

    # return
    return _num, _columns


def upload_file_async(_columns=None, _num=0, _user=None):
    @copy_current_request_context
    def upload_file_in_thread(_columns, _num, _user):
        upload_file(_columns, _num, _user)

    if _columns is not None:
        Thread(name='upload_file_async', target=upload_file_in_thread, args=(_columns, _num, _user,)).start()

### +
### since the introduction is ObsReq2, this is broken??!!!
### -
def upload_file(_columns=None, _num=0, _user=None):
    for _i in range(0, _num):
        msg_out(f"upload_file> creating observation request {_columns['object_name'][_i]} for "
                f"{_columns['username'][_i]}", True, False)

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

        # is user allowed to upload this request?
        if _user is None:
            msg_out(f"ERROR: no authorization to create an ObsReq() for {_username}", True, True)
        else:
            if (_user.username.strip().lower() == _username.strip().lower()) or _user.is_admin:
                pass
            else:
                msg_out(f"ERROR: {_user.username} does not have permission to create an ObsReq() "
                        f"for {_username}", True, True)
                continue

        # check telescope / instrument pairing
        if f'{_instrument}' not in ARTN_SUPPORTED_NODES[f'{_telescope}']:
            msg_out(f"upload_file> invalid telescope ({_telescope}) and instrument ({_instrument}) combination",
                    True, False)
            continue

        # check known limit(s)
        _d = dec_to_deg(_dec_dms)
        if _d > TEL__DEC__LIMIT[f'{_telescope.lower()}']:
            msg_out(f"upload_file> requested declination {_d:.3f} > {TEL__DEC__LIMIT[_telescope.lower()]} limit "
                    f"for {_telescope} telescope", True, False)
            continue

        # set default(s)
        if _non_sidereal:
            _str = _columns['non_sidereal_json'][_i]
            _str_start = _str.find('{')
            _str_end = _str.rfind('}') + 1
            _json = f"{_str[_str_start:_str_end]}"
            if check_json(_json):
                _non_sidereal_json = json.loads(_json)
            else:
                msg_out(f"upload_file> json not valid ... skipping", True, False)
                continue
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

        # noinspection PyArgumentList
        msg_out(f"upload_file> instantiating ObsReq(username={_username}, pi=f'{_user.firstname} {_user.lastname}, "
                f"{_user.affiliation}', created_iso={_iso}, created_mjd={_mjd}, group_id={get_unique_hash()}, "
                f"observation_id={get_unique_hash()}, priority={_priority}, "
                f"priority_value=-{_mjd} if _priority == 'urgent' else {_mjd}, object_name={_object_name}, "
                f"ra_hms={_ra_hms}, ra_deg={ra_to_deg(_ra_hms)}, dec_dms={_dec_dms}, dec_deg={dec_to_deg(_dec_dms)}, "
                f"begin_iso={_begin_iso}, begin_mjd={_begin_mjd}, end_iso={_end_iso}, end_mjd={_end_mjd}, "
                f"airmass={_airmass}, lunarphase={_lunarphase}, moonphase={_moonphase}, photometric={_photometric}, "
                f"guiding={_guiding}, non_sidereal={_non_sidereal}, filter_name={_filter_name}, exp_time={_exp_time}, "
                f"num_exp={_num_exp}, binning={_binning}, dither={_dither}, cadence={_cadence}, "
                f"telescope={_telescope}, instrument={_instrument}, rts2_doc='<>', rts2_id=-1, queued=False, "
                f"queued_iso={ARTN_ZERO_ISO}, queued_mjd={ARTN_ZERO_MJD}, completed_iso={ARTN_ZERO_ISO}, completed_mjd={ARTN_ZERO_MJD}, "
                f"completed=False, non_sidereal_json={_non_sidereal_json})", True, False)
        _or = None
        try:
            # create obsreq object
            # noinspection PyArgumentList
            _or = ObsReq(username=_username, pi=f'{_user.firstname} {_user.lastname}, {_user.affiliation}',
                         created_iso=_iso, created_mjd=_mjd, group_id=get_unique_hash(),
                         observation_id=get_unique_hash(), priority=_priority,
                         priority_value=_priority_value, object_name=_object_name,
                         ra_hms=_ra_hms, ra_deg=ra_to_deg(_ra_hms), dec_dms=_dec_dms, dec_deg=dec_to_deg(_dec_dms),
                         begin_iso=_begin_iso, begin_mjd=_begin_mjd, end_iso=_end_iso, end_mjd=_end_mjd,
                         airmass=_airmass, lunarphase=_lunarphase, moonphase=_moonphase, photometric=_photometric,
                         guiding=_guiding, non_sidereal=_non_sidereal, filter_name=_filter_name, exp_time=_exp_time,
                         num_exp=_num_exp, binning=_binning, dither=_dither, cadence=_cadence, telescope=_telescope,
                         instrument=_instrument, rts2_doc='{}', rts2_id=-1, queued=False, completed=False,
                         queued_iso=ARTN_ZERO_ISO, queued_mjd=ARTN_ZERO_MJD, completed_iso=ARTN_ZERO_ISO, completed_mjd=ARTN_ZERO_MJD,
                         non_sidereal_json=_non_sidereal_json, author=_user)
        except Exception as _e:
            msg_out(f"ERROR: failed instantiating ObsReq(), error={_e}", True, True)
        else:
            msg_out(f"upload_file> instantiated ObsReq() OK", True, False)

        # update database (admin is allowed insert any records, users on those they own)
        if _user.is_admin or (_user.username.lower() == _username.lower()):
            try:
                db.session.add(_or)
                db.session.commit()
                msg_out(f"upload_file> loaded object {_columns['object_name'][_i]} for {_columns['username'][_i]}",
                        True, False)
            except Exception as _e:
                db.session.rollback()
                msg_out(f"ERROR: Failed to create observation request {_columns['object_name'][_i]} for "
                        f"{_columns['username'][_i]}, error={_e}", True, True)
                return redirect(url_for('orp_user', username=_user.username))


# noinspection PyBroadException
def history_seek_json(_path=os.getcwd(), _ajd=0.0, _bjd=0.0):

    # check input(s)
    try:
        _path = os.path.abspath(os.path.expanduser(f'{_path}'))
        if not isinstance(_path, str) or _path.strip() == '' or not os.path.isdir(_path):
            return {}
    except Exception:
        return {}

    if not isinstance(_ajd, float) or not (0.0 < _ajd < get_jd()):
        return {}

    if not isinstance(_bjd, float) or not (_ajd < _bjd < get_jd()):
        return {}

    msg_out(f'history_seek_json> searching {_path} over {_bjd-_ajd} days', True, False)

    # generator code
    _fw = (
        os.path.join(_root, _file)
        for _root, _dirs, _files in os.walk(_path)
        for _file in _files
    )

    # return all files within jd period - this only works if the file modification time has not been altered!
    try:
        return {
            f'{_k}': iso_to_jd(time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(os.stat(f'{_k}').st_mtime)))
            for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                              _k.endswith('.json') and int(os.stat(f'{_k}').st_size) > 2 and
                              (_ajd < iso_to_jd(time.strftime('%Y-%m-%dT%H:%M:%S',
                                                              time.localtime(os.stat(f'{_k}').st_mtime))) < _bjd))
        }
    except Exception:
        return {}


# noinspection PyBroadException
def old_history_seek(_path=ARTN_DATA_ROOT, _type='.json', _jd=0.0):
    """ returns list of files: size of given type in directory tree or {} """

    # check input(s)
    if not isinstance(_path, str) or _path.strip() == '':
        return {}
    if not isinstance(_type, str) or _type.strip() == '':
        return {}
    if not isinstance(_jd, float) or _jd < 0.0:
        return {}

    # (re)set default(s)
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))
    if not os.path.isdir(_path):
        return {}

    # generator code
    _fw = (
        os.path.join(_root, _file)
        for _root, _dirs, _files in os.walk(_path)
        for _file in _files
    )

    # return all files within jd period - this only works if the file modification time has not been altered!
    try:
        return {f'{_k}': iso_to_jd(time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(os.stat(f'{_k}').st_mtime)))
                for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                  _k.endswith(f'{_type}') and int(os.stat(f'{_k}').st_size) > 2
                                  and iso_to_jd(time.strftime('%Y-%m-%dT%H:%M:%S',
                                                              time.localtime(os.stat(f'{_k}').st_mtime))) > _jd)}
    except Exception:
        return {}


# noinspection PyBroadException
def history_load_user(_fdict=None, _observation='', _user=''):

    # check input(s)
    if not isinstance(_fdict, dict) or _fdict is None or _fdict is {}:
        return []
    if not isinstance(_observation, str) or _observation.strip() == '':
        return []
    if not isinstance(_user, str) or _user.strip() == '':
        return []

    msg_out(f'history_load_user> _fdict={_fdict}, _observation={_observation}, _user={_user}', True, False)

    # load json data
    _j_list = []
    for _k in _fdict:
        try:
            _this_json = None
            with open(f'{_k}', 'r') as _fr:
                _this_json = list(json.load(_fr))
            for _e in _this_json:
                if _observation.lower() == 'all' or f'/{_observation.lower()}/' in _e['file']:
                    if _user.strip().lower() in _e['user'].strip().lower():
                        logger.debug(f'history_load_user> _e={_e}')
                        _j_list.append(_e)
        except Exception:
            continue

    # return
    return _j_list


# noinspection PyBroadException
def old_history_loader(_fdict=None):
    """ returns list of file entries or [] """

    # check input(s)
    if not isinstance(_fdict, dict) or _fdict is None or _fdict is {}:
        return []

    # load json data
    _json = []
    for _k in _fdict:
        try:
            _this_json = None
            with open(f'{_k}', 'r') as _fr:
                _this_json = list(json.load(_fr))
            for _e in _this_json:
                _json.append(_e)
        except Exception:
            continue

    # return
    return _json


# noinspection PyBroadException
def history_get_fits_headers(_in=None):

    # check input(s)
    if _in is None or not isinstance(_in, list) or _in is []:
        return []

    # get fits data
    _l_out = []
    for _e in _in:
        _d_out = {'FILE': os.path.basename(_e['file']), 'DIRECTORY': os.path.dirname(_e['file']),
                  'SIZE': _e['size'], 'OWNER': _e['user']}
        with fits.open(_e['file']) as _hdul:
            for _h in ARTN_FITS_HEADERS:
                try:
                    _d_out[_h.replace('-', '')] = str(_hdul[0].header[_h]).strip()
                except Exception:
                    _d_out[_h] = ''

        # append new record
        _l_out.append(_d_out)

    # return list sorted by Julian date key
    return sorted(_l_out, key=lambda _i: _i['JULIAN'])


def old_history_search(_flist=None, _lookback=0.0, _name=''):
    """ returns list of file entries or [] """

    # check input(s)
    if not isinstance(_flist, list) or _flist is None or _flist is []:
        return []
    if not isinstance(_lookback, float) or _lookback < 0.0:
        return []
    if not isinstance(_name, str):
        return []

    # search
    _udata = []
    for _e in _flist:
        _object = ''
        if 'gid' in _e:
            _o = ObsReq.query.filter_by(group_id=_e['gid']).first() 
            if _o:
                _object = encode_verboten(_o.object_name.strip(), ARTN_ENCODE_DICT)

        if 'timestamp' in _e:
            _jd = iso_to_jd(_e['timestamp'])
        else:
            _jd = iso_to_jd(get_date_time())

        if 'email' in _e and _name in _e['email'] and _jd > _lookback:
            _udata.append(f"{_jd} {_e['timestamp']:26s} {_e['file']:30s} {_e['email']} {_object}")

    # return
    return sorted(_udata, reverse=True)


def get_user_history(_after=0.0, _before=get_jd(), _instrument='Mont4k',
                     _observation='all', _telescope='Kuiper', _user=''):

    # check input(s)
    if not isinstance(_after, float) or not (0.0 < _after < get_jd()):
        logger.error(f'Invalid input, _after={_after}')
        return []
    if not isinstance(_before, float) or not (_after < _before < get_jd()):
        logger.error(f'Invalid input, _before={_before}')
        return []
    if not isinstance(_instrument, str) or _instrument.strip() == '' or _instrument not in ARTN_SUPPORTED_INSTRUMENTS:
        logger.error(f'Invalid input, _instrument={_instrument}')
        return []
    if not isinstance(_observation, str) or _observation.strip() == '':
        logger.error(f'Invalid input, _observation={_observation}')
        return []
    if not isinstance(_telescope, str) or _telescope.strip() == '' or _telescope not in ARTN_SUPPORTED_TELESCOPES:
        logger.error(f'Invalid input, _telescope={_telescope}')
        return []
    if _instrument not in ARTN_SUPPORTED_NODES[_telescope]:
        logger.error(f'Invalid telescope ({_telescope}) and instrument ({_instrument}) combination')
        return []

    msg_out(f"get_user_history> _after={_after}, _before={_before}, _instrument={_instrument}, "
            f"_observation={_observation}, _telescope={_telescope}, _user={_user}", True, False)

    # find .json files
    _json = history_seek_json(f'{ARTN_DATA_ROOT}/{_telescope}/{_instrument}', _after, _before)

    # search .json files for observation type and user
    _load = history_load_user(_json, _observation, _user)

    # return fits headers for all files found
    return history_get_fits_headers(_load)


# noinspection PyBroadException
def get_old_history(_path=ARTN_DATA_ROOT, _type='.dna.json', _lookback=ARTN_LOOKBACK_PERIOD, _user=''):

    # check input(s)
    if not isinstance(_path, str) or _path.strip() == '':
        return []
    if not isinstance(_type, str) or _type.strip() == '':
        return []
    if not isinstance(_lookback, int) or _lookback < 0:
        return []
    if not isinstance(_user, str):
        return []
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))
    if not os.path.isdir(f'{_path}'):
        return []
    _now = iso_to_jd(get_date_time())
    _lb = iso_to_jd(get_date_time(-_lookback))
    msg_out(f"get_old_history> _path={_path}, _type={_type}, _lookback={_lookback}, _user={_user}, "
            f"_lb={_lb}, _now={_now}", True, False)

    # get and munge data
    _files = old_history_seek(_path, _type, _lb)
    _jlist = old_history_loader(_files)
    _data = old_history_search(_jlist, _lb, _user)

    # create output 
    _op = []
    for _e in _data:
        _r = _e.split()
        try:
            _t = {'jd': _r[0], 'ts': _r[1], 'file': _r[2], 'email': _r[3],
                  'object': decode_verboten(_r[4], ARTN_DECODE_DICT)}
            _op.append(_t)
        except Exception:
            continue
    return _op


def get_old_history_page(_results=None, _offset=0, _per_page=ARTN_RESULTS_PER_PAGE):
    return _results[_offset: _offset + _per_page]


# noinspection PyBroadException
def nlog_seek_files(_path: str = os.getcwd(), _include: str = 'all'):

    # get input(s)
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))
    if not os.path.isdir(_path):
        return {}
    _include = _include.lower().strip()
    if _include not in ['all', 'stitched', 'raw']:
        return {}

    # generator code
    _fw = (
        os.path.join(_root, _file)
        for _root, _dirs, _files in os.walk(_path)
        for _file in _files
    )

    # get file(s)
    try:
        if _include == 'all':
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2)}
        elif (_include == 'raw' or _include == 'unstitched'):
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      'stitched' not in _k and
                                      _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2)}
        elif _include == 'stitched':
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      'stitched' in _k and
                                      _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2)}
        else:
            return {}
    except Exception:
        return {}


# noinspection PyBroadException
def get_old_nightlog(_path=ARTN_DIR_OBJECTS, _type=''):
    """ returns list of files: size of given type in directory tree or {} """

    # check input(s)
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))
    if not os.path.isdir(_path):
        return {}
    if _type.lower() not in [_l[0] for _l in OBSERVATION_TYPES]:
        return {}

    # generator code
    _fw = (
        os.path.join(_root, _file)
        for _root, _dirs, _files in os.walk(_path)
        for _file in _files
    )

    # return all files within directory
    _type = _type.lower()
    if _type == 'darks':
        try:
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2)}
        except Exception:
            return {}

    elif _type == 'flats':
        try:
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      (os.path.basename(_k).lower().startswith('flat') and
                                       _k.lower().endswith('.fits')) and int(os.stat(f'{_k}').st_size) > 2)}
        except Exception:
            return {}

    elif _type == 'focus':
        try:
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2)}
        except Exception:
            return {}

    elif _type == 'objects':
        try:
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2 and
                                      not os.path.basename(_k).lower().startswith('focus') and
                                      not os.path.basename(_k).lower().startswith('flat'))}
        except Exception:
            return {}

    elif _type == 'skyflats':
        try:
            return {f'{_k}': int(os.stat(f'{_k}').st_size)
                    for _k in _fw if (not os.path.islink(f'{_k}') and os.path.exists(f'{_k}') and
                                      _k.endswith('.fits') and int(os.stat(f'{_k}').st_size) > 2)}
        except Exception:
            return {}
    else:
        return {}


### +
### since the introduction is ObsReq2, this is broken??!!!
### -
# noinspection PyBroadException
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

        # +
        # why was the ARTNGID removed from the database table
        # as this was going to be used to identify dither member(s)?!!!
        # -
        try:
            # who requested it?
            # if _d_out['ARTNGID'].strip() != '' and _d_out['ARTNOID'].strip() != '':
            if _d_out['ARTNOID'].strip() != '':
                query = db.session.query(ObsReq2)
                # query = obsreq_filters(query, {'group_id': f"{_d_out['ARTNGID']}"})
                query = obsreq2_filters(query, {'observation_id': f"{_d_out['ARTNOID']}"})
                _d_out['OWNER'] = query.first().username
            else:
                _d_out['OWNER'] = ''
        except Exception:
            _d_out['OWNER'] = ''

        # append new record
        _l_out.append(_d_out)

    # return list sorted by Julian date key
    msg_out(f'nlog_get_fits_headers()> _l_out={_l_out}', True, False)
    return sorted(_l_out, key=lambda _i: _i['JULIAN'])


# noinspection PyBroadException
def get_old_nightlog_fits(_in=None):

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

        # +
        # why was the ARTNGID removed from the database table
        # as this was going to be used to identify dither member(s)?!!!
        # -
        try:
            # who requested it?
            # if _d_out['ARTNGID'].strip() != '' and _d_out['ARTNOID'].strip() != '':
            if _d_out['ARTNOID'].strip() != '':
                query = db.session.query(ObsReq2)
                # query = obsreq_filters(query, {'group_id': f"{_d_out['ARTNGID']}"})
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


def get_current_queue_table(rts2ids, obsreqs_dict, table_class, expids, username):
    FOCUS_FIELD_IDS = [3611, 3612, 3613, 3614, 3615, 3616, 3617, 3618, 3619, 3620, 3621, 3622, 3623, 3624]
    html= ''
    for rts2_id in rts2ids:
        try:
            ob = obsreqs_dict[rts2_id]
            t_expids = [x['id'] for x in ob['exposures']]
            allchecked = ' checked' if all([tid in expids for tid in t_expids]) else ''
            ob = obsreqs_dict[rts2_id]
            nameid = ob['object_name']
            btn_disable = ''
            if '+' in nameid:
                nameid = nameid.replace('+', '')
            object_href = '<a href="/orp/obsreq2/{}?obsreqid={}&return_page=orp_manage_queue">{}</a>'.format(username,ob['id'],ob['object_name'])
            status = ob['obs_status']
            print(nameid,status)
            if status == 'inprogress':
                status = 'In Progress (%{})'.format(ob['percent_completed'])
            elif status == 'completed':
                status = 'Completed (%100)'
            else:
                status = 'Queued (%0.0)'
        except:
            if rts2_id == 1:
                nameid = 'DARK FRAMES'
            if rts2_id == 2:
                nameid = 'FLAT FRAMES'
            if rts2_id in FOCUS_FIELD_IDS:
                nameid = 'FOCUS FIELD'

            btn_disable = 'disabled '
            ob = {
                'id':-1,
                'object_name':nameid,
                'ra_hms':'',
                'dec_dms':'',
                'exposures':[]
            }
            allchecked = False
            object_href=nameid
            status = ''
            
        html += '''
        <tr class="{}">
            <td><button {}id="collbtn{}" onclick="changeCollapseButtonText(this.id)" type="button" class="btn btn-primary btn-xs arrow-right" data-toggle="collapse" data-target="#collapse{}"></button></td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td></td>
            <td></td>
            <td></td>
            <td>{}</td>
            <td><input id="queuetarg_{}" type="checkbox" onclick="objectCheckAll(this.id)"{}></td>
        </tr>
        '''.format(table_class,btn_disable,nameid,nameid,object_href,ob['ra_hms'],ob['dec_dms'], status, nameid, allchecked)
        html+= '''
        <tr class="collapse" id="collapse{}">
            <td colspan="999">
                <div>
                    <table class="table table-striped table-sm">
                        <thead>
                            <tr>
                                <td><font color='blue'>Filter</font></td>
                                <td><font color='blue'>Exptime (s)</font></td>
                                <td><font color='blue'>Num Exp</font></td>
                                <td><font color='blue'>Requeue</font><td>
                            </tr>
                        </thead>
                        <tbody>
        '''.format(nameid)
        for obexp in ob['exposures']:
            thischecked = ' checked' if obexp['id'] in expids else ''
            html+='''
                                <tr>
                                    <td>{}</td>
                                    <td>{}</td>
                                    <td>{}</td>
                                    <td><input value="{}" id="{}_{}" type="checkbox" onclick="expCheckOne(this.id)"{}></td>
                                </tr>
            '''.format(obexp['filter_name'], obexp['exp_time'], obexp['num_exp'], obexp['id'], nameid, obexp['id'], thischecked)
        html += '''
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
        '''
    
    return html

# +
# error handler(s)
# -
@app.errorhandler(401)
def not_allowed_error(error=None):
    if error is None:
        raise Exception('Access unauthorized')
    return render_template('401.html'), 401


@app.errorhandler(403)
def not_allowed_error(error=None):
    if error is None:
        raise Exception('Access forbidden')
    return render_template('403.html'), 403


@app.errorhandler(404)
def not_found_error(error=None):
    if error is None:
        raise Exception('Invalid argument')
    return render_template('404.html'), 404


@app.errorhandler(415)
def not_found_error(error=None):
    if error is None:
        raise Exception('Invalid argument')
    return render_template('415.html'), 415


@app.errorhandler(500)
def internal_error(error=None):
    if error is None:
        raise Exception('Server error')
    db.session.rollback()
    return render_template('500.html'), 500


# +
# update database before request(s)
# -
# noinspection PyPep8
@app.before_request
def before_request():
    if current_user.is_authenticated:
        _iso = get_iso()
        _mjd = iso_to_mjd(_iso)
        current_user.last_seen_iso = _iso
        current_user.last_seen_mjd = _mjd
        try:
            db.session.commit()
        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to update database, error={_e}', True, False)


# +
# route(s): /, /orp
# -
@app.route('/orp/orp/')
@app.route('/orp/')
@app.route('/')
def orp_home():
    msg_out(f'/orp/ entry', True, False)
    get_client_ip(_request=request)
    return render_template('orp.html', url={'url': f'{ORP_APP_URL}', 'page': '/orp'})


# +
# route(s): /orp/api, requires login
# -
#@app.route('/orp/orp/api/')
#@app.route('/orp/api/')
#@app.route('/api/')
#@login_required
#def orp_api():
#    msg_out(f'/orp/api entry', True, False)
#    get_client_ip(_request=request)
#    return render_template('api.html', url={'url': f'{ORP_APP_URL}', 'page': '/orp/api'}, user=current_user)


# +
# route(s): /orp/cli_upload/<username>
# -
@app.route('/orp/orp/cli_upload/<username>', methods=['POST'])
@app.route('/orp/cli_upload/<username>', methods=['POST'])
@app.route('/cli_upload/<username>', methods=['POST'])
def cli_upload(username=''):
    msg_out(f'/orp/cli_upload/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # get request
    if 'file' not in request.files:
        return jsonify({'status': 400, 'message': 'Bad request'})

    # get file
    _file = request.files['file']
    msg_out(f'/orp/cli_upload/{username} _file={_file}', True, False)
    if not _file:
        return jsonify({'status': 404, 'message': 'File not found'})
    if os.path.splitext(_file.filename)[-1][1:] not in ARTN_SUPPORTED_FILETYPES:
        return jsonify({'status': 404, 'message': 'Unsupported file type'})
    filename = secure_filename(_file.filename)
    pathname = os.path.join(app.instance_path, 'files', f'{_u.username}_{filename}')

    # load it
    try:
        _file.save(pathname)
        _num, _columns = check_upload_format(pathname)
        if _num < 0 or _columns is {}:
            msg_out(f'ERROR: /orp/cli_upload/{username} input file has invalid format, '
                    f'please check {pathname}', True, False)
            return jsonify({'status': 404, 'filename': filename, 'message': f"{filename} has invalid format"})
        if _num < 100:
            upload_file(_columns, _num, _u)
            return jsonify({'status': 200, 'filename': filename, 'message': f"{filename} "
                                                                            f"uploading synchronously ... OK"})
        else:
            upload_file_async(_columns, _num, _u)
            return jsonify({'status': 200, 'filename': filename, 'message': f"{filename} uploading asynchronously"})

    except Exception as _e:
        return jsonify({'status': 500, 'message': f"{_e}"})


# +
# route(s): /orp/confirm_delete/<dbid>, requires login
# -
@app.route('/orp/orp/confirm_delete/<obsreqid>', methods=['GET', 'POST'])
@app.route('/orp/confirm_delete/<obsreqid>', methods=['GET', 'POST'])
@app.route('/confirm_delete/<obsreqid>', methods=['GET', 'POST'])
@login_required
def orp_confirm_delete(obsreqid=''):
    msg_out(f'/orp/confirm_delete/{obsreqid} entry', True, False)
    get_client_ip(request)

    return_page = request.args.get('return_page', 'orp_view_requests')

    _args = request.args.copy()
    try:
        _args.pop('obsreqid')
    except KeyError:
        pass
    arg_str = urlencode(_args)

    # build form
    form = ConfirmDeleteForm()

    # validate form (POST request)
    if form.validate_on_submit():

        # update database
        try:
            ObsReq2.query.filter_by(id=obsreqid).delete()
            ObsExposure.query.filter_by(obsreqid=obsreqid).delete()
            db.session.commit()
            msg_out(f'Observation request {obsreqid} deleted OK', True, True)
        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to delete observation request {obsreqid}, error={_e}', True, True)

        return redirect(url_for(return_page, username=current_user.username) + '?' + arg_str)

    # return for GET
    return render_template('confirm_delete.html', username=current_user.username, form=form, return_page=return_page)


# +
# route(s): /orp/confirm_registration/<token>
# -
@app.route('/orp/orp/confirm_registration/<token>', methods=['GET', 'POST'])
@app.route('/orp/confirm_registration/<token>', methods=['GET', 'POST'])
@app.route('/confirm_registration/<token>', methods=['GET', 'POST'])
@login_required
def orp_confirm_registration(token=None):
    msg_out(f'/orp/confirm_registration/{token} entry', True, False)
    get_client_ip(request)

    # if we are not an admin, re-direct
    if not current_user.is_admin:
        msg_out(f'Only admin users may perform confirm new user registrations!', True, True)
        return redirect(url_for('orp_home'))

    # verify token
    _u = User.verify_confirm_registration_token(token)
    if _u is None:
        msg_out(f'ERROR: Invalid token {token}', True, True)
        return redirect(url_for('orp_home'))

    # build form
    form = ConfirmRegistrationForm()

    # GET method
    if request.method == 'GET':
        form.firstname.data = _u.firstname
        form.lastname.data = _u.lastname
        form.username.data = _u.username
        form.affiliation.data = _u.affiliation
        form.email.data = _u.email
        form.is_disabled.data = _u.is_disabled
        return render_template('confirm_registration.html', form=form)

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _fn = form.firstname.data.strip()
        _ln = form.lastname.data.strip()
        _us = form.username.data.strip()
        _em = form.email.data.strip()
        _af = form.affiliation.data.strip()
        _id = form.is_disabled.data

        # change record
        try:
            _u.firstname = _fn if (_fn != _u.firstname) else _u.firstname
            _u.lastname = _ln if (_fn != _u.lastname) else _u.lastname
            _u.username = _us if (_us != _u.username) else _u.username
            _u.affiliation = _af if (_af != _u.affiliation) else _u.affiliation
            _u.email = _em if (_em != _u.email) else _u.email
            _u.email = _id if (_id != _u.is_disabled) else _u.is_disabled

            db.session.commit()

            # send new user welcome email
            send_gmail_async(create_gmail(
                'Welcome to the ARTN Observation Request Portal',
                sender=ARTN_MAIL_USERNAME,
                recipients=[f'{_em}'],
                text_body=render_template('_new_user_approved.txt', user=_u),
                html_body=render_template('_new_user_approved.html', user=_u)))
            msg_out(f'User {_u.username} account has been confirmed', True, True)
            return redirect(url_for('orp_user', username=current_user.username))

        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to confirm user {_u.username} account, error={_e}', True, True)

    # return
    return render_template('confirm_registration.html', form=form)


# +
# route(s): /orp/delete/<username>?dbid=<num>, requires login
# -
@app.route('/orp/orp/delete/<username>', methods=['GET', 'POST'])
@app.route('/orp/delete/<username>', methods=['GET', 'POST'])
@app.route('/delete/<username>', methods=['GET', 'POST'])
@login_required
def orp_delete(username=''):
    msg_out(f'/orp/delete/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # get dbid
    obsreqid = request.args.get('obsreqid', None)
    return_page = request.args.get('return_page', 'orp_view_requests')

    _args = request.args.copy()
    try:
        _args.pop('obsreqid')
    except KeyError:
        pass
    arg_str = urlencode(_args)

    if obsreqid is None:
        msg_out(f'ERROR: Failed to get observation id {obsreqid}', True, True)
        return redirect(url_for(return_page, username=_u.username))

    # get observation request
    _obsreq = ObsReq2.query.filter_by(id=obsreqid).first_or_404()

    # confirm deletion
    if _obsreq.queued:
        return redirect(url_for('orp_confirm_delete', obsreqid=obsreqid) + '?' + arg_str +'&return_page='+return_page)

    # delete from database
    else:
        try:
            ObsReq2.query.filter_by(id=obsreqid).delete()
            ObsExposure.query.filter_by(obsreqid=obsreqid).delete()
            db.session.commit()
            msg_out(f'Observation request {obsreqid} deleted OK', True, True)
        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to delete observation request {obsreqid}, error={_e}', True, True)

    # return for GET
    return redirect(url_for(return_page, username=_u.username) + '?' + arg_str)


# +
# route(s): /orp/download/artn_template.v1.csv
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/download/artn_template.v1.csv')
@app.route('/orp/download/artn_template.v1.csv')
@app.route('/download/artn_template.v1.csv')
def orp_download_csv_v1():
    msg_out(f'/orp/download/artn_template.v1.csv entry', True, False)
    get_client_ip(_request=request)
    return send_from_directory(
        directory=os.path.join(app.instance_path, 'files'), filename='artn_template.v1.csv')


# +
# route(s): /orp/download/artn_template.v1.tsv
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/download/artn_template.v1.tsv')
@app.route('/orp/download/artn_template.v1.tsv')
@app.route('/download/artn_template.v1.tsv')
def orp_download_tsv_v1():
    msg_out(f'/orp/download/artn_template.v1.tsv entry', True, False)
    get_client_ip(_request=request)
    return send_from_directory(
        directory=os.path.join(app.instance_path, 'files'), filename='artn_template.v1.tsv')


# +
# route(s): /orp/download/artn_template.v2.tsv
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/download/artn_template.v2.tsv')
@app.route('/orp/download/artn_template.v2.tsv')
@app.route('/download/artn_template.v2.tsv')
def orp_download_tsv_v2():
    msg_out(f'/orp/download/artn_template.v2.tsv entry', True, False)
    get_client_ip(_request=request)
    return send_from_directory(
        directory=os.path.join(app.instance_path, 'files'), filename='artn_template.v2.tsv')


# +
# route(s): /orp/download/check_upload_format_standalone.py
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/download/check_upload_format_standalone.py')
@app.route('/orp/download/check_upload_format_standalone.py')
@app.route('/download/check_upload_format_standalone.py')
def orp_download_check_upload_format_standalone():
    msg_out(f'/orp/download/check_upload_format_standalone.py entry', True, False)
    get_client_ip(_request=request)
    return send_from_directory(
        directory=app.config['SCRIPTS_PYTHON'], filename='check_upload_format_standalone.py', as_attachment=True)


# +
# route(s): /orp/download/orp_cli_upload.sh
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/download/orp_cli_upload.sh')
@app.route('/orp/download/orp_cli_upload.sh')
@app.route('/download/orp_cli_upload.sh')
def orp_download_cli_upload():
    msg_out(f'/orp/download/orp_cli_upload.sh entry', True, False)
    get_client_ip(_request=request)
    return send_from_directory(
        directory=app.config['SCRIPTS_BASH'], filename='orp_cli_upload.sh', as_attachment=True)


# +
# route(s): /orp/feedback/<username>, requires login
# -
@app.route('/orp/orp/feedback/<username>', methods=['GET', 'POST'])
@app.route('/orp/feedback/<username>', methods=['GET', 'POST'])
@app.route('/feedback/<username>', methods=['GET', 'POST'])
@login_required
def orp_feedback(username=''):
    msg_out(f'/orp/feedback/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # build form
    form = FeedbackForm()

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _category = form.category.data.strip()
        _urgency = form.urgency.data.strip()
        _report = form.report.data.strip()
        _fn = form.screenshot.data

        # upload
        if _fn is not None:
            filename = secure_filename(_fn.filename)
            pathname = os.path.join(app.instance_path, 'files', f'{_u.username}_{filename}')
            _fn.save(pathname)
        else:
            filename = ''

        # send email
        _page = {
            'category': f'{_category}',
            'urgency': f'{_urgency}',
            'report': f'{_report}',
            'filename': f'{filename}'
        }
        send_gmail(create_gmail(
            f'Feedback from {_u.firstname} {_u.lastname}, {_u.affiliation} ({_u.username}, {_u.email})',
            sender=ARTN_MAIL_USERNAME,
            recipients=[f'{_u.email}', ARTN_MAIL_USERNAME],
            text_body=render_template('_user_feedback.txt', user=_u, page=_page),
            html_body=render_template('_user_feedback.html', user=_u, page=_page)))

        # re-direct to login page
        return render_template('feedback_ok.html', incoming={'url': f'/orp/user/{_u.username}',
                                                             'text': f'Thanks, {_u.firstname}, for your feedback'})

    else:
        for _e in form.errors:
            msg_out(f'ERROR: invalid value {form.errors[_e][0]}', True, False)

    # return for GET
    return render_template('feedback.html', form=form)


# +
# route: /orp/files/<download_file>
# -
@app.route('/orp/orp/files/<download_file>')
@app.route('/orp/files/<download_file>')
@app.route('/files/<download_file>')
@login_required
def orp_get_file(download_file=''):
    msg_out(f'/orp/files/{download_file} entry', True, False)
    get_client_ip(_request=request)

    # check file exists
    _directory = os.path.join(app.instance_path, 'files')
    _file = f'{os.path.basename(download_file)}'
    if not os.path.exists(os.path.abspath(os.path.expanduser(f'{os.path.join(_directory, _file)}'))):
        return render_template('401.html')
    msg_out(f"Serving {os.path.abspath(os.path.expanduser(os.path.join(_directory, _file)))} to "
            f"{current_user.username}", True, False)

    # if it's a CSV or TSV files, the filename is of the form <user>_<file>.csv or <user>_<file>.tsv
    if _file.lower().endswith('csv') or _file.lower().endswith('tsv'):
        _u = _file.split('_')[0].strip().lower()
    # if it's a TGZ file, the filename is of the form <user>.<date>.<id>.tgz
    elif _file.lower().endswith('tgz'):
        _u = _file.split('.')[0].strip().lower()
        if _u.lower() in ARTN_RESERVED_USERNAMES:
            _u = current_user.username
    # unknown
    else:
        _u = ''

    # return content
    if current_user.is_admin or (_u != '' and _u == current_user.username.lower()):
        try:
            return send_from_directory(
                directory=f'{_directory}', filename=f'{_file}', mimetype='application/octet-stream',
                as_attachment=True, attachment_filename=f'{_file}')
        except Exception as _e:
            msg_out(f'ERROR: {_e}', True, True)
            return render_template('404.html')
    else:
        return render_template('401.html')


# +
# route(s): /orp/help, requires login
# -
@app.route('/orp/orp/help/')
@app.route('/orp/help/')
@app.route('/help/')
@login_required
def orp_help():
    msg_out(f'/orp/help entry', True, False)
    get_client_ip(_request=request)
    return render_template('help.html', url={'url': f'{ORP_APP_URL}', 'page': '/orp/help'})


# +
# route(s): /orp/old_history/, requires login
# -
# noinspection PyBroadException
@app.route('/orp/orp/old_history/', methods=['GET', 'POST'])
@app.route('/orp/old_history/', methods=['GET', 'POST'])
@app.route('/old_history/', methods=['GET', 'POST'])
@login_required
def orp_old_history():
    msg_out(f'/orp/old_history/ entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _user = request.args.get('username', '')
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=_user).first_or_404()

    # build form
    form = OldUserHistoryForm(telescope='Kuiper', instrument='Mont4k')

    # GET method
    if request.method == 'GET':
        if _u.is_admin:
            form.username.data = _user
        else:
            form.username.data = _u.username

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _username = User.query.filter_by(username=form.username.data.strip()).first_or_404()
        _lookback = int(form.lookback.data.strip())
        _ins = form.instrument.data.strip()
        _tel = form.telescope.data.strip()

        if isinstance(_username, User):
            msg_out(f'/orp/old_history/ _username={repr(_username)}, _lookback={_lookback}', True, False)
        else:
            msg_out(f'/orp/old_history/ _username={str(_username)}, _lookback={_lookback}', True, False)

        if f'{_ins}' not in ARTN_SUPPORTED_NODES[f'{_tel}']:
            return render_template('409.html',
                                   reason=f'Invalid telescope ({_tel}) and instrument ({_ins}) combination!',
                                   caller='orp_old_history')

        # get history
        _history = []
        _d_path = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}"
        if _u.is_admin:
            _history = get_old_history(_path=_d_path, _type='.dna.json',
                                       _lookback=_lookback, _user=_username.username)
        else:
            if _username.username.strip().lower() == _u.username.strip().lower():
                _history = get_old_history(_path=_d_path, _type='.dna.json',
                                           _lookback=_lookback, _user=_username.username)
            else:
                msg_out(f'ERROR: User {_username.username} does not have permission to view record(s) for {_user}',
                        True, True)
                return render_template('401.html')
        _total = len(_history)
        msg_out(f'/orp/old_history/ _history={_history}, _total={_total}', True, False)

        # output
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = ARTN_RESULTS_PER_PAGE
        offset = (page - 1) * ARTN_RESULTS_PER_PAGE
        pagination_history = get_old_history_page(_history, offset, per_page)
        pagination = Pagination(page=page, per_page=per_page, offset=offset, total=_total, css_framework='bootstrap4')
        return render_template('old_user_history_results.html', history=pagination_history, total=_total,
                               lookback=_lookback, page=page, per_page=per_page, pagination=pagination,
                               user=_username, telescope=_tel, instrument=_ins)

    # return
    return render_template('old_user_history.html', form=form)


# +
# route(s): /orp/history/, requires login
# -
# noinspection PyBroadException
@app.route('/orp/orp/history/', methods=['GET', 'POST'])
@app.route('/orp/history/', methods=['GET', 'POST'])
@app.route('/history/', methods=['GET', 'POST'])
@login_required
def orp_history():
    msg_out(f'/orp/history/ entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _user = request.args.get('username', '')
    _u = User.query.filter_by(username=_user).first_or_404()

    # build form
    form = UserHistoryForm(telescope='Kuiper', instrument='Mont4k', observation='object', user=_u.username)

    # GET method
    if request.method == 'GET':
        form.after.data = get_date_time(-90)
        form.before.data = get_date_time(0)

    # validate form (POST request)
    if form.validate_on_submit():

        # get form value(s)
        _after = str(form.after.data).strip().split()[0]
        _before = str(form.before.data).strip().split()[0]
        _ins = form.instrument.data.strip()
        _obs = form.observation.data.lower().strip()
        _pdf = form.pdf.data
        _tel = form.telescope.data.strip()
        _user = form.user.data.lower().strip()

        _ajd = iso_to_jd(f'{_after}T00:00:00.000000')
        _bjd = iso_to_jd(f'{_before}T00:00:00.000000')
        msg_out(f'/orp/history/ _after={_after}, _ajd={_ajd}, _before={_before}, _bjd={_bjd}, _ins={_ins}, '
                f'_obs={_obs}, _pdf={_pdf}, _tel={_tel}, _user={_user}', True, False)

        if f'{_ins}' not in ARTN_SUPPORTED_NODES[f'{_tel}']:
            return render_template('409.html',
                                   reason=f'Invalid telescope ({_tel}) and instrument ({_ins}) combination!',
                                   caller='orp_history')

        # get history
        _u = User.query.filter_by(username=_user).first_or_404()
        if _u.is_admin:
            _history = get_user_history(_ajd, _bjd, _ins, _obs, _tel, _user)
        else:
            if _user.strip().lower() == _u.username.strip().lower():
                _history = get_user_history(_ajd, _bjd, _ins, _obs, _tel, _user)
            else:
                _history = []
                msg_out(f'ERROR: User {_u.username} does not have permission to view record(s) for {_user}', True, True)
                return render_template('401.html')
        _total = len(_history)

        # render page or create pdf
        _s_all = f"{_total} observations for {_user} on server scopenet.as.arizona.edu in directory " \
                 f"{ARTN_DATA_ROOT}/{_tel}/{_ins} between {_after} and {_before}"
        _nod = TEL__NODES[_tel.lower()]
        _html = f'user_history_results_pdf.html' if _pdf else f'user_history_results.html'
        msg_out(f'/orp/history/ using template {_html}', True, False)
        _rendered = render_template(_html, pdf=_pdf, user=_u, tel=_tel, nod=_nod, after=_after,
                                    before=_before, history=_history, n_all=_total, s_all=_s_all)
        if _pdf:
            _obslog = pdfkit.from_string(_rendered, False, css=f"{ARTN_BASE_DIR}/static/css/main.css")
            _response = make_response(_obslog)
            _response.headers['Content-Type'] = 'application/pdf'
            _response.headers['Content-Disposition'] = f'attachment; ' \
                                                       f'filename={_tel}.{_ins}.{_u.firstname}.{_u.lastname}.pdf'
            return _response
        else:
            return _rendered

    # return
    return render_template('user_history.html', form=form)


# +
# route(s): /orp/instance_files, requires login
# -
@app.route('/orp/orp/instance_files/<ftype>/')
@app.route('/orp/instance_files/<ftype>/')
@app.route('/instance_files/<ftype>/')
@login_required
def dir_listing(ftype=''):
    msg_out(f'/orp/instance_files/{ftype} entry', True, False)
    get_client_ip(request)

    # check file support
    if ftype.lower() not in ARTN_SUPPORTED_FILETYPES:
        return render_template('415.html')

    # get data
    _results = []
    if current_user.is_admin:
        _files = glob.glob(f"{os.path.join(app.instance_path, 'files')}/*.{ftype}")
    else:
        _files = glob.glob(f"{os.path.join(app.instance_path, 'files')}/*{current_user.username}*.{ftype}")
    msg_out(f'/orp/instance_files/{ftype} _files={_files}', True, False)

    # return result(s)
    for _e in _files:
        if 'template' in _e.lower():
            continue
        _num, _columns = -1, {}
        if _e.lower().endswith('csv') or _e.lower().endswith('tsv'):
            _num, _columns = check_upload_format(f'{_e}')
            if _num > 0 and _columns:
                _dict = {'file': f'{_e}', 'name': f'{os.path.basename(_e)}', 'OK': True}
            else:
                _dict = {'file': f'{_e}', 'name': f'{os.path.basename(_e)}', 'OK': False}
            _results.append(_dict)
        elif _e.lower().endswith('tgz'):
            if int(os.stat(f'{_e}').st_size) > 45:
                _dict = {'file': f'{_e}', 'name': f'{os.path.basename(_e)}', 'OK': True}
            else:
                _dict = {'file': f'{_e}', 'name': f'{os.path.basename(_e)}', 'OK': False}
            _results.append(_dict)

    msg_out(f'/orp/instance_files/{ftype} _results={_results}', True, False)

    # Show directory contents
    _response = {'total': len(_results), 'results': _results}
    msg_out(f'/orp/instance_files/{ftype} _response={_response}', True, False)
    return render_template('files.html', response=_response)


# +
# route(s): /orp/login
# -
@app.route('/orp/orp/login', methods=['GET', 'POST'])
@app.route('/orp/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def orp_login():
    msg_out(f'/orp/login entry', True, False)
    get_client_ip(_request=request)

    # if current user is authenticated, re-direct to the user page
    if current_user.is_authenticated:
        _u_ok = User.query.filter_by(username=current_user.username).first_or_404()
        return render_template('user.html', user=_u_ok)

    # build form
    form = LoginForm()

    # form authenticates (POST request)
    if form.validate_on_submit():

        # get data
        _u = form.username.data.strip()
        _p = form.password.data.strip()
        _r = form.remember_me.data

        # get user
        _db_u = User.query.filter_by(username=_u).first()

        # invalid username
        if _db_u is None:
            msg_out(f'ERROR: Invalid username {_u}, please try again', True, True)
            return render_template('login.html', form=form)

        # invalid password
        elif not _db_u.check_password(_p):
            msg_out(f'ERROR: Invalid password for {_db_u.username}, please try again', True, True)
            return render_template('login.html', form=form)

        # disabled account
        elif _db_u.is_disabled:
            _msg = f'This account is disabled. Please contact {ARTN_MAIL_USERNAME} for further assistance.'
            msg_out(f'ERROR: {_msg}', True, True)
            return render_template('index.html', incoming={'url': f'/orp/login', 'text': f'{_msg}'})

        else:
            msg_out(f'User {_db_u.username}, login successful', True, False)

        # login the user
        login_user(_db_u, remember=_r)

        # if there was a redirect to get here, do it
        next_page = request.args.get('next')
        msg_out(f'next_page = {next_page}', True, False)
        if next_page is None or url_parse(next_page).netloc != '':
            return redirect(url_for('orp_user', username=_u))
        else:
            return redirect(next_page)

    # return for GET
    return render_template('login.html', form=form)


# +
# route(s): /orp/logout
# -
@app.route('/orp/orp/logout')
@app.route('/orp/logout')
@app.route('/logout')
def orp_logout():
    msg_out(f'/orp/logout entry', True, False)
    get_client_ip(_request=request)
    logout_user()
    return render_template('orp.html', url={'url': f'{ORP_APP_URL}', 'page': '/orp/logout'})


# +
# route(s): /orp/nightlog/, requires login
# -
# noinspection PyBroadException
@app.route('/orp/orp/nightlog/', methods=['GET', 'POST'])
@app.route('/orp/nightlog/', methods=['GET', 'POST'])
@app.route('/nightlog/', methods=['GET', 'POST'])
@login_required
def orp_nightlog():
    msg_out(f'/orp/nightlog/ entry', True, False)
    get_client_ip(request)

    # only admin can do this
    if not current_user.is_admin:
        return render_template('403.html')

    # build form
    form = NightLogForm(telescope='Kuiper', instrument='Mont4k', fits='Stitched')

    # GET method
    if request.method == 'GET':
        form.iso.data = get_date_time(0)

    # validate form (POST request)
    if form.validate_on_submit():

        # get form value(s)
        _ins = form.instrument.data.strip()
        _iso = str(form.iso.data).strip().split()[0].replace('-', '')
        _obs = form.obs.data.lower().strip()
        _pdf = form.pdf.data
        _tel = form.telescope.data.strip()
        _fit = form.fits.data.lower().strip()
        msg_out(f'/orp/nightlog/ _fit={_fit}, _ins={_ins}, _iso={_iso}, _obs={_obs}, _pdf={_pdf}, _tel={_tel}', True, False)

        if f'{_ins}' not in ARTN_SUPPORTED_NODES[f'{_tel}']:
            return render_template('409.html',
                                   reason=f'Invalid telescope ({_tel}) and instrument ({_ins}) combination!',
                                   caller='orp_nightlog')

        # set default(s)
        _d_bias, _d_calibration, _d_dark, _d_flat, _d_focus, _d_object, _d_skyflat, _d_standard = \
            '', '', '', '', '', '', '', ''
        _f_bias, _f_calibration, _f_dark, _f_flat, _f_focus, _f_object, _f_skyflat, _f_standard = \
            {}, {}, {}, {}, {}, {}, {}, {}
        _h_bias, _h_calibration, _h_dark, _h_flat, _h_focus, _h_object, _h_skyflat, _h_standard = \
            [], [], [], [], [], [], [], []
        _n_bias, _n_calibration, _n_dark, _n_flat, _n_focus, _n_object, _n_skyflat, _n_standard = \
            0, 0, 0, 0, 0, 0, 0, 0
        _s_bias, _s_calibration, _s_dark, _s_flat, _s_focus, _s_object, _s_skyflat, _s_standard = \
            '', '', '', '', '', '', '', ''
        _f_all, _n_all, _s_all = {}, 0, ''

        # seek files and headers
        if _obs == 'all' or _obs == 'bias':
            _d_bias = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/bias" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/bias/stitched"
            _f_bias = nlog_seek_files(_d_bias, _fit)
            _h_bias = nlog_get_fits_headers(_f_bias)
            _n_bias = len(_f_bias)
            _s_bias = f"{_n_bias} BIAS observations on server scopenet.as.arizona.edu in directory {_d_bias}"
            msg_out(f'/orp/nightlog/ searching {_d_bias}', True, False)
        if _obs == 'all' or _obs == 'calibration':
            _d_calibration = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/calibration" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/calibration/stitched"
            _f_calibration = nlog_seek_files(_d_calibration, _fit)
            _h_calibration = nlog_get_fits_headers(_f_calibration)
            _n_calibration = len(_f_calibration)
            _s_calibration = f"{_n_calibration} CALIBRATION observations on server scopenet.as.arizona.edu " \
                             f"in directory {_d_calibration}"
            msg_out(f'/orp/nightlog/ searching {_d_calibration}', True, False)
        if _obs == 'all' or _obs == 'dark':
            _d_dark = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/dark" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/dark/stitched"
            _f_dark = nlog_seek_files(_d_dark, _fit)
            _h_dark = nlog_get_fits_headers(_f_dark)
            _n_dark = len(_f_dark)
            _s_dark = f"{_n_dark} DARK observations on server scopenet.as.arizona.edu in directory {_d_dark}"
            msg_out(f'/orp/nightlog/ searching {_d_dark}', True, False)
        if _obs == 'all' or _obs == 'flat':
            _d_flat = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/flat" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/flat/stitched"
            _f_flat = nlog_seek_files(_d_flat, _fit)
            _h_flat = nlog_get_fits_headers(_f_flat)
            _n_flat = len(_f_flat)
            _s_flat = f"{_n_flat} FLAT observations on server scopenet.as.arizona.edu in directory {_d_flat}"
            msg_out(f'/orp/nightlog/ searching {_d_flat}', True, False)
        if _obs == 'all' or _obs == 'focus':
            _d_focus = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/focus" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/focus/stitched"
            _f_focus = nlog_seek_files(_d_focus, _fit)
            _h_focus = nlog_get_fits_headers(_f_focus)
            _n_focus = len(_f_focus)
            _s_focus = f"{_n_focus} FOCUS observations on server scopenet.as.arizona.edu in directory {_d_focus}"
            msg_out(f'/orp/nightlog/ searching {_d_focus}', True, False)
        if _obs == 'all' or _obs == 'object':
            _d_object = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/object" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/object/stitched"
            _f_object = nlog_seek_files(_d_object, _fit)
            _h_object = nlog_get_fits_headers(_f_object)
            _n_object = len(_f_object)
            _s_object = f"{_n_object} OBJECT observations on server scopenet.as.arizona.edu in directory {_d_object}"
            msg_out(f'/orp/nightlog/ searching {_d_object}', True, False)
        if _obs == 'all' or _obs == 'skyflat':
            _d_skyflat = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/skyflat" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/skyflat/stitched"
            _f_skyflat = nlog_seek_files(_d_skyflat, _fit)
            _h_skyflat = nlog_get_fits_headers(_f_skyflat)
            _n_skyflat = len(_f_skyflat)
            _s_skyflat = f"{_n_skyflat} SKYFLAT observations on server scopenet.as.arizona.edu " \
                         f"in directory {_d_skyflat}"
            msg_out(f'/orp/nightlog/ searching {_d_skyflat}', True, False)
        if _obs == 'all' or _obs == 'standard':
            _d_standard = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/standard" if _fit != 'stitched' else f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}/standard/stitched"
            _f_standard = nlog_seek_files(_d_standard, _fit)
            _h_standard = nlog_get_fits_headers(_f_standard)
            _n_standard = len(_f_standard)
            _s_standard = f"{_n_standard} STANDARD observations on server scopenet.as.arizona.edu " \
                          f"in directory {_d_standard}"
            msg_out(f'/orp/nightlog/ searching {_d_standard}', True, False)

        # amalgamate
        _d_all = f"{ARTN_DATA_ROOT}/{_tel}/{_ins}/{_iso}"
        _f_all = {**_f_bias, **_f_calibration, **_f_dark, **_f_flat, **_f_focus, **_f_object, **_f_skyflat, **_f_standard}
        _n_all = len(_f_all)
        _s_all = f"{_n_all} observations on server scopenet.as.arizona.edu in directory {_d_all}"
        msg_out(f'/orp/nightlog/ _s_all={_s_all}', True, False)

        # render page or create pdf
        _nod = TEL__NODES[_tel.lower()]
        msg_out(f'/orp/nightlog/ _nod={_nod}', True, False)
        _html = f'nightlog_results_pdf.html' if _pdf else f'nightlog_results.html'
        msg_out(f'/orp/nightlog/ using template {_html}', True, False)
        _rendered = render_template(_html, pdf=_pdf, user=current_user, tel=_tel, nod=_nod, iso=_iso, 
                                    h_bias=_h_bias, n_bias=_n_bias, s_bias=_s_bias, 
                                    h_calibration=_h_calibration, n_calibration=_n_calibration,
                                    s_calibration=_s_calibration, h_dark=_h_dark, n_dark=_n_dark, s_dark=_s_dark,
                                    h_flat=_h_flat, n_flat=_n_flat, s_flat=_s_flat, 
                                    h_focus=_h_focus, n_focus=_n_focus, s_focus=_s_focus, 
                                    h_object=_h_object, n_object=_n_object, s_object=_s_object, 
                                    h_skyflat=_h_skyflat, n_skyflat=_n_skyflat, s_skyflat=_s_skyflat, 
                                    h_standard=_h_standard, n_standard=_n_standard, s_standard=_s_standard, 
                                    n_all=_n_all, s_all=_s_all)
        msg_out(f'/orp/nightlog/ _rendered={_rendered}', True, False)
        if _pdf:
            msg_out(f'/orp/nightlog/ _css={ARTN_BASE_DIR}/static/css/main.css', True, False)
            _options = {'enable-local-file-access': True}
            _obslog = pdfkit.from_string(_rendered, False, css=f"{ARTN_BASE_DIR}/static/css/main.css", options=_options)
            _response = make_response(_obslog)
            _response.headers['Content-Type'] = 'application/pdf'
            _response.headers['Content-Disposition'] = f'attachment; filename={_tel}.{_ins}.{_iso}.{_obs}.pdf'
            return _response

        else:
            return _rendered

        # return
    return render_template('nightlog.html', form=form)


# +
# route(s): /orp/old_nightlog/, requires login
# -
# noinspection PyBroadException
@app.route('/orp/orp/old_nightlog/', methods=['GET', 'POST'])
@app.route('/orp/old_nightlog/', methods=['GET', 'POST'])
@app.route('/old_nightlog/', methods=['GET', 'POST'])
@login_required
def orp_old_nightlog():
    msg_out(f'/orp/old_nightlog/ entry', True, False)
    get_client_ip(request)

    # only admin can do this
    if not current_user.is_admin:
        return render_template('403.html')

    # build form
    form = OldNightLogForm(telescope='Kuiper')

    # GET method
    if request.method == 'GET':
        form.iso.data = get_date_time(0)

    # validate form (POST request)
    if form.validate_on_submit():

        # get form value(s)
        _obs = form.obs.data.strip()
        _iso = str(form.iso.data).strip().split()[0].replace('-', '')
        _tel = form.telescope.data.strip()
        _pdf = form.pdf.data
        msg_out(f'/orp/old_nightlog/ _obs={_obs}, _iso={_iso}, _tel={_tel}, _pdf={_pdf}', True, False)

        # search for data
        _all, _darks, _foci, _flats, _objects, _skyflats = {}, {}, {}, {}, {}, {}
        if _obs == 'all':
            _darks = get_old_nightlog(_path=f'{ARTN_DIR_DARKS.replace("YYYYMMDD", _iso)}', _type='darks')
            _flats = get_old_nightlog(_path=f'{ARTN_DIR_FLATS.replace("YYYYMMDD", _iso)}', _type='flats')
            _foci = get_old_nightlog(_path=f'{ARTN_DIR_FOCUS.replace("YYYYMMDD", _iso)}', _type='focus')
            _objects = get_old_nightlog(_path=f'{ARTN_DIR_OBJECTS.replace("YYYYMMDD", _iso)}', _type='objects')
            _skyflats = get_old_nightlog(_path=f'{ARTN_DIR_SKYFLATS.replace("YYYYMMDD", _iso)}', _type='skyflats')
            # _all = {**_darks, **_flats, **_focus, **_objects, **_skyflats}
        elif _obs == 'darks':
            _darks = get_old_nightlog(_path=f'{ARTN_DIR_DARKS.replace("YYYYMMDD", _iso)}', _type=_obs)
        elif _obs == 'flats':
            _flats = get_old_nightlog(_path=f'{ARTN_DIR_FLATS.replace("YYYYMMDD", _iso)}', _type=_obs)
        elif _obs == 'focus':
            _foci = get_old_nightlog(_path=f'{ARTN_DIR_FOCUS.replace("YYYYMMDD", _iso)}', _type=_obs)
        elif _obs == 'objects':
            _objects = get_old_nightlog(_path=f'{ARTN_DIR_OBJECTS.replace("YYYYMMDD", _iso)}', _type=_obs)
        elif _obs == 'skyflats':
            _skyflats = get_old_nightlog(_path=f'{ARTN_DIR_SKYFLATS.replace("YYYYMMDD", _iso)}', _type=_obs)
        else:
            return render_template('401.html')

        # get fits data
        _telescope = TEL__NODES[_tel.lower()]
        _l_darks = get_old_nightlog_fits(_darks)
        _l_flats = get_old_nightlog_fits(_flats)
        _l_foci = get_old_nightlog_fits(_foci)
        _l_objects = get_old_nightlog_fits(_objects)
        _l_skyflats = get_old_nightlog_fits(_skyflats)

        # render page or create pdf
        msg_out(f'/orp/old_nightlog/ _css={ARTN_BASE_DIR}/static/css/main.css', True, False)
        if _pdf:
            _rendered = render_template(f'old_nightlog_{_tel.lower()}_pdf.html', telescope=_telescope, iso=_iso,
                                        user=current_user, darks=_l_darks, flats=_l_flats, foci=_l_foci,
                                        objects=_l_objects, skyflats=_l_skyflats, num_darks=len(_l_darks),
                                        num_flats=len(_l_flats), num_foci=len(_l_foci), num_objects=len(_l_objects),
                                        num_skyflats=len(_l_skyflats))
            _obslog = pdfkit.from_string(_rendered, False, css=f"{ARTN_BASE_DIR}/static/css/main.css")
            _response = make_response(_obslog)
            _response.headers['Content-Type'] = 'application/pdf'
            _response.headers['Content-Disposition'] = f'attachment; filename=obslog_{_iso}.pdf'
            return _response

        else:
            return render_template(f'old_nightlog_{_tel.lower()}.html', telescope=_telescope, iso=_iso,
                                   user=current_user, darks=_l_darks, flats=_l_flats, foci=_l_foci,
                                   objects=_l_objects, skyflats=_l_skyflats, num_darks=len(_l_darks),
                                   num_flats=len(_l_flats), num_foci=len(_l_foci), num_objects=len(_l_objects),
                                   num_skyflats=len(_l_skyflats))

        # return
    return render_template('old_nightlog.html', form=form)


# +
# route(s): /orp/observe/<username>?dbid=<num>, requires login
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/observe/<username>', methods=['GET', 'POST'])
@app.route('/orp/observe/<username>', methods=['GET', 'POST'])
@app.route('/observe/<username>', methods=['GET', 'POST'])
@login_required
def orp_observe(username=''):
    msg_out(f'/orp/observe/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # just delete it without checking!
    _dbid = request.args.get('dbid', None)
    if _dbid is None:
        msg_out(f'ERROR: Failed to get observation id {_dbid}', True, True)
        return redirect(url_for('orp_view_requests', username=_u.username))

    # get observation
    _obsreq = None
    try:
        _obsreq = ObsReq.query.filter_by(id=_dbid).first_or_404()
    except Exception as _e:
        msg_out(f'ERROR: Failed to get observation request {_dbid}, error={_e}', True, True)
        return redirect(url_for('orp_view_requests', username=_u.username))
    else:
        msg_out(f"orp_observe> observation request: _dbid={_dbid}, "
                f"_object_name={decode_verboten(_obsreq.object_name, ARTN_DECODE_DICT)}, "
                f"_user={_u.username}", True, False)

    # call telescope-specific routine
    _rts2_doc = None
    _rts2_id = -1

    if _obsreq is not None:

        _tel_name = _obsreq.telescope.lower()
        msg_out(f"orp_observe> calling TELESCOPES['{_tel_name}'].observe()", True, False)
        _rts2_doc, _rts2_id = TELESCOPES[f'{_tel_name}'].observe(_obsreq=_obsreq, _user=_u)
        msg_out(f"orp_observe> called TELESCOPES['{_tel_name}'].observe()", True, False)

        if _rts2_doc is not None:
            if _rts2_id != -1:
                msg_out(f'Observation request {_dbid} sent to telescope OK', True, False)
            if _rts2_id > 0:
                try:
                    _obsreq.completed = False
                    _obsreq.completed_iso = ARTN_ZERO_ISO
                    _obsreq.completed_mjd = ARTN_ZERO_MJD
                    _obsreq.queued = True
                    _iso = get_iso()
                    _obsreq.queued_iso = _iso
                    _obsreq.queued_mjd = iso_to_mjd(_iso)
                    _obsreq.rts2_doc = _rts2_doc
                    _obsreq.rts2_id = _rts2_id
                    db.session.commit()
                    msg_out(f'Observation request {_dbid} committed to database OK', True, False)
                except Exception as _e:
                    db.session.rollback()
                    msg_out(f'ERROR: Failed to send observation request {_dbid} to telescope, error={_e}', True, True)

    # return for GET
    return redirect(url_for('orp_user', username=_u.username))


# +
# route(s): /orp/obsreq/<username>, requires login
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/obsreq/<username>', methods=['GET', 'POST'])
@app.route('/orp/obsreq/<username>', methods=['GET', 'POST'])
@app.route('/obsreq/<username>', methods=['GET', 'POST'])
@login_required
def orp_obsreq(username=''):
    msg_out(f'/orp/obsreq/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # build form
    form = ObsReqForm(telescope='Kuiper', instrument='Mont4k', user=_u.username)

    # GET method
    if request.method == 'GET':
        form.username.data = _u.username
        form.begin_iso.data = get_date_utctime()
        form.end_iso.data = get_date_utctime(30)
        form.non_sidereal.data = False
        return render_template('obsreq.html', form=form)

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _priority = form.priority.data.strip().lower()
        _object_name = encode_verboten(form.object_name.data.strip(), ARTN_ENCODE_DICT)
        _ra_hms = form.ra_hms.data.strip()
        _dec_dms = form.dec_dms.data.strip()
        _begin_iso = form.begin_iso.data
        _end_iso = form.end_iso.data
        _airmass = form.airmass.data
        _lunarphase = form.lunarphase.data.strip().lower()
        _photometric = form.photometric.data
        _guiding = form.guiding.data
        _non_sidereal = form.non_sidereal.data
        _filter_name = form.filter_name.data.strip()
        _exp_time = form.exp_time.data
        _num_exp = form.num_exp.data
        _binning = form.binning.data.strip()
        _dither = form.dither.data.strip()
        _cadence = form.cadence.data.strip()
        _telescope = form.telescope.data.strip()
        _instrument = form.instrument.data.strip()
        _iso = get_iso()
        _mjd = float(iso_to_mjd(_iso))

        # validate telescope / instrument pair
        if f'{_instrument}' not in ARTN_SUPPORTED_NODES[f'{_telescope}']:
            return render_template('409.html', reason=f'Invalid telescope ({_telescope}) and instrument '
                                                      f'({_instrument}) combination!', caller='orp_osbreq')

        # check known limit(s)
        _d = dec_to_deg(_dec_dms)
        if _d > TEL__DEC__LIMIT[f'{_telescope.lower()}']:
            msg_out(f"ERROR: requested declination {_d:.3f} > {TEL__DEC__LIMIT[_telescope.lower()]} limit "
                    f"for {_telescope} telescope", True, True)
            return redirect(url_for('orp_user', username=_u.username))

        # get json
        if _non_sidereal:
            _str = form.ns_params.data
            _str_start = _str.find('{')
            _str_end = _str.rfind('}') + 1
            _json = f"{_str[_str_start:_str_end]}"
            if check_json(_json):
                _non_sidereal_json = json.loads(_json)
            else:
                msg_out(f"ERROR: json not valid ... skipping", True, True)
                return redirect(url_for('orp_user', username=_u.username))
        else:
            _non_sidereal_json = json.loads('{}')

        # munge the input(s) as required
        _begin_mjd = str(_begin_iso).replace(' ', 'T')
        _begin_mjd = f'{_begin_mjd}.000000'
        _begin_mjd = float(iso_to_mjd(_begin_mjd))

        _end_mjd = str(_end_iso).replace(' ', 'T')
        _end_mjd = f'{_end_mjd}.000000'
        _end_mjd = float(iso_to_mjd(_end_mjd))

        # assign a (nominal) moonphase calculation
        _sign = -1.0 if random.uniform(-1.0, 1.0) < 0.0 else 1.0
        if _lunarphase == 'dark':
            _moonphase = _sign * random.uniform(0.0, 5.5)
        elif _lunarphase == 'grey':
            _moonphase = _sign * random.uniform(5.5, 8.5)
        else:
            _moonphase = _sign * random.uniform(8.5, 15.0)

        # noinspection PyArgumentList
        _or = ObsReq(username=_u.username, pi=f'{_u.firstname} {_u.lastname}, {_u.affiliation}', created_iso=_iso,
                     created_mjd=_mjd, group_id=get_unique_hash(), observation_id=get_unique_hash(),
                     priority=_priority, priority_value=-_mjd if _priority == 'urgent' else _mjd,
                     object_name=_object_name, ra_hms=_ra_hms, ra_deg=ra_to_deg(_ra_hms), dec_dms=_dec_dms,
                     dec_deg=dec_to_deg(_dec_dms), begin_iso=_begin_iso, begin_mjd=_begin_mjd, end_iso=_end_iso,
                     end_mjd=_end_mjd, airmass=_airmass, lunarphase=_lunarphase, moonphase=_moonphase,
                     photometric=_photometric, guiding=_guiding, non_sidereal=_non_sidereal,
                     non_sidereal_json=_non_sidereal_json, filter_name=_filter_name, exp_time=_exp_time,
                     num_exp=_num_exp, binning=_binning, dither=_dither, cadence=_cadence, telescope=_telescope,
                     queued_iso=ARTN_ZERO_ISO, queued_mjd=ARTN_ZERO_MJD, completed_iso=ARTN_ZERO_ISO, completed_mjd=ARTN_ZERO_MJD,
                     instrument=_instrument, queued=False, completed=False, author=_u)

        # update database
        try:
            db.session.add(_or)
            db.session.commit()
            msg_out(f'Observation request {_or.__str__()} created OK', True, True)
            return redirect(url_for('orp_user', username=_u.username))
        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to create observation request for {_u.username}, error={_e}', True, True)
            return render_template('obsreq.html', form=form)

    else:
        for _e in form.errors:
            msg_out(f'ERROR: invalid value {form.errors[_e][0]}', True, False)

    # return for GET
    return render_template('obsreq.html', form=form)


# +
# route(s): /orp/profile/<username>, requires login
# -
@app.route('/orp/orp/profile/<username>', methods=['GET', 'POST'])
@app.route('/orp/profile/<username>', methods=['GET', 'POST'])
@app.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def orp_profile(username=''):
    msg_out(f'/orp/profile/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # build form
    form = ProfileForm()

    # GET method
    if request.method == 'GET':
        form.email.data = _u.email
        form.about_me.data = _u.about_me
        form.affiliation.data = _u.affiliation
        form.avatar.data = _u.avatar
        return render_template('profile.html', form=form)

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _u.email = form.email.data.strip()
        _u.about_me = form.about_me.data.strip()
        _u.affiliation = form.affiliation.data.strip()
        _u.avatar = form.avatar.data.strip()

        # update database
        try:
            db.session.commit()
            msg_out(f'User {_u.username} changes have been saved', True, True)
        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: User {_u.username} changes have not been saved, error={_e}', True, True)
        return redirect(url_for('orp_user', username=_u.username))

    # return for GET
    return render_template('profile.html', form=form)


# +
# (simple) route(s): /orp/register_old
# -
@app.route('/orp/orp/register_old', methods=['GET', 'POST'])
@app.route('/orp/register_old', methods=['GET', 'POST'])
@app.route('/register_old', methods=['GET', 'POST'])
def orp_register_old():
    msg_out(f'/orp/register_old entry', True, False)
    get_client_ip(_request=request)

    # if current user is authenticated, re-direct to the user page
    if current_user.is_authenticated:
        user = User.query.filter_by(username=current_user.username).first_or_404()
        return render_template('user.html', user=user)

    # build form
    form = RegistrationForm()
    msg_out(f'New registration requested, please complete the following form', True, True)

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _fn = form.firstname.data.strip()
        _ln = form.lastname.data.strip()
        _un = form.username.data.strip()
        _em = form.email.data.strip()
        _af = form.affiliation.data.strip()
        _pp = form.passphrase.data.strip()
        _pw = form.password.data.strip()
        _cw = form.confirm.data.strip()
        _ok = form.policy_ok.data

        _iso = get_iso()
        _mjd = iso_to_mjd(_iso)

        # check they've signed the policy agreement
        if not _ok:
            msg_out(f'User {_un} failed to accept policy agreement', True, True)
            return render_template('register.html', form=form)

        # does it match the password rule?
        if re.match(ARTN_PASSWORD_RULE, f'{_pw}') is None:
            msg_out(f'User {_un} password does not conform to rules', True, True)
            return render_template('register.html', form=form)

        # noinspection PyArgumentList
        _u = User(firstname=_fn, lastname=_ln, username=_un, hashword='', passphrase=_pp, email=_em,
                  affiliation=_af, created_iso=_iso, created_mjd=_mjd,
                  avatar=f"http://www.gravatar.com/avatar/{md5(_em.lower().encode('utf-8')).hexdigest()}",
                  about_me='', last_seen_iso=_iso, last_seen_mjd=_mjd, is_admin=False, is_disabled=False)
        _u.set_password(_pw)

        # update database
        try:
            db.session.add(_u)
            db.session.commit()
            msg_out(f'User {_un} registered OK', True, True)

            # send new user welcome email
            send_gmail_async(create_gmail(
                'Welcome to the ARTN Observation Request Portal',
                sender=ARTN_MAIL_USERNAME,
                recipients=[f'{_em}', ARTN_MAIL_USERNAME],
                text_body=render_template('_new_user_welcome_message.txt', user=_u),
                html_body=render_template('_new_user_welcome_message.html', user=_u)))

            # re-direct to login page
            return redirect(url_for('orp_login'))

        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to register new user {_un}, error={_e}', True, True)
            return render_template('register.html', form=form)

    # return for GET
    return render_template('register.html', form=form)


# +
# route(s): /orp/register
# -
@app.route('/orp/orp/register', methods=['GET', 'POST'])
@app.route('/orp/register', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def orp_register():
    msg_out(f'/orp/register entry', True, False)
    get_client_ip(_request=request)

    # if current user is authenticated, re-direct to the user page
    if current_user.is_authenticated:
        user = User.query.filter_by(username=current_user.username).first_or_404()
        return render_template('user.html', user=user)

    # build form
    form = RegistrationForm()

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _fn = form.firstname.data.strip()
        _ln = form.lastname.data.strip()
        _un = form.username.data.strip()
        _em = form.email.data.strip()
        _af = form.affiliation.data.strip()
        _pp = form.passphrase.data.strip()
        _pw = form.password.data.strip()
        _cw = form.confirm.data.strip()
        _ok = form.policy_ok.data
        _iso = get_iso()
        _mjd = iso_to_mjd(_iso)

        # check they've signed the policy agreement
        if not _ok:
            msg_out(f'User {_un} failed to accept policy agreement', True, True)
            return render_template('register.html', form=form)

        # is it a reserved username?
        if _un.lower() in ARTN_RESERVED_USERNAMES:
            msg_out(f'User {_un} is a reserved name, please choose another', True, True)
            return render_template('register.html', form=form)

        # does it match the password rule?
        if re.match(ARTN_PASSWORD_RULE, f'{_pw}') is None:
            msg_out(f'User {_un} password does not conform to rules', True, True)
            return render_template('register.html', form=form)

        # noinspection PyArgumentList
        _u = User(firstname=_fn, lastname=_ln, username=_un, hashword='', passphrase=_pp, email=_em,
                  affiliation=_af, created_iso=_iso, created_mjd=_mjd,
                  avatar=f"http://www.gravatar.com/avatar/{md5(_em.lower().encode('utf-8')).hexdigest()}",
                  about_me='', last_seen_iso=_iso, last_seen_mjd=_mjd, is_admin=False, is_disabled=True)
        _u.set_password(_pw)

        # update database
        try:
            db.session.add(_u)
            db.session.commit()
            msg_out(f'User {_un} registered OK', True, False)

            # send new user welcome email
            send_gmail_async(create_gmail(
                'Welcome to the ARTN Observation Request Portal',
                sender=ARTN_MAIL_USERNAME,
                recipients=[f'{_em}'],
                text_body=render_template('_new_user_registration.txt', user=_u),
                html_body=render_template('_new_user_registration.html', user=_u)))
            msg_out(f'Sent welcome email to {_em}', True, False)

            # send admin an email to confirm registration
            _token = _u.get_confirm_registration_token()
            send_gmail_async(create_gmail(
                f'Confirmation link for new user {_fn} {_ln}, {_af}, {_em}',
                sender=ARTN_MAIL_USERNAME,
                recipients=[ARTN_MAIL_USERNAME],
                text_body=render_template('_confirm_registration.txt', user=_u, token={_token}),
                html_body=render_template('_confirm_registration.html', user=_u, token={_token})))
            msg_out(f'Sent link email to {ARTN_MAIL_USERNAME}, token={_token}', True, False)

            # re-direct to register_ok page
            return render_template(
                'register_ok.html',
                incoming={'url': f'/orp/', 'text': f'Thanks, {_u.firstname}, for registering: please check your inbox'})

        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to register new user {_un}, error={_e}', True, False)
            return render_template('register.html', form=form)

    # return for GET
    return render_template('register.html', form=form)


# +
# route(s): /orp/reset_password/<token>
# -
@app.route('/orp/orp/reset_password/<token>', methods=['GET', 'POST'])
@app.route('/orp/reset_password/<token>', methods=['GET', 'POST'])
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def orp_reset_password(token=None):
    msg_out(f'/orp/reset_password/{token} entry', True, False)
    get_client_ip(request)

    # if we are logged in, re-direct
    if current_user.is_authenticated:
        return redirect(url_for('orp_user', username=current_user.username))

    # verify token
    _u = User.verify_reset_password_token(token)
    if _u is None:
        return redirect(url_for('orp_home'))

    # build form
    form = ResetPasswordForm()

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _pw = form.password.data.strip()

        # does it match the password rule?
        if re.match(ARTN_PASSWORD_RULE, f'{_pw}') is None:
            msg_out(f'ERROR: New password, {_pw}, does not conform to rules', True, True)
            return render_template('reset_password.html', form=form)

        # change password
        try:
            _u.set_password(_pw)
            db.session.commit()
            msg_out(f'User {_u.username} password has been changed', True, True)
            return redirect(url_for('orp_login'))
        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: User {_u.username} password has not been changed, error={_e}', True, True)

    # return
    return render_template('reset_password.html', form=form)


# +
# route(s): /orp/reset_password_request
# -
@app.route('/orp/orp/reset_password_request', methods=['GET', 'POST'])
@app.route('/orp/reset_password_request', methods=['GET', 'POST'])
@app.route('/reset_password_request', methods=['GET', 'POST'])
def orp_reset_password_request():
    msg_out(f'/orp/reset_password_request entry', True, False)
    get_client_ip(request)

    # if we are logged in, re-direct
    if current_user.is_authenticated:
        return redirect(url_for('orp_user', username=current_user.username))

    # build form
    form = ResetPasswordRequestForm()

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _em = form.email.data.strip()
        _pp = form.passphrase.data.strip()

        # find user
        _u = User.query.filter_by(email=_em).first_or_404()
        if _u is not None and _u.passphrase == _pp:

            # get a token and send it to the given email address
            _token = _u.get_reset_password_token()
            send_gmail_async(create_gmail(
                'ARTN ORP Reset Password Requested',
                sender=ARTN_MAIL_USERNAME,
                recipients=[f'{_em}', ARTN_MAIL_USERNAME],
                text_body=render_template('_reset_password_message.txt', user=_u, token=_token),
                html_body=render_template('_reset_password_message.html', user=_u, token=_token)))
            msg_out('Check your email for the instructions to reset your password', True, True)

            # re-direct to login page
            return redirect(url_for('orp_login'))

        else:
            _msg = f"Email '{_em}' or pass phrase '{_pp}' does not match our records!"
            msg_out(f'ERROR: {_msg}', True, True)
            return render_template('index.html', incoming={'url': f'/orp/reset_password_request', 'text': f'{_msg}'})

    # return for GET
    return render_template('reset_password_request.html', form=form)


# +
# route(s): /orp/show/<username>?dbid=<num>, requires login
# -
# noinspection PyPep8
@app.route('/orp/orp/show/<username>', methods=['GET', 'POST'])
@app.route('/orp/show/<username>', methods=['GET', 'POST'])
@app.route('/show/<username>', methods=['GET', 'POST'])
@login_required
def orp_show(username=''):
    msg_out(f'/orp/show/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # get dbid
    obsreqid = request.args.get('obsreqid', None)
    if obsreqid is None:
        msg_out(f'ERROR: Failed to get observation id {obsreqid}', True, True)
        return redirect(url_for('orp_view_requests', username=_u.username))

    return_page = request.args.get('return_page', 'orp_view_requests')

    _args = request.args.copy()
    try:
        _args.pop('return_page')
        _args.pop('obsreqid')
    except KeyError:
        pass
    arg_str = urlencode(_args)

    # get observation request
    _expired = None
    _now = iso_to_jd(get_date_time())
    _obsreq = ObsReq2.query.filter_by(id=obsreqid).first_or_404()
    if _obsreq:
        exposures = ObsExposure.query.filter_by(obsreqid=obsreqid).all()

        _obsreq.object_name = decode_verboten(_obsreq.object_name.strip(), ARTN_DECODE_DICT)
        _telescope = _obsreq.telescope.lower()
        _begin = iso_to_jd(_obsreq.begin_iso)
        _end = iso_to_jd(_obsreq.end_iso)
        if _begin < _now < _end:
            _expired = False
            msg_out(f'/orp/show/{username} creating airmass plot for {TEL__AKA[_telescope]}', True, False)
            msg_out(f'/orp/show/{username} airmass_plot(_ra={_obsreq.ra_deg:.2f}, _dec={_obsreq.dec_deg:.2f}, '
                    f'_date={jd_to_iso(_now)}, _ndays=1, _from_now=False)', True, False)
            # noinspection PyPep8
            _png = f'{TELESCOPES[_telescope].airmass_plot(_obsreq.ra_deg, _obsreq.dec_deg, jd_to_iso(_now), 1, False)}'
        else:
            _expired = True
            _png = ARTN_OBSERVATION_EXPIRED

        # show record
        if _u.is_admin or (_u.username.lower() == _obsreq.username.lower()):
            _format = request.args.get('?format', None)
            if _format is not None and _format.lower() == 'json':
                return jsonify(_obsreq.serialized())
            else:
                _format = request.args.get('format', None)
                if _format is not None and _format.lower() == 'json':
                    return jsonify(_obsreq.serialized())
                else:
                    return render_template('show.html', record=_obsreq, exposures=exposures, image=_png, expired=_expired, return_page=return_page, arg_str=arg_str)


# +
# route(s): /orp/telescopes/
# -
@app.route('/orp/orp/telescopes/')
@app.route('/orp/telescopes/')
@app.route('/telescopes/')
@login_required
def orp_telescopes():
    msg_out(f'/orp/telescopes/ entry', True, False)
    get_client_ip(request)

    # return data
    return jsonify({"telescopes": [TEL__NODES[_t] for _t in TEL__NODES]})


# +
# route(s): /orp/telescope/<name>, requires login
# -
@app.route('/orp/orp/telescope/<name>', methods=['GET', 'POST'])
@app.route('/orp/telescope/<name>', methods=['GET', 'POST'])
@app.route('/telescope/<name>', methods=['GET', 'POST'])
@login_required
def orp_telescope_name(name=''):
    msg_out(f'/orp/telescope/{name} entry', True, False)
    get_client_ip(request)

    # return data
    if name.lower() in TEL__NODES:
        return jsonify({'telescope': TEL__NODES[f'{name.lower()}']})
    else:
        return jsonify({})


# +
# route(s): /orp/update/<username>?dbid=<num>, requires login
# -
### +
### since the introduction is ObsReq2, this is broken??!!!
### -
@app.route('/orp/orp/update/<username>', methods=['GET', 'POST'])
@app.route('/orp/update/<username>', methods=['GET', 'POST'])
@app.route('/update/<username>', methods=['GET', 'POST'])
@login_required
def orp_update(username=''):
    msg_out(f'/orp/update/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # get dbid
    _dbid = request.args.get('dbid', None)
    if _dbid is None:
        msg_out(f'ERROR: Failed to get observation id {_dbid}', True, True)
        return redirect(url_for('orp_view_requests', username=_u.username))

    # get observation request
    _obsreq = ObsReq.query.filter_by(id=_dbid).first_or_404()

    # build form
    form = UpdateObsReqForm(telescope='Kuiper', instrument='Mont4k', user=_u.username)

    # GET method
    if request.method == 'GET':
        form.username.data = _obsreq.username
        form.priority.data = _obsreq.priority
        form.object_name.data = decode_verboten(_obsreq.object_name.strip(), ARTN_DECODE_DICT)
        form.ra_hms.data = _obsreq.ra_hms
        form.dec_dms.data = _obsreq.dec_dms
        form.begin_iso.data = _obsreq.begin_iso
        form.end_iso.data = _obsreq.end_iso
        form.airmass.data = float(_obsreq.airmass)
        form.lunarphase.data = _obsreq.lunarphase
        form.photometric.data = bool(_obsreq.photometric)
        form.guiding.data = bool(_obsreq.guiding)
        form.non_sidereal.data = bool(_obsreq.non_sidereal)
        form.ns_params.data = json.dumps(_obsreq.non_sidereal_json)
        form.filter_name.data = _obsreq.filter_name
        form.exp_time.data = float(_obsreq.exp_time)
        form.num_exp.data = int(_obsreq.num_exp)
        form.binning.data = _obsreq.binning
        form.dither.data = _obsreq.dither
        form.cadence.data = _obsreq.cadence
        form.telescope.data = _obsreq.telescope
        form.instrument.data = _obsreq.instrument
        return render_template('update_obsreq.html', form=form, dbid=_dbid)

    # validate form (POST request)
    if form.validate_on_submit():

        # update records
        _obsreq.username = _u.username
        _obsreq.object_name = encode_verboten(form.object_name.data.strip(), ARTN_ENCODE_DICT)
        _obsreq.ra_hms = form.ra_hms.data.strip()
        _obsreq.dec_dms = form.dec_dms.data.strip()
        _obsreq.begin_iso = form.begin_iso.data
        _obsreq.end_iso = form.end_iso.data
        _obsreq.airmass = form.airmass.data
        _obsreq.lunarphase = form.lunarphase.data.strip().lower()
        _obsreq.photometric = form.photometric.data
        _obsreq.guiding = form.guiding.data
        _obsreq.non_sidereal = form.non_sidereal.data
        _obsreq.filter_name = form.filter_name.data.strip()
        _obsreq.exp_time = form.exp_time.data
        _obsreq.num_exp = form.num_exp.data
        _obsreq.binning = form.binning.data.strip()
        _obsreq.dither = form.dither.data.strip()
        _obsreq.cadence = form.cadence.data.strip()
        _obsreq.telescope = form.telescope.data.strip()

        # validate telescope / instrument pair
        if f'{_obsreq.instrument}' not in ARTN_SUPPORTED_NODES[f'{_obsreq.telescope}']:
            return render_template('409.html', reason=f'Invalid telescope ({_obsreq.telescope}) and instrument '
                                                      f'({_obsreq.instrument}) combination!', caller='orp_update')

        # reset flags
        _obsreq.queued = False
        _obsreq.queued_iso = ARTN_ZERO_ISO
        _obsreq.queued_mjd = ARTN_ZERO_MJD
        _obsreq.completed = False
        _obsreq.completed_iso = ARTN_ZERO_ISO
        _obsreq.completed_mjd = ARTN_ZERO_MJD
        _obsreq.rts2_id = -1
        _obsreq.rts2_doc = '{}'

        # get json
        if _obsreq.non_sidereal:
            _str = form.ns_params.data
            _str_start = _str.find('{')
            _str_end = _str.rfind('}') + 1
            _json = f"{_str[_str_start:_str_end]}"
            msg_out(f"_json={_json}", True, True)
            if check_json(_json):
                _obsreq.non_sidereal_json = json.loads(_json)
            else:
                msg_out(f"ERROR: json not valid ... skipping", True, True)
                return redirect(url_for('orp_user', username=_u.username))
        else:
            _obsreq.non_sidereal_json = json.loads('{}')

        # munge the input(s) as required
        _old_priority_value = _obsreq.priority_value
        _old_priority = _obsreq.priority.strip().lower()
        _new_priority = form.priority.data.strip().lower()

        _priority_value = 0.0
        if _new_priority != _old_priority:
            if _new_priority == 'routine':
                _priority_value = _obsreq.created_mjd,
            elif _new_priority == 'urgent':
                created_iso = get_iso()
                created_mjd = iso_to_mjd(created_iso)
                _priority_value = -created_mjd if _obsreq.priority == 'urgent' else created_mjd
        _obsreq.priority_value = _priority_value
        _obsreq.priority = _new_priority

        _ra_hms = form.ra_hms.data.strip()
        _obsreq.ra_deg = ra_to_deg(_ra_hms)

        _dec_dms = form.dec_dms.data.strip()
        _obsreq.dec_deg = dec_to_deg(_dec_dms)
        if _obsreq.dec_deg > TEL__DEC__LIMIT[f'{_obsreq.telescope.lower()}']:
            msg_out(f"ERROR: requested declination {_obsreq.dec_deg:.3f} > {TEL__DEC__LIMIT[_obsreq.telescope.lower()]}"
                    f" limit for {_obsreq.telescope} telescope", True, True)
            return redirect(url_for('orp_user', username=_u.username))

        _begin_iso = form.begin_iso.data
        _begin_mjd = str(_begin_iso).replace(' ', 'T')
        _begin_mjd = f'{_begin_mjd}.000000'
        _begin_mjd = float(iso_to_mjd(_begin_mjd))
        _obsreq.begin_mjd = _begin_mjd

        _end_iso = form.end_iso.data
        _end_mjd = str(_end_iso).replace(' ', 'T')
        _end_mjd = f'{_end_mjd}.000000'
        _end_mjd = float(iso_to_mjd(_end_mjd))
        _obsreq.end_mjd = _end_mjd

        _sign = -1.0 if random.uniform(-1.0, 1.0) < 0.0 else 1.0
        if _obsreq.lunarphase == 'dark':
            _obsreq.moonphase = _sign * random.uniform(0.0, 5.5)
        elif _obsreq.lunarphase == 'grey':
            _obsreq.moonphase = _sign * random.uniform(5.5, 8.5)
        else:
            _obsreq.moonphase = _sign * random.uniform(8.5, 15.0)

        # update database
        try:
            db.session.commit()
            msg_out(f'Observation request {_dbid} has been updated', True, True)
        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to update observation request {_dbid} changes, error={_e}', True, True)

        return redirect(url_for('orp_user', username=_u.username))

    else:
        for _e in form.errors:
            msg_out(f'ERROR: invalid value {form.errors[_e][0]}', True, False)

    # return for GET
    return render_template('update_obsreq.html', form=form, dbid=_dbid)


# +
# route(s): /orp/upload/<username>, requires login
# -
@app.route('/orp/orp/upload/<username>', methods=['GET', 'POST'])
@app.route('/orp/upload/<username>', methods=['GET', 'POST'])
@app.route('/upload/<username>', methods=['GET', 'POST'])
@login_required
def orp_upload(username=''):
    msg_out(f'/orp/upload/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # build form
    form = UploadForm()

    # validate form (POST request)
    if form.validate_on_submit():

        # get data
        _fn = form.filename.data

        # upload
        filename = secure_filename(_fn.filename)
        pathname = os.path.join(app.instance_path, 'files', f'{_u.username}_{filename}')
        _fn.save(pathname)
        
        #try:
        #validate opening jsonfile
        filedata = json.loads(open(pathname).read())
        for obs in filedata:
            #validate each obsreq
            obsreq, validator, isvalid  = ObsReq2.validate_json(obs, _u)
            if isvalid:
                #if it is deemed valid, look for the exposures in the keys
                if 'exposures' in obs.keys() and len(obs['exposures']):
                    #add and flush to get obsreqid
                    db.session.add(obsreq)
                    db.session.flush()
                    exps = obs['exposures']
                    #loop over each obsexp and test their validity
                    for e in exps:
                        e['obsreqid'] = obsreq.id
                        obsexp, validator, isvalid = ObsExposure.validate_json(e)
                        if isvalid:
                            db.session.add(obsexp)
                        else:
                            msg_out(f'Error: Invalid Observation Request: {obsexp.serialized()}')
                            msg_out(f'Errors: {json.dumps(validator.errors)}')
                            return redirect(url_for('orp_upload', username=current_user.username))
                #No exposures
                else:
                    msg_out(f'Error: Invalid Observation Request: {json.dumps(obs)}')
                    msg_out(f'Errors: list of \'exposures\' is required')
                    return redirect(url_for('orp_upload', username=current_user.username))
            #Invalid Observation request
            else:
                msg_out(f'Error: Invalid Observation Request: {json.dumps(obs)}')
                msg_out(f'Errors: {json.dumps(validator.errors)}')
                return redirect(url_for('orp_upload', username=current_user.username))
        #Everything is Kosher, submit to database and return
        db.session.commit()
        msg_out(f'Successfully uploaded file', True, True)
        return redirect(url_for('orp_view_requests', username=current_user.username))

        #except:
        #    msg_out(f'ERROR: Input file has invalid format, please check {filename}', True, True)
        #    return redirect(url_for('orp_view_requests', username=current_user.username))


        # check file is valid
        #_num, _columns = check_upload_format(pathname)
        #if _num < 0 or _columns is {}:
        #    msg_out(f'ERROR: Input file has invalid format, please check {filename}', True, True)
        #    return redirect(url_for('orp_view_requests', username=current_user.username))

        # if number of lines < 100, upload synchronously otherwise use a thread
        #if _num < 100:
        #    msg_out(f'Input file has {_num} records, loading synchronously', True, True)
        #    upload_file(_columns, _num, _u)
        #else:
        #    msg_out(f'Input file has {_num} records, loading asynchronously', True, True)
        #    upload_file_async(_columns, _num, _u)

        # return to view requests
        return redirect(url_for('orp_view_requests', username=current_user.username))

    # return for GET
    return render_template('upload.html', form=form)


# +
# route(s): /orp/user/<username>, requires login
# -
@app.route('/orp/orp/user/<username>')
@app.route('/orp/user/<username>')
@app.route('/user/<username>')
@login_required
def orp_user(username=''):
    msg_out(f'/orp/user/{username} entry', True, False)
    get_client_ip(request)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=_u)


# +
# route(s): /orp/version/
# -
@app.route('/orp/orp/version/', methods=['GET'])
@app.route('/orp/version/', methods=['GET'])
@app.route('/version/', methods=['GET'])
def orp_version():
    get_client_ip(request)
    return render_template('version.html', msg=f'{HISTORY_HTML}'), 200


# +
# route(s): /orp/view_observable/<username>, requires login
# -
@app.route('/orp/orp/view_observable/<username>', methods=['GET', 'POST'])
@app.route('/orp/view_observable/<username>', methods=['GET', 'POST'])
@app.route('/view_observable/<username>', methods=['GET', 'POST'])
@login_required
def orp_view_observable(username=''):
    msg_out(f'/orp/view_observable/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()
    msg_out(f'/orp/view_observable/{username} _u.username={_u.username}', True, False)

    # set default(s)
    page = request.args.get('page', 1, type=int)
    response = {}
    paginator = None

    # GET request
    if request.method == 'GET':
        query = db.session.query(ObsReq2)
        msg_out(f'/orp/view_observable/{username} request.args={request.args}', True, False)
        _now = float(iso_to_mjd(get_date_time()))

        if _u.is_admin:
            _filter = {'begin_mjd__lte': f"{_now}", 'end_mjd__gte': f"{_now}", 'username': f''}
        else:
            _filter = {'begin_mjd__lte': f"{_now}", 'end_mjd__gte': f"{_now}", 'username': f'{_u.username}'}
        msg_out(f'/orp/view_observable/{username} _filter={_filter}', True, False)
        query = obsreq2_filters(query, _filter)

        # request by sort_field / sort_order
        _sf = request.args.get('sort_field')
        _so = request.args.get('sort_order')
        if (_sf is None or _sf == '') and (_so is None or _so == ''):
            query = obsreq2_filters(query, {"sort_field": "id", "sort_order": "descending"})

        query = obsreq2_filters(query, request.args)
        paginator = query.paginate(page, ARTN_RESULTS_PER_PAGE, True)
        response = {
            'total': paginator.total,
            'pages': paginator.pages,
            'has_next': paginator.has_next,
            'has_prev': paginator.has_prev,
            'results': ObsReq.serialize_list(paginator.items)
        }

    # POST request
    if request.method == 'POST':

        # get search criteria
        searches = request.get_json().get('queries')
        msg_out(f'/orp/view_observable/{username} searches={searches}', True, False)

        # initialize output(s)
        search_results = []
        total = 0

        # iterate over searches
        for search_args in searches:
            search_result = {}
            query = db.session.query(ObsReq2)
            query = obsreq2_filters(query, search_args)
            search_result['query'] = search_args
            search_result['num_requests'] = query.count()
            search_result['results'] = ObsReq.serialize_list(query.all())
            search_results.append(search_result)
            total += search_result['num_requests']

        # set response dictionary
        response = {
            'total': total,
            'results': search_results
        }

    # add avatars to response dictionary
    # msg_out(f'response={response}', True, False)
    for _e in response['results']:
        _tu = User.query.filter_by(username=_e['username']).first()
        _e['avatar'] = _e['username'] if _tu is None else _tu.get_avatar(16)
        _e['object_name'] = decode_verboten(_e['object_name'], ARTN_DECODE_DICT)

    # return response in desired format
    if request_wants_json() or request.method == 'POST':
        return jsonify(response)
    else:
        _args = request.args.copy()
        try:
            _args.pop('page')
        except KeyError:
            pass
        arg_str = urlencode(_args)
        return render_template('view_observable.html', context=response, page=paginator.page, arg_str=arg_str, )


# +
# route(s): /orp/view_users/, requires login
# -
@app.route('/orp/orp/view_users/', methods=['GET', 'POST'])
@app.route('/orp/view_users/', methods=['GET', 'POST'])
@app.route('/view_users/', methods=['GET', 'POST'])
@login_required
def orp_view_users():
    msg_out(f'/orp/view_users/ entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _user = request.args.get('username', '')
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=_user).first_or_404()

    # get history
    if not _u.is_admin:
        msg_out(f'ERROR: you do not have permission for this operation', True, True)
        return render_template('401.html')

    # get result(s)
    query = db.session.query(User)
    query = user_filters(query, request.args)
    query = query.order_by(User.id.desc())

    # create output 
    return render_template('view_users.html', user=[_e for _e in User.serialize_list(query.all())])


# +
# route(s): /orp/view_requests/<username>, requires login
# -
@app.route('/orp/orp/view_requests/<username>', methods=['GET', 'POST'])
@app.route('/orp/view_requests/<username>', methods=['GET', 'POST'])
@app.route('/view_requests/<username>', methods=['GET', 'POST'])
@login_required
def orp_view_requests(username=''):
    msg_out(f'/orp/view_requests/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()
    msg_out(f'/orp/view_requests/{username} _u.username={_u.username}', True, False)

    # set default(s)
    page = request.args.get('page', 1, type=int)
    response = {}
    paginator = None

    # GET request
    if request.method == 'GET':
        #query = db.session.query(ObsReq)
        query = db.session.query(ObsReq2)
        msg_out(f'/orp/view_requests/{username} entry request.args={request.args}', True, False)

        # request by username
        if _u.is_admin:
            #query = obsreq_filters(query, {"username": f""})
            query = obsreq2_filters(query, {"username": f""})
        else:
            #query = obsreq_filters(query, {"username": f"{_u.username}"})
            query = obsreq2_filters(query, {"username": f"{_u.username}"})

        # request by sort_field / sort_order
        _sf = request.args.get('sort_field')
        _so = request.args.get('sort_order')
        if (_sf is None or _sf == '') and (_so is None or _so == ''):
            #query = obsreq_filters(query, {"sort_field": "id", "sort_order": "descending"})
            query = obsreq2_filters(query, {"sort_field": "id", "sort_order": "descending"})

        # request by everything else
        #query = obsreq_filters(query, request.args)
        query = obsreq2_filters(query, request.args)
        paginator = query.paginate(page, ARTN_RESULTS_PER_PAGE, True)
        response = {
            'total': paginator.total,
            'pages': paginator.pages,
            'has_next': paginator.has_next,
            'has_prev': paginator.has_prev,
            'results': ObsReq2.serialize_list(paginator.items)
        }

    # POST request
    if request.method == 'POST':

        # get search criteria
        searches = request.get_json().get('queries')
        msg_out(f'/orp/view_requests/{username} entry searches={searches}', True, False)

        # initialize output(s)
        search_results = []
        total = 0

        # iterate over searches
        for search_args in searches:
            search_result = {}
            query = db.session.query(ObsReq2)
            query = obsreq2_filters(query, search_args)
            search_result['query'] = search_args
            search_result['num_requests'] = query.count()
            search_result['results'] = ObsReq2.serialize_list(query.all())
            search_results.append(search_result)
            total += search_result['num_requests']

        # set response dictionary
        response = {
            'total': total,
            'results': search_results
        }

    # add avatars to response dictionary
    # msg_out(f'response={response}', True, False)
    for _e in response['results']:
        _tu = User.query.filter_by(username=_e['username']).first()
        _e['avatar'] = _e['username'] if _tu is None else _tu.get_avatar(16)
        _e['object_name'] = decode_verboten(_e['object_name'], ARTN_DECODE_DICT)

    # return response in desired format
    if request_wants_json() or request.method == 'POST':
        return jsonify(response)
    else:
        _args = request.args.copy()
        try:
            _args.pop('page')
        except KeyError:
            pass
        arg_str = urlencode(_args)
        return render_template('view_requests.html', context=response, page=paginator.page, arg_str=arg_str)


# +
# route(s): /orp/manage_queue/<username>, requires login + admin
# -
@app.route('/orp/orp/manage_queue/<username>', methods=['GET', 'POST'])
@app.route('/orp/manage_queue/<username>', methods=['GET', 'POST'])
@app.route('/manage_queue/<username>', methods=['GET', 'POST'])
@login_required
def orp_manage_queue(username='', telescope='Kuiper'):
    msg_out(f'/orp/view_queue/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    #What do I want on this page
    #I want it to find the current date
    #query for all queued obsreqs that are around this date
    #display them
    #have multiple buttons on the page
    #   schedule the queue
    #       display a verbose log
    #       if something never gets scheduled in the queue mark it red in the queue table. 
    #   submit the queue (this actually sets 'scheduled=True')

    #the objects can be displayed with the rough group by and an expandable + to view the individual observation info
    #have it display the airmass chart (javascript)
    #encorporate a 'scheduled' boolean with a scheduled date iso bullshit (same thing as above)
    #this is going to be a lot.

    date_list = []
    n1 = datetime.datetime.now()
    d1 = datetime.datetime(n1.year, n1.month, n1.day)

    delta = n1 - d1
    delta_hours = delta.seconds//3600
    if delta_hours < 5:
        d1 = d1-datetime.timedelta(days=1)

    for td in range(30):
        date_deltad = d1-datetime.timedelta(days=td)
        date_formatted = date_deltad.strftime("%Y-%m-%d")
        date_list.append(date_formatted)

    return render_template('manage_queue.html', dates=date_list, telescope=telescope, username=username)

# +
# route(s): /orp/manage_queue/<username>, requires login + admin
# -
@app.route('/orp/orp/view_current_queue/<username>', methods=['GET', 'POST'])
@app.route('/orp/view_current_queue/<username>', methods=['GET', 'POST'])
@app.route('/view_current_queue/<username>', methods=['GET', 'POST'])
@login_required
def orp_view_current_queue(username='', telescope='Kuiper'):
    msg_out(f'/orp/view_current_queue/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    telescope = request.args.get('telescope')
    view_current = request.args.get('current', False)
    currentqueue = getCurrentQueue(telescope=telescope)

    communicator = rts2comm()
    rts2all = communicator._getall()
    rts2_sel_values = rts2all['SEL']['d']
    
    executed_ids = rts2_sel_values['plan_executed_ids'][1] #list of ids
    current_id = rts2_sel_values['current_target'][1] #just the id
    plan_ids = rts2_sel_values['plan_ids'][1] #list of ids

    executed_ids = [x for x in executed_ids if x not in [current_id]]

    total_rts2ids = []
    total_rts2ids.extend(executed_ids)
    total_rts2ids.extend([current_id])
    total_rts2ids.extend(plan_ids)

    currently_submitted_queue = len(total_rts2ids) > 0

    queuenight = datetime.datetime.now()
    if queuenight.hour < 8:
        queuenight += datetime.timedelta(days=-1)
    queuenight_str = queuenight.strftime("%Y-%m-%d")

    #queued_iso_begin = datetime.datetime.now() - datetime.timedelta(days=30)
    #submitted_queues = NightlyQueue.query.filter(NightlyQueue.queued_iso > queued_iso_begin).all()
    #date_list = list(sorted([x.night for x in submitted_queues], reverse=True))



    if currently_submitted_queue:
        '''
            plan_executed_ids -> [1] rts2_ids of executed exposures
            plan_executed_names -> [1] database names of executed exposures 
            plan_ids -> [1] rts2_ids of targets in queue
            current_target -> [1] rts2_id of current target
            plan_ids -> [1] rts2_ids of targets in queue
            next_id -> [1] rts2_id of next target
        '''

        
        around_dates = [
            (datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            datetime.datetime.now().strftime("%Y-%m-%d"),
            (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        ]
        
        obsreqs = ObsReq2.query.filter(ObsReq2.rts2_id.in_(total_rts2ids)).all()
        total_obsreqids = [x.id for x in obsreqs]
        executed_ids = [str(e) for e in executed_ids if e in total_obsreqids]
        obsreqexps = ObsExposure.query.filter(ObsExposure.obsreqid.in_(total_obsreqids)).all()

        obsreqs_dict = {}
        for o in obsreqs:
            obsexps = [x for x in obsreqexps if x.obsreqid == o.id]
            status = None
            if o.rts2_id in executed_ids:
                status = 'executed'
            if o.rts2_id in plan_ids:
                status = 'planned'
            if o.rts2_id == current_id:
                status = 'current'
            
            obsreqs_dict[o.rts2_id] = o.serialized(queuedonly=True)

        return render_template('view_current_queue.html', queuenight=queuenight_str, active=True, queuelist=obsreqs_dict, executed=executed_ids, planned_ids=plan_ids, current_id=[current_id], telescope=telescope, username=username)
    return render_template('view_current_queue.html', active=False, queuenight=queuenight_str)


@app.route('/orp/orp/ajax_current_queued_list')
@app.route('/orp/ajax_current_queued_list')
@app.route('/ajax_current_queued_list')
def current_queued_list():
    
    expids = []
    page = 0
    num_items = 10
    username = request.args.get('username')
    expids_string = request.args.get('expids')
    if expids_string is not None and expids_string is not '':
        for r in expids_string.split(','):
            expids.append(int(r))
    
    communicator = rts2comm()
    rts2all = communicator._getall()
    rts2_sel_values = rts2all['SEL']['d']
    
    executed_ids = rts2_sel_values['plan_executed_ids'][1] #list of ids
    current_id = rts2_sel_values['current_target'][1] #just the id
    plan_ids = rts2_sel_values['plan_ids'][1] #list of ids

    executed_ids = [x for x in executed_ids if x not in [current_id]]

    total_rts2ids = []
    total_rts2ids.extend(executed_ids)
    total_rts2ids.extend([current_id])
    total_rts2ids.extend(plan_ids)

    around_dates = [
        (datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        datetime.datetime.now().strftime("%Y-%m-%d"),
        (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    ]
    
    obsreqs = ObsReq2.query.filter(ObsReq2.rts2_id.in_(total_rts2ids)).all()
    total_obsreqids = [x.id for x in obsreqs]
    total_obsreq_rts2ids = [x.rts2_id for x in obsreqs]
    #executed_ids = list(set([e for e in executed_ids if e in total_obsreq_rts2ids]))
    obsreqexps = ObsExposure.query.filter(ObsExposure.obsreqid.in_(total_obsreqids)).all()

    obsreqs_dict = {}
    for o in obsreqs:
        obsexps = [x for x in obsreqexps if x.obsreqid == o.id]
        status = None
        if o.rts2_id in executed_ids:
            status = 'executed'
        if o.rts2_id in plan_ids:
            status = 'planned'
        if o.rts2_id == current_id:
            status = 'current'

        obsreqs_dict[o.rts2_id] = o.serialized(queuedonly=True)

    html = '''
    <table class="table table-striped table-lg">
        <thead>
            <tr>
                <th><font color="blue">Exp Info</font></th>
                <th><font color="blue">Object</font></th>
                <th><font color="blue">RA</font></th>
                <th><font color="blue">Dec</font></th>
                <th><font color="blue">Start (est)</font></th>
                <th><font color="blue">End (est)</font></th>
                <th><font color="blue">Overhead</font></th>
                <th><font color="blue">Status(%)</font></th>
                <th><font color="blue">Requeue Request</font></th>
            </tr>
            <tr>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center>J2k &deg;</center></font></th>
                <th><font color="grey"><center>J2k &deg;</center></font></th>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center> </center></font></th>
            </tr>
        </thead>
        <tbody>
    '''

    html += get_current_queue_table(executed_ids, obsreqs_dict, 'table-success', expids, username)
    html += get_current_queue_table([current_id], obsreqs_dict, 'table-primary', expids, username)
    html += get_current_queue_table(plan_ids, obsreqs_dict, 'table-warning', expids, username)

    html += '''
        </tbody>
    </table>
    '''

    payload = {
        'qt_html':html
    }

    return payload


@app.route('/orp/orp/ajax_bigartn_queue')
@app.route('/orp/ajax_bigartn_queue')
@app.route('/ajax_bigartn_queue')
def bigartn_queue_query():
    telescope = request.args.get('telescope')
    
    canInterrupt = len(getCurrentQueue(telescope=telescope)) > 0

    if canInterrupt:
        html = "<b><font color='red'>There is a queue already submitted. Re-Submitting will overwrite/interrupt the queue</font></b>"
    else:
        html = ""

    payload = {
        "canInterrupt" : canInterrupt,
        "canCommunicate" : True,
        "html" : html
    }

    return payload


@app.route('/orp/orp/ajax_queued_list')
@app.route('/orp/ajax_queued_list')
@app.route('/ajax_queued_list')
def queued_list_query(night=None, completed=False, day_buffer=1):
    
    expids = []
    page = 0
    num_items = 10
    username = request.args.get('username')
    if night is None:
        night = request.args.get('night')
        night = datetime.datetime.strptime(night, "%Y-%m-%d")
    
        completed = request.args.get('completed')
        day_buffer = request.args.get('day_buffer')
        try:
            day_buffer = int(day_buffer)
        except:
            day_buffer = 1
        
        expids_string = request.args.get('expids')
        if expids_string is not None and expids_string is not '':
            for r in expids_string.split(','):
                expids.append(int(r))

        page = request.args.get('page')
        page = int(page) if page is not None else 0

        name_query = request.args.get('name_query')

    skip = page*num_items
    take = skip+num_items

    queued_iso_begin = datetime.datetime.now() - datetime.timedelta(days=day_buffer)
    queued_iso_end = datetime.datetime.now() + datetime.timedelta(days=1)

    query_filter = [
        ObsReq2.completed == False,
        ObsReq2.queued == True,
        ObsReq2.queued_iso > queued_iso_begin,
        ObsReq2.queued_iso < queued_iso_end
    ]

    if name_query is not None and name_query != '':
        query_filter.append(ObsReq2.object_name.contains(name_query))

    obsreqs = ObsReq2.query.filter(*query_filter).order_by(
        ObsReq2.ra_hms
    ).all()

    obsreqids = [x.id for x in obsreqs]

    exposures = ObsExposure.query.filter(ObsExposure.obsreqid.in_(obsreqids)).all()

    targets = format_orp_targets(obsreqs, exposures)
    targets = sorted(targets, key=attrgetter('ra'))

    num_pages = int(len(targets)/num_items)
    if len(targets) % num_items != 0:
        num_pages += 1

    html = '''
    <table class="table table-striped table-lg">
        <thead>
            <tr>
                <th><font color="blue">Exp Info</font></th>
                <th><font color="blue">Object</font></th>
                <th><font color="blue">RA</font></th>
                <th><font color="blue">Dec</font></th>
                <th><input id='checkalltargs' type=checkbox onclick="doEmAll(this.id)"><font color="blue"> Queue (all exps)</font></th>
            </tr>
            <tr>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center> </center></font></th>
                <th><font color="grey"><center>J2k &deg;</center></font></th>
                <th><font color="grey"><center>J2k &deg;</center></font></th>
                <th><font color="grey"><center> </center></font></th>
            </tr>
        </thead>
    <tbody>
    '''

    for t in targets[skip:take]:
        t_expids = [x.expid for x in t.exp_objs]
        allchecked = ' checked' if all([tid in expids for tid in t_expids]) else ''

        nameid = t.name
        if '+' in t.name:
            nameid = t.name.replace('+', '')

        html += '''
        <tr>
            <td><button id="collbtn{}" onclick="changeCollapseButtonText(this.id)" type="button" class="btn btn-primary btn-xs arrow-right" data-toggle="collapse" data-target="#collapse{}"></button></td>
            <td><a href="/orp/obsreq2/{}?obsreqid={}&return_page=orp_manage_queue">{}</a></td>
            <td>{}</td>
            <td>{}</td>
            <td><input id="queuetarg_{}" type="checkbox" onclick="objectCheckAll(this.id)"{}></td>
        </tr>
        '''.format(nameid,nameid,username,t.id,t.name,t.ra,t.dec, nameid, allchecked)
        html+= '''
        <tr class="collapse" id="collapse{}">
            <td colspan="999">
                <div>
                    <table class="table table-striped table-sm">
                        <thead>
                            <tr>
                                <td><font color='blue'>Filter</font></td>
                                <td><font color='blue'>Exptime (s)</font></td>
                                <td><font color='blue'>Num Exp</font></td>
                                <td><font color='blue'>Queue</font><td>
                            </tr>
                        </thead>
                        <tbody>
        '''.format(nameid)
        #href="{{ url_for('orp_update') }}?dbid={}"
        for obsinfo in t.exp_objs:
            thischecked = ' checked' if obsinfo.expid in expids else ''
            html+='''
                                <tr>
                                    <td>{}</td>
                                    <td>{}</td>
                                    <td>{}</td>
                                    <td><input value="{}" id="{}_{}" type="checkbox" onclick="expCheckOne(this.id)"{}></td>
                                </tr>
            '''.format(obsinfo.filter, obsinfo.exptime, obsinfo.amount, obsinfo.expid, nameid, obsinfo.expid, thischecked)
        html += '''
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
        '''
    html+='''
        </tbody>
    </table>
     <div class="row">
      <div class="col">
       <div align="left">
    '''
    if page != 0:
        prevpage = page-1
        html+='<a onclick="paginateTargetsTable({})" class="btn btn-outline-secondary">Prev</a>'.format(prevpage)
    else:
        html+='<a href="#" class="btn btn-outline-secondary disabled">Prev</a>'
    html += '''
       </div>
      </div>

      <div class="col-md-8">
       <div align="center">
        {} record(s) found. Showing page {} / {}.
       </div>
      </div>

      <div class="col">
       <div align="right">
    '''.format(len(targets),page+1,num_pages)
    if page != num_pages-1:
        nextpage = page+1
        html+='<a onclick="paginateTargetsTable({})" class="btn btn-outline-secondary">Next</a>'.format(nextpage)
    else:
        html+='<a href="#" class="btn btn-outline-secondary disabled">Next</a>'
    html+='''
       </div>
      </div>
     </div>
    '''

    payload = {
        'qt_html':html
    }

    return payload


@app.route('/orp/orp/ajax_run_scheduler')
@app.route('/orp/ajax_run_scheduler')
@app.route('/ajax_run_scheduler')
def run_artn_scheduler():

    '''
    Idea for interrupt:
        if there is a current queue running
            make the checkbox undisabled
        if interrupt is True
            read in the current queue rts2 ids
            add the interrupt target as well
            rerun the queue and make the obstime and frames cooperate
    '''

    exposureids = []
    exposureids_string = request.args.get('expids')

    schedule_focus = True if request.args.get('schedule_focus') == 'true' else False
    interrupt = True if request.args.get('interrupt') == 'true' else False
    simulate = True if request.args.get('simulate') == 'true' else False

    nightstr = request.args.get('night')
    night = datetime.datetime.strptime(nightstr, "%Y-%m-%d")

    telescope = request.args.get('telescope')

    if exposureids_string != '':
        for r in exposureids_string.split(','):
            exposureids.append(int(r))

    if interrupt:
        q = getCurrentQueue(telescope=telescope)
        rts2ids = [x.id for x in q]
        interruptable_obsrqsids = db.session.query(ObsReq2.id).filter(
            ObsReq2.rts2_id.in_(rts2ids)
        ).all()

        inter_obsreqids = [x.id for x in interruptable_obsrqsids]

        interruptable_expids = db.session.query(ObsExposure.id).filter(
            ObsExposure.obsreqid.in_(inter_obsreqids),
            ObsExposure.completed == False,
            ObsExposure.queued == True,
        ).all()

        exposureids.extend([x.id for x in interruptable_expids])
        exposureids = list(set(exposureids))

    scheduled_exposures = db.session.query(ObsExposure).filter(
        ObsExposure.id.in_(exposureids)
    ).all()

    obsreqsids = list(set([x.obsreqid for x in scheduled_exposures]))

    obsreqs = db.session.query(ObsReq2).filter(
        ObsReq2.id.in_(obsreqsids)
    ).all()

    targets = format_orp_targets(obsreqs, scheduled_exposures)

    big2 = astropy.coordinates.EarthLocation.of_site('mtbigelow')

    scheduler = ARTNScheduler(targets, big2, night, schedule_focus, simulate)

    scheduler.run()
    scheduler.logdump()
    scheduler.plot()

    log_html = scheduler.html_log
    chart_html = f"<img src='data:image/png;base64,{scheduler.encoded_chart}'/>"

    payload = {
        'chart':chart_html,
        'log':log_html
    }

    return make_response(payload, 200)


@app.route('/orp/orp/ajax_populate_queue')
@app.route('/orp/ajax_populate_queue')
@app.route('/ajax_populate_queue')
def populate_queue():
    exposureids = []
    exposureids_string = request.args.get('expids')

    telescope = request.args.get('telescope')
    schedule_focus = True if request.args.get('schedule_focus') == 'true' else False
    interrupt = True if request.args.get('interrupt') == 'true' else False
    simulate = True if request.args.get('simulate') == 'true' else False
    queue_type = int(request.args.get('queue_type'))

    nightstr = request.args.get('night')
    night = datetime.datetime.strptime(nightstr, "%Y-%m-%d")
    
    if exposureids_string != '':
        for r in exposureids_string.split(','):
            exposureids.append(int(r))

    if interrupt:
        q = getCurrentQueue(telescope=telescope)
        rts2ids = [x.id for x in q]
        interruptable_obsrqsids = db.session.query(ObsReq2.id).filter(
            ObsReq2.rts2_id.in_(rts2ids)
        ).all()

        inter_obsreqids = [x.id for x in interruptable_obsrqsids]

        interruptable_expids = db.session.query(ObsExposure.id).filter(
            ObsExposure.obsreqid.in_(inter_obsreqids),
            ObsExposure.completed == False,
            ObsExposure.queued == True,
        ).all()

        exposureids.extend([x.id for x in interruptable_expids])
        exposureids = list(set(exposureids))

    scheduled_exposures = db.session.query(ObsExposure).filter(
        ObsExposure.id.in_(exposureids)
    ).all()

    obsreqsids = list(set([x.obsreqid for x in scheduled_exposures]))

    obsreqs = db.session.query(ObsReq2).filter(
        ObsReq2.id.in_(obsreqsids)
    ).all()

    targets = format_orp_targets(obsreqs, scheduled_exposures)

    if telescope == 'Kuiper':
        big2 = astropy.coordinates.EarthLocation.of_site('mtbigelow')

        scheduler = ARTNScheduler(targets, big2, night, schedule_focus, simulate, queue_type)

        scheduler.run()
        scheduler.logdump()
        
        #try:
        success = scheduler.submit_queue()
        if success:

            db_nightlyqueue = NightlyQueue(
                night = nightstr,
                telescope = telescope,
                submitted = True,
                interrupt = interrupt,
                queuetype = queue_type,
            )
            db.session.add(db_nightlyqueue)
            db.session.flush()

            for targ in scheduler.scheduled_targets:
                db_nightlyqueueobj = NightlyQueueExposure(
                    nightlyqueueid = db_nightlyqueue.id,
                    queueorder = targ.order,
                    obsreqid = targ.id,
                    rts2_id = targ.rts2id,
                    overhead = targ.overhead,
                    starttime = targ.db_starttime,
                    endtime = targ.db_endtime,
                    rts2start_t = targ.rts2start_t,
                    rts2end_t = targ.rts2end_t,
                    schedule_log = targ.db_log,
                )
                db.session.add(db_nightlyqueueobj)

            payload = {
                'message':'Success'
            }

            for se in scheduled_exposures:
                se.completed = False
                se.queued = True
            db.session.flush()

            for obsr in obsreqs:
                obsr.stellar_dictify()
            db.session.commit()
        else:
            payload = {
                'message':'Error in submitting to RTS2'
            }
        
        #except:
        #    payload = {
        #        'message':'Error in submitting to RTS2'
        #    }
    else:
        payload = {
            'message':'Telescope Queue system not yet implemented'
        }

    return make_response(payload, 200)


@app.route('/orp/orp/ajax_tnsloadtarget')
@app.route('/orp/ajax_tnsloadtarget')
@app.route('/ajax_tnsloadtarget')
def tnsloadtarget():
    args = request.args
    tns_name = args.get('tnsname')
    
    prefix = ''
    if 'SN' in tns_name:
        search_tns = tns_name.split('SN')[1]
        prefix='SN'
    else:
        search_tns = tns_name

    keywords = {
        'format':'json',
        'tns_name':search_tns
    }

    base = 'https://sassy.as.arizona.edu/sassy'
    target = 'tns_q3c'
    url = '{}/{}/?{}'.format(base, target, urlencode(keywords))
    r = requests.get(url)
    payload = {}
    if r.status_code == 200:
        returns = json.loads(r.text)['total']
        package = json.loads(r.text)['results']
        if returns > 0:

            targ = package[0]
            if 'AT' in targ['tns_name']:
                n = targ['tns_name']
                _n = prefix+n.split('AT ')[1]
            else:
                _n = prefix+targ['tns_name']

            #dd = targ['discovery_date']
            #if 'GMT' in dd:
            #	_dd = datetime.datetime.strptime(dd, '%a, %d %b %Y %H:%M:%S GMT')
            #	_dd = _dd.strftime('%Y-%m-%dT%H:%M:%S.%f')
            #else:
            #	try:
            #		_dd = datetime.datetime.strptime(dd, '%Y-%m-%dT%H:%M:%S.%f')
            #	except:
            #		pass

            payload = {
                'ra':ra_to_hms(float(targ['ra'])),
                'dec':dec_to_dms(float(targ['dec'])),
                'name':_n
            }
    return jsonify(payload)


@app.route('/orp/orp/obsreq2/<username>', methods=['GET', 'POST'])
@app.route('/orp/obsreq2/<username>', methods=['GET', 'POST'])
@app.route('/obsreq2/<username>', methods=['GET', 'POST'])
@login_required
def orp_obsreq2(username=''):
    
    '''
        Things to do:
            be able to save multiple exposures on obsreq page X
            be able view multiple exposures on obsreq page X
            be able to edit multiple exposures on obsreq page X

            data conversion for current database. 

            be able to submit obsreq with multiple exposures to rts2
    '''

    msg_out(f'/orp/obsreq2/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    # build form
    form = ObsReqForm(telescope='Kuiper', instrument='Mont4k', user=_u.username)
    page_form = request.form
    obsreqid = request.args.get('obsreqid', None)
    return_page = request.args.get('return_page', 'orp_view_requests')

    _args = request.args.copy()
    print(_args)
    try:
        _args.pop('obsreqid')
        _args.pop('page')
    except KeyError:
        pass
    arg_str = urlencode(_args)

	#test to load page
    if obsreqid and request.method != 'POST':

        _obsreq = ObsReq2.query.filter_by(id=obsreqid).first_or_404()

        form.username.data = _obsreq.username
        form.priority.data = _obsreq.priority
        form.object_name.data = decode_verboten(_obsreq.object_name.strip(), ARTN_DECODE_DICT)
        form.ra_hms.data = _obsreq.ra_hms
        form.dec_dms.data = _obsreq.dec_dms
        form.begin_iso.data = _obsreq.begin_iso
        form.end_iso.data = _obsreq.end_iso
        form.airmass.data = float(_obsreq.airmass)
        form.lunarphase.data = _obsreq.lunarphase
        form.photometric.data = bool(_obsreq.photometric)
        form.guiding.data = bool(_obsreq.guiding)
        form.non_sidereal.data = bool(_obsreq.non_sidereal)
        form.ns_params.data = json.dumps(_obsreq.non_sidereal_json)
        form.telescope.data = _obsreq.telescope
        form.instrument.data = _obsreq.instrument
        form.binning.data = _obsreq.binning
        form.dither.data = _obsreq.dither
        form.cadence.data = _obsreq.cadence
        form.priority.data = _obsreq.priority
        
        exposures = db.session.query(ObsExposure).filter(ObsExposure.obsreqid == obsreqid).all()

        return render_template('obsreq2.html', form=form, exposures=exposures, fresh=False, obsreqid=_obsreq.id, arg_str=arg_str, return_page=return_page)

	#test if new save
    if obsreqid is None and form.validate_on_submit():
         # get data
        _priority = form.priority.data.strip().lower()
        _object_name = encode_verboten(form.object_name.data.strip(), ARTN_ENCODE_DICT)
        _ra_hms = form.ra_hms.data.strip()
        _dec_dms = form.dec_dms.data.strip()
        _begin_iso = form.begin_iso.data
        _end_iso = form.end_iso.data
        _airmass = form.airmass.data
        _lunarphase = form.lunarphase.data.strip().lower()
        _photometric = form.photometric.data
        _guiding = form.guiding.data
        _non_sidereal = form.non_sidereal.data
        _telescope = form.telescope.data.strip()
        _instrument = form.instrument.data.strip()
        _binning = form.binning.data.strip()
        _dither = form.dither.data.strip()
        _cadence = form.cadence.data.strip()
        _iso = get_iso()
        _mjd = float(iso_to_mjd(_iso))

        #get multiple exposures from the page
        exposures = ObsExposure.ObsExposuresFromPage(page_form)

        #validate multiple exposures:

        # validate telescope / instrument pair
        if f'{_instrument}' not in ARTN_SUPPORTED_NODES[f'{_telescope}']:
            return render_template('409.html', reason=f'Invalid telescope ({_telescope}) and instrument '
                                                      f'({_instrument}) combination!', caller='orp_osbreq')

        # check known limit(s)
        _d = dec_to_deg(_dec_dms)
        if _d > TEL__DEC__LIMIT[f'{_telescope.lower()}']:
            msg_out(f"ERROR: requested declination {_d:.3f} > {TEL__DEC__LIMIT[_telescope.lower()]} limit "
                    f"for {_telescope} telescope", True, True)
            return redirect(url_for('orp_user', username=_u.username))

        # get json
        if _non_sidereal:
            _str = form.ns_params.data
            _str_start = _str.find('{')
            _str_end = _str.rfind('}') + 1
            _json = f"{_str[_str_start:_str_end]}"
            if check_json(_json):
                _non_sidereal_json = json.loads(_json)
            else:
                msg_out(f"ERROR: json not valid ... skipping", True, True)
                return redirect(url_for('orp_user', username=_u.username))
        else:
            _non_sidereal_json = json.loads('{}')

        # munge the input(s) as required
        _begin_mjd = str(_begin_iso).replace(' ', 'T')
        _begin_mjd = f'{_begin_mjd}.000000'
        _begin_mjd = float(iso_to_mjd(_begin_mjd))

        _end_mjd = str(_end_iso).replace(' ', 'T')
        _end_mjd = f'{_end_mjd}.000000'
        _end_mjd = float(iso_to_mjd(_end_mjd))

        # assign a (nominal) moonphase calculation
        _sign = -1.0 if random.uniform(-1.0, 1.0) < 0.0 else 1.0
        if _lunarphase == 'dark':
            _moonphase = _sign * random.uniform(0.0, 5.5)
        elif _lunarphase == 'grey':
            _moonphase = _sign * random.uniform(5.5, 8.5)
        else:
            _moonphase = _sign * random.uniform(8.5, 15.0)

        # noinspection PyArgumentList
        _or = ObsReq2(username=_u.username, pi=f'{_u.firstname} {_u.lastname}, {_u.affiliation}', created_iso=_iso,
                     created_mjd=_mjd, observation_id=get_unique_hash(),
                     priority=_priority, priority_value=-_mjd if _priority == 'urgent' else _mjd,
                     object_name=_object_name, ra_hms=_ra_hms, ra_deg=ra_to_deg(_ra_hms), dec_dms=_dec_dms,
                     dec_deg=dec_to_deg(_dec_dms), begin_iso=_begin_iso, begin_mjd=_begin_mjd, end_iso=_end_iso,
                     end_mjd=_end_mjd, airmass=_airmass, lunarphase=_lunarphase, moonphase=_moonphase,
                     photometric=_photometric, guiding=_guiding, non_sidereal=_non_sidereal,
                     non_sidereal_json=_non_sidereal_json, telescope=_telescope, binning=_binning, dither=_dither, cadence=_cadence,
                     queued_iso=ARTN_ZERO_ISO, queued_mjd=ARTN_ZERO_MJD, completed_iso=ARTN_ZERO_ISO, completed_mjd=ARTN_ZERO_MJD,
                     instrument=_instrument, queued=False, completed=False)

        # insert into database
        try:
            db.session.add(_or)
            db.session.flush()

            for e in exposures:
                e.obsreqid = _or.id
                e.completed = False
                db.session.add(e)

            db.session.commit()
            msg_out(f'Observation request {_or.__str__()} created OK with {str(len(exposures))} exposures', True, True)
            return redirect(url_for(return_page, username=_u.username)+'?'+arg_str)

        except Exception as _e:
            db.session.rollback()
            msg_out(f'ERROR: Failed to create observation request for {_u.username}, error={_e}', True, True)
            return render_template('obsreq2.html', form=form)

	#test if update save
    if obsreqid and form.validate_on_submit():
        _obsreq = ObsReq2.query.filter_by(id=obsreqid).first_or_404()
        
        # update records
        _obsreq.username = _u.username
        _obsreq.object_name = encode_verboten(form.object_name.data.strip(), ARTN_ENCODE_DICT)
        _obsreq.ra_hms = form.ra_hms.data.strip()
        _obsreq.dec_dms = form.dec_dms.data.strip()
        _obsreq.begin_iso = form.begin_iso.data
        _obsreq.end_iso = form.end_iso.data
        _obsreq.airmass = form.airmass.data
        _obsreq.lunarphase = form.lunarphase.data.strip().lower()
        _obsreq.photometric = form.photometric.data
        _obsreq.guiding = form.guiding.data
        _obsreq.non_sidereal = form.non_sidereal.data
        _obsreq.filter_name = form.filter_name.data.strip()
        _obsreq.telescope = form.telescope.data.strip()
        _obsreq.binning = form.binning.data.strip()
        _obsreq.dither = form.dither.data.strip()
        _obsreq.cadence = form.cadence.data.strip()

        # validate telescope / instrument pair
        if f'{_obsreq.instrument}' not in ARTN_SUPPORTED_NODES[f'{_obsreq.telescope}']:
            return render_template('409.html', reason=f'Invalid telescope ({_obsreq.telescope}) and instrument '
                                                      f'({_obsreq.instrument}) combination!', caller='orp_update')

        # reset flags
        _obsreq.queued = False
        _obsreq.queued_iso = ARTN_ZERO_ISO
        _obsreq.queued_mjd = ARTN_ZERO_MJD
        _obsreq.completed = False
        _obsreq.completed_iso = ARTN_ZERO_ISO
        _obsreq.completed_mjd = ARTN_ZERO_MJD
        _obsreq.rts2_id = -1
        _obsreq.rts2_doc = '{}'
        _obsreq.obs_status = ''
        _obsreq.percent_completed = 0.0

        # get json
        if _obsreq.non_sidereal:
            _str = form.ns_params.data
            _str_start = _str.find('{')
            _str_end = _str.rfind('}') + 1
            _json = f"{_str[_str_start:_str_end]}"
            msg_out(f"_json={_json}", True, True)
            if check_json(_json):
                _obsreq.non_sidereal_json = json.loads(_json)
            else:
                msg_out(f"ERROR: json not valid ... skipping", True, True)
                return redirect(url_for('orp_user', username=_u.username))
        else:
            _obsreq.non_sidereal_json = json.loads('{}')

        # munge the input(s) as required
        _old_priority_value = _obsreq.priority_value
        _old_priority = _obsreq.priority.strip().lower()
        _new_priority = form.priority.data.strip().lower()

        _priority_value = 0.0
        if _new_priority != _old_priority:
            if _new_priority == 'routine':
                _priority_value = _obsreq.created_mjd,
            elif _new_priority == 'urgent':
                created_iso = get_iso()
                created_mjd = iso_to_mjd(created_iso)
                _priority_value = -created_mjd if _obsreq.priority == 'urgent' else created_mjd
        _obsreq.priority_value = _priority_value
        _obsreq.priority = _new_priority

        _ra_hms = form.ra_hms.data.strip()
        _obsreq.ra_deg = ra_to_deg(_ra_hms)

        _dec_dms = form.dec_dms.data.strip()
        _obsreq.dec_deg = dec_to_deg(_dec_dms)
        if _obsreq.dec_deg > TEL__DEC__LIMIT[f'{_obsreq.telescope.lower()}']:
            msg_out(f"ERROR: requested declination {_obsreq.dec_deg:.3f} > {TEL__DEC__LIMIT[_obsreq.telescope.lower()]}"
                    f" limit for {_obsreq.telescope} telescope", True, True)
            return redirect(url_for('orp_user', username=_u.username))

        _begin_iso = form.begin_iso.data
        _begin_mjd = str(_begin_iso).replace(' ', 'T')
        _begin_mjd = f'{_begin_mjd}.000000'
        _begin_mjd = float(iso_to_mjd(_begin_mjd))
        _obsreq.begin_mjd = _begin_mjd

        _end_iso = form.end_iso.data
        _end_mjd = str(_end_iso).replace(' ', 'T')
        _end_mjd = f'{_end_mjd}.000000'
        _end_mjd = float(iso_to_mjd(_end_mjd))
        _obsreq.end_mjd = _end_mjd

        _sign = -1.0 if random.uniform(-1.0, 1.0) < 0.0 else 1.0
        if _obsreq.lunarphase == 'dark':
            _obsreq.moonphase = _sign * random.uniform(0.0, 5.5)
        elif _obsreq.lunarphase == 'grey':
            _obsreq.moonphase = _sign * random.uniform(5.5, 8.5)
        else:
            _obsreq.moonphase = _sign * random.uniform(8.5, 15.0)

        #get the requested exposures table
        updated_exposures = ObsExposure.ObsExposuresFromPage(page_form)
        prev_exposures = db.session.query(ObsExposure).filter(ObsExposure.obsreqid == obsreqid)

        #test if any exposures were deleted
        updated_expids = [x.id for x in updated_exposures]
        for p_exp in prev_exposures:
            if p_exp.id not in updated_expids:
                db.session.delete(p_exp)

        #update all exposures information, or if new insertion
        for up_exp in updated_exposures:
            up_exp.completed = False
            up_exp.queued = False
            up_exp.obsreqid = int(obsreqid)
            if up_exp.id is None:
                db.session.add(up_exp)
            prev = prev_exposures.filter(ObsExposure.id == up_exp.id).first()
            if prev:
                prev.completed = False
                prev.queued = False
                prev.filter_name = up_exp.filter_name
                prev.exp_time = up_exp.exp_time
                prev.num_exp = up_exp.num_exp


        db.session.flush()
        db.session.commit()
        msg_out(f'Observation request {_obsreq.__str__()} updated OK with {str(len(updated_exposures))} exposures', True, True)
        return redirect(url_for(return_page, username=_u.username) + '?' + arg_str)

    return render_template('obsreq2.html', form=form, fresh=True, arg_str=arg_str, return_page=return_page)


# +
# route(s): /orp/observe/<username>?dbid=<num>, requires login
# -
@app.route('/orp/orp/observe2/<username>', methods=['GET', 'POST'])
@app.route('/orp/observe2/<username>', methods=['GET', 'POST'])
@app.route('/observe2/<username>', methods=['GET', 'POST'])
@login_required
def orp_observe2(username=''):
    #implement view_request argstring as well

    msg_out(f'/orp/observe/{username} entry', True, False)
    get_client_ip(request)

    # look up user (as required)
    _u = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()

    obsreqid = request.args.get('obsreqid', None)
    return_page = request.args.get('return_page', 'orp_view_requests')

    _args = request.args.copy()
    try:
        _args.pop('return_page')
        _args.pop('obsreqid')
    except KeyError:
        pass
    arg_str = urlencode(_args)

    if obsreqid is None:
        msg_out(f'ERROR: Failed to get observation id {obsreqid}', True, True)
        return redirect(url_for('orp_view_requests', username=_u.username))

    # get observation
    _obsreq = None
    _exposures = []
    try:
        _obsreq = ObsReq2.query.filter_by(id=obsreqid).first_or_404()
        _exposures = ObsExposure.query.filter_by(obsreqid=obsreqid).all()
    except Exception as _e:
        msg_out(f'ERROR: Failed to get observation request {obsreqid}, error={_e}', True, True)
        return redirect(url_for('orp_view_requests', username=_u.username))
    else:
        msg_out(f"orp_observe> observation request: obsreqid={obsreqid}, "
                f"_object_name={decode_verboten(_obsreq.object_name, ARTN_DECODE_DICT)}, "
                f"_user={_u.username}", True, False)

    # call telescope-specific routine
    _rts2_doc = None
    _rts2_id = -1

    if _obsreq is not None:

        _tel_name = _obsreq.telescope.lower()
        msg_out(f"orp_observe> calling TELESCOPES['{_tel_name}'].observe()", True, False)
        _rts2_doc, _rts2_id = TELESCOPES[f'{_tel_name}'].observe(_obsreq=_obsreq, _exposures=_exposures, _user=_u)
        msg_out(f"orp_observe> called TELESCOPES['{_tel_name}'].observe()", True, False)

        if _rts2_doc is not None:
            if _rts2_id != -1:
                msg_out(f'Observation request {obsreqid} sent to telescope OK', True, False)
            if _rts2_id > 0:
                try:
                    _obsreq.completed = False
                    _obsreq.completed_iso = ARTN_ZERO_ISO
                    _obsreq.completed_mjd = ARTN_ZERO_MJD
                    _obsreq.queued = True
                    _iso = get_iso()
                    _obsreq.queued_iso = _iso
                    _obsreq.queued_mjd = iso_to_mjd(_iso)
                    _obsreq.rts2_doc = _rts2_doc
                    _obsreq.rts2_id = _rts2_id
                    db.session.commit()
                    msg_out(f'Observation request {obsreqid} committed to database OK', True, False)
                except Exception as _e:
                    db.session.rollback()
                    msg_out(f'ERROR: Failed to send observation request {obsreqid} to telescope, error={_e}', True, True)

    # return for GET
    #make this go back to the view_requests
    return redirect(url_for(return_page, username=_u.username) + '?' + arg_str)


@app.route('/orp/orp/test_data/<username>', methods=['GET', 'POST'])
@app.route('/orp/test_data/<username>', methods=['GET', 'POST'])
@app.route('/test_data/<username>', methods=['GET', 'POST'])
def test_data(username=''):

    user = current_user if current_user.is_authenticated else User.query.filter_by(username=username).first_or_404()
    
    test_json = {
        'object_name':'Sam',
        'ra':'22',
        'dec':'-63',
        'begin':datetime.datetime(2022, 5, 30),
        'end':datetime.datetime(2022, 5, 30),
        'cadence':'Once',
        'dither':'None',
        'guiding':True,
        'lunarphase':'Any',
        'instrument':'Mont4k',
        'telescope':'Kuiper',
        'non_sidereal_json':{'RA_BiasRate':30.0, 'Dec_BiasRate':30.0, 'ObjectRate':5.0, 'PositionAngle':0.0, 'UTC_At_Position':datetime.datetime(2022, 5, 30)},
        'priority':'ToO',

    }
    obsreq, validator, obsreq_valid = ObsReq2.validate_json(test_json, user)


    if obsreq_valid:
        print('valid obsreq')
        db.session.add(obsreq)
        db.session.flush()    
        test_exposure_obs = {
            'filter':'V',
            'num_exp':4,
            'exp_time':333,
            'obsreqid':obsreq.id
        }
        obsexp, validator, obsexp_valid = ObsExposure.validate_json(test_exposure_obs)
        if obsexp_valid:
            print('valid obsexp')
            db.session.add(obsexp)
            db.session.flush()  
            return obsreq.serialized()
        else:
            return jsonify(validator.errors)
    else:
        return jsonify(validator.errors)
        

@app.route('/orp/orp/dataconvert_obsreq2/<username>', methods=['GET', 'POST'])
@app.route('/orp/dataconvert_obsreq2/<username>', methods=['GET', 'POST'])
@app.route('/dataconvert_obsreq2/<username>', methods=['GET', 'POST'])
def dataconvert_obsreq2(username=''):

    return 'Not for you'
    db_resp = db.session.query(ObsReq).all()

    '''Dirty way to group obsreqs'''
    target_names = []

    print('Length of old ObsReq Entries: ', len(db_resp))

    SNs = []

    for resp in db_resp:
        objname = resp.object_name
        

        sn20splitkeys = ['sn20', 'SN20', 'at20', 'AT20', 'sn.ws.20', 'SN.ws.20', 'fuk20']
        for sk in sn20splitkeys:
            if sk in objname:
                atin = 'sn20' in objname or 'SN20' in objname or '.ws.20' in objname or 'fuk20' in objname
                if '-' in objname:
                    objname = objname.split(sk)[1].split('-')[0]
                else:
                    objname = objname.split(sk)[1]
                if atin:
                    SNs.append(objname)

        sn20splitkeys2 = ['2015','2017', '2018', '2019', '2020', '2021', '2022']
        for sk in sn20splitkeys2:
            if sk in objname:
                if '-' in objname:
                    objname = objname.split('20')[1].split('-')[0]
                else:
                    objname = objname.split('20')[1]
                SNs.append(objname)

        if '.us.' in objname:
            objname = objname.split('.us.')[0]
        elif '.ws.' in objname:
            objname = objname.split('.ws.')[0]
        if '_' in objname:
            objname = objname.split('_')[0]

        if objname  == 'sn' or objname == 'SN':
            objname = resp.object_name.split('.ws.')[1]
        if objname == 'GW':
            objname = resp.object_name

        target_names.append(objname)

    dumbbumbles = ['SA112-check', 'NGC4559-OT-U', 'NGC4559-OT-R', 'HD']
    target_names = [x for x in target_names if x != '' and x not in dumbbumbles]
    target_names = list(set(target_names))
    target_names.append('140982')

    print(sorted(target_names))
    print('Grouped targetnames: ', len(target_names))

    new_expdata = []
    new_obsreqdata = []

    oldids = []

    for t in target_names:
        if t == '20ue':
            observations = [x for x in db_resp if t in x.object_name and '20uec' not in x.object_name]
        else:
            observations = [x for x in db_resp if t in x.object_name]
        ob1 = observations[0]
        if t == '140982':
            t = 'HD140982'

        '''
        create the ObsReq2 from ob1
        session.flush() for obsreq2 id
        iterate over all observations
            create ObsExposure
                obsreqid = or.id
        session.commit()
        '''

        target_keytests = ['00','09','16','17','18','19','20','21','22']
        for tt in target_keytests:
            if t.startswith(tt):
                if t in SNs:
                    t = 'SN20'+t
                else:
                    t = 'AT20'+t

        _or = ObsReq2(
            username = ob1.username,
            pi = ob1.pi,
            priority = ob1.priority,
            priority_value = ob1.priority_value,
            created_iso = ob1.created_iso,
            created_mjd = ob1.created_mjd,
            object_name = t,
            ra_hms = ob1.ra_hms,
            ra_deg = ob1.ra_deg,
            dec_dms = ob1.dec_dms,
            dec_deg = ob1.dec_deg,
            observation_id = ob1.observation_id,
            begin_iso = ob1.begin_iso,
            begin_mjd = ob1.begin_mjd,
            end_iso = ob1.end_iso,
            end_mjd = ob1.end_mjd,
            airmass = ob1.airmass,
            lunarphase = ob1.lunarphase,
            moonphase = ob1.moonphase,
            photometric = ob1.photometric,
            guiding = ob1.guiding,
            binning = ob1.binning,
            dither = ob1.dither,
            cadence = ob1.cadence,
            non_sidereal = ob1.non_sidereal,
            non_sidereal_json = ob1.non_sidereal_json,
            telescope = ob1.telescope,
            instrument = ob1.instrument, 
            rts2_doc = ob1.rts2_doc,
            rts2_id = ob1.rts2_id,
            queued = ob1.queued,
            queued_iso = ob1.queued_iso,
            queued_mjd = ob1.queued_mjd,
            completed = ob1.completed,
            completed_iso = ob1.completed_iso,
            completed_mjd = ob1.completed_mjd,
            user_id = ob1.user_id
        )

        #db.session.add(_or)
        #db.session.flush()

        new_obsreqdata.append(_or)

        for ob in observations:
            oldids.append(ob.id)
            obexp = ObsExposure(
                obsreqid = _or.id,
                filter_name = ob.filter_name,
                exp_time = ob.exp_time,
                num_exp = ob.num_exp,
                completed = ob.completed,
            )
            #db.session.add(obexp)
            new_expdata.append(obexp)
        
    unique_oldids = list(set(oldids))
    for uo in unique_oldids:
        test = [x for x in oldids if x == uo]
        if len(test) > 1:
            duped = [x for x in db_resp if x.id == uo][0].object_name
            print("duped name: ", duped)


    print()
    print('Length of grouped exposures', len(new_obsreqdata))
    print('Length of new data exposures: ', len(new_expdata))
    
    #db.session.commit()

    return 'sucksess'

####
'''
    NEW TODO 1st.
        1.) Write a data conversion script to 'dirty group observations' X
        2.) Make it so that the rts2doc json object works when submitting to rts2 
        3.) Edit the view observable request(s) and view all request(s) tables X
        4.) test test test submissions X

    To do: 
        rename view_queue to manage_queue X
            consider permissions when there is a queue already submitted
            only artn/operator can interrupt/clear queue
            maybe programs with ToO

        create view_queue<telescope>
            if there is a queue submitted/running for the telescope
            have an small table that displays this information
            maybe a nightly queue history
'''
####
# +
# main()
# -
if __name__ == '__main__':
    app.run(host=os.getenv("ORP_APP_HOST"), port=int(os.getenv("ORP_APP_PORT")), threaded=True, debug=False)
