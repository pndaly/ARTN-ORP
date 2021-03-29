#!/usr/bin/env python3


# +
# import(s)
# -
from . import *

import os
import random
import sys


# +
# initialize RTS2
# -
RTS2SOLIBPATH = os.getenv("RTS2SOLIBPATH", f'{os.getenv("ORP_SRC")}/telescopes')
RTS2SOLIBSRC = os.getenv("RTS2SOLIBSRC", f'{os.getenv("ORP_SRC")}/rts2solib')

try:
    sys.path.append(RTS2SOLIBSRC)
    sys.path.append(RTS2SOLIBPATH)
    # noinspection PyUnresolvedReferences
    from rts2solib import Queue, stellar, so_exposure
except Exception as e:
    tel_logger.critical(f'failed to load rts2solib, src={RTS2SOLIBSRC}, error={e}')


# +
# constant(s)
# -
_seed = random.seed()


# +
# function: kuiper_observe()
# -
def kuiper_observe(_obsreq=None, _user=None, _sim=False):

    if _sim:
        tel_log(f'kuiper_observe> entry _obsreq={_obsreq.__repr__()}, _user={_user.__repr__()}, _sim={str(_sim)}',
                True, False)
    else:
        tel_logger.info(f'kuiper_observe> entry _obsreq={_obsreq.__repr__()}, _user={_user.__repr__()}, '
                        f'_sim={str(_sim)}')

    # check input(s)
    if _obsreq is None:
        tel_log(f'ERROR: invalid input, _obsreq={_obsreq}', True, True)
        return '{}', -1
    if _user is None:
        tel_log(f'ERROR: invalid input, _user={_user}', True, True)
        return '{}', -1

    # set default(s)
    _filter_name = _obsreq.filter_name
    _exp_time = _obsreq.exp_time
    _num_exp = _obsreq.num_exp
    _object_name = decode_verboten(_obsreq.object_name, ARTN_DECODE_DICT)
    _ra_hms = _obsreq.ra_hms
    _dec_dms = _obsreq.dec_dms
    _observation_id = _obsreq.observation_id
    _group_id = _obsreq.group_id
    _tel_name = _obsreq.telescope

    _queue = None
    _target = None
    _json = '{}'
    _id = -1
    _sim_json = '{}'
    _sim_id = -1

    if _sim:
        _sim_id = random.randrange(-1000, -500, 1)
        _sim_json = {
            'ra': f'{_ra_hms}', 
            'dec': f'{_dec_dms}', 
            'name': f'{_object_name}', 
            'obs_id': f'{_observation_id}', 
            'group_id': f'{_group_id}', 
            'obs_info': [{
                'Filter': f'{_filter_name}', 
                'amount': _num_exp, 
                'exptime': _exp_time
            }]
        }
        _sim_json = f'"{_sim_json}"'
    tel_log(f'_json={_json}, _id={_id}', True, False)
    tel_log(f'_sim_json={_sim_json}, _sim_id={_sim_id}', True, False)

    # for RTS2, remove white-space in object_name and ensure it does *not* end in 'target' !
    _object_name = _object_name.replace(' ', '_')
    if _object_name.lower().endswith(f'target'):
        _object_name = _object_name[:-6].strip()
    tel_log(f'Queueing {_object_name} on the {_tel_name} telescope', False, True)
    tel_log(f'Queueing {_object_name} on the {_tel_name} telescope ({_ra_hms} {_dec_dms} {_exp_time}s '
            f'{_num_exp}x {_filter_name}-band)', True, False)

    # create the target
    _msg_err = f'ERROR: Failed calling stellar(), _sim={_sim}'
    _msg_in = f'Calling stellar(), _sim={_sim}'
    _msg_out = f'Called stellar(), _sim={_sim}'
    try:
        tel_log(_msg_in, True, False)
        if not _sim:
            _target = stellar(name=_observation_id[:4]+_object_name, ra=_ra_hms, dec=_dec_dms,
                              obs_info=[so_exposure(Filter=_filter_name, exptime=_exp_time, amount=_num_exp)],
                              artn_obs_id=_observation_id, artn_group_id=_group_id)
        tel_log(_msg_out, True, False)
    except Exception as _e:
        tel_log(_msg_err, True, True)
        tel_logger.error(f'Failed calling stellar(), _target={_target}, error={_e}')
        return '{}', -1

    # create the json script
    _msg_err = f'ERROR: Failed calling _target.create_target_api(), _sim={_sim}'
    _msg_in = f'calling _target.create_target_api(), _sim={_sim}'
    _msg_out = f'called _target.create_target_api(), _sim={_sim}'
    try:
        tel_log(_msg_in, True, False)
        if not _sim:
            _id = _target.create_target_api()
        tel_log(_msg_out, True, False)
    except Exception as _e:
        tel_log(_msg_err, True, True)
        tel_logger.error(f'Failed calling _target.create_target_api(), _id={_id}, error={_e}')
        return '{}', -1

    # dictify the target
    _msg_err = f'ERROR: Failed calling _target.dictify(), _sim={_sim}'
    _msg_in = f'calling _target.dictify(), _sim={_sim}'
    _msg_out = f'called _target.dictify(), _sim={_sim}'
    try:
        tel_log(_msg_in, True, False)
        if not _sim:
            _json = _target.dictify()
        tel_log(_msg_out, True, False)
    except Exception as _e:
        tel_log(_msg_err, True, True)
        tel_logger.error(f'Failed calling _target.dictify(), _json={_json}, error={_e}')
        return '{}', -1

    # create queue
    _msg_err = f'ERROR: Failed calling Queue(), _sim={_sim}'
    _msg_in = f'calling Queue(), _sim={_sim}'
    _msg_out = f'called Queue(), _sim={_sim}'
    try:
        tel_log(_msg_in, True, False)
        if not _sim:
            _queue = Queue(f'plan')
        tel_log(_msg_out, True, False)
    except Exception as _e:
        tel_log(_msg_err, True, True)
        tel_logger.error(f'Failed calling Queue() OK, _queue={_queue}, error={_e}')
        return '{}', -1

    # add target to queue
    _msg_err = f'ERROR: Failed calling _queue.add_target(), _sim={_sim}'
    _msg_in = f'calling _queue.add_target(), _sim={_sim}'
    _msg_out = f'called _queue.add_target(), _sim={_sim}'
    try:
        tel_log(_msg_in, True, False)
        if not _sim:
            _queue.add_target(_id)
        tel_log(_msg_out, True, False)
    except Exception as _e:
        tel_log(_msg_err, True, True)
        tel_logger.error(f'Failed calling _queue.add_target(), error={_e}')
        return '{}', -1

    # load the queue
    _msg_err = f'ERROR: Failed calling _queue.load(), _sim={_sim}'
    _msg_in = f'calling _queue.load(), _sim={_sim}'
    _msg_out = f'called _queue.load(), _sim={_sim}'
    try:
        tel_log(_msg_in, True, False)
        if not _sim:
            _queue.load()
        tel_log(_msg_out, True, False)
    except Exception as _e:
        tel_log(_msg_err, True, True)
        tel_logger.error(f'Failed calling _queue.load(), error={_e}')
        return '{}', -1

    # save the queue (in effect, send to rts2)
    _msg_err = f'ERROR: Failed calling _queue.save(), _sim={_sim}'
    _msg_in = f'calling _queue.save(), _sim={_sim}'
    _msg_in = f'called _queue.save(), _sim={_sim}'
    try:
        tel_log(_msg_in, True, False)
        if not _sim:
            _queue.save()
        tel_log(_msg_out, True, False)
    except Exception as _e:
        tel_log(_msg_err, True, True)
        tel_logger.error(f'Failed calling _queue.save(), error={_e}')
        return '{}', -1

    # return
    tel_log(f'Queued {_object_name} on the {_tel_name} telescope', False, True)
    tel_log(f'Queued {_object_name} on the {_tel_name} telescope ({_ra_hms} {_dec_dms} {_exp_time}s '
            f'{_num_exp}x {_filter_name}-band)', True, False)
    if _sim:
        tel_log(f'_sim_json={_sim_json}, _sim_id={_sim_id}', True, False)
        tel_log(f'kuiper_observe> exit _obsreq={_obsreq.__repr__()}, _user={_user.__repr__()}, '
                f'_sim={str(_sim)}', True, False)
        return _sim_json, _sim_id
    else:
        tel_logger.info(f'_json={_json}, _id={_id}')
        tel_logger.info(f'kuiper_observe> exit _obsreq={_obsreq.__repr__()}, _user={_user.__repr__()}, '
                        f'_sim={str(_sim)}')
        return _json, _id
