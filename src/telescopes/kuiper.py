#!/usr/bin/env python3.7


# +
# import(s)
# -
from . import *

import os
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
    raise Exception(f'Failed to load rts2solib, src={RTS2SOLIBSRC}, error={e}')


# +
# logging
# -
_rts2_log = UtilsLogger('RTS2-Logger').logger
_rts2_log.debug(f'PYTHONPATH = {PYTHONPATH}')
_rts2_log.debug(f'RTS2SOLIBPATH={RTS2SOLIBPATH}')
_rts2_log.debug(f'RTS2SOLIBSRC={RTS2SOLIBSRC}')


# +
# function: kuiper_observe()
# -
def kuiper_observe(_obsreq=None, _user=None):

    # check input(s)
    if _obsreq is None:
        raise Exception(f'Invalid input, _obsreq={_obsreq}')
    if _user is None:
        raise Exception(f'Invalid input, _user={_user}')

    _rts2_log.debug(f"kuiper_observe(_obsreq={_obsreq.__repr__()}, _user=()) ... entry")

    # set default(s)
    _queue = None
    _target = None
    _json = '{}'
    _id = -1

    _filter_name = _obsreq.filter_name
    _exp_time = _obsreq.exp_time
    _num_exp = _obsreq.num_exp
    _object_name = decode_verboten(_obsreq.object_name, ARTN_DECODE_DICT)
    _ra_hms = _obsreq.ra_hms
    _dec_dms = _obsreq.dec_dms
    _observation_id = _obsreq.observation_id
    _group_id = _obsreq.group_id

    # for RTS2, remove white-space in object_name and ensure it does *not* end in 'target' !
    _object_name = _object_name.replace(' ', '_')
    if _object_name.lower().endswith(f'target'):
        _object_name = _object_name[:-6].strip()
    tel_log(f'Queueing {_object_name} ({_ra_hms} {_dec_dms} {_exp_time}s {_num_exp}x {_filter_name}-band)', True, True)
    _rts2_log.debug(f'Queueing {_object_name} ({_ra_hms} {_dec_dms} {_exp_time}s {_num_exp}x {_filter_name}-band)')

    # create the target
    try:
        _rts2_log.debug(f'Calling stellar()')
        _target = stellar(name=_observation_id[:4]+_object_name, ra=_ra_hms, dec=_dec_dms,
                          obs_info=[so_exposure(Filter=_filter_name, exptime=_exp_time, amount=_num_exp)],
                          artn_obs_id=_observation_id, artn_group_id=_group_id)
        _rts2_log.debug(f'Called stellar() OK, _target={_target}')
        tel_log(f'Created target OK, _target={_target}', True, False)
    except Exception as _e:
        _rts2_log.error(f'ERROR: Calling stellar(), _target={_target}, error={_e}')
        tel_log(f'ERROR: Failed to create _target, error={_e}', True, True)
        return '{}', -1

    # create the json script
    try:
        _rts2_log.debug(f'Calling _target.create_target_api()')
        _id = _target.create_target_api()
        _rts2_log.debug(f'Called _target.create_target_api() OK, _id={_id}')
        tel_log(f'Saved target OK, id={_id}', True, False)
    except Exception as _e:
        _rts2_log.error(f'ERROR: Calling _target.create_target_api(), _id={_id}')
        tel_log(f'ERROR: Failed to save target, error={_e}', True, True)
        return '{}', -1

    # dictify the target
    try:
        _rts2_log.debug(f'Calling _target.dictify()')
        _json = _target.dictify()
        _rts2_log.debug(f'Called _target.dictify() OK, _json={_json}')
        tel_log(f'Dictified target OK, _json={_json}', True, False)
    except Exception as _e:
        _rts2_log.error(f'ERROR: Calling _target.dictify(), _json={_json}')
        tel_log(f'ERROR: Failed to dictify target, error={_e}', True, True)
        return '{}', -1

    # create queue
    try:
        _rts2_log.debug(f'Calling Queue()')
        _queue = Queue(f'plan')
        _rts2_log.debug(f'Called Queue() OK, _queue={_queue}')
        tel_log(f'Created queue OK, _queue={_queue}', True, False)
    except Exception as _e:
        _rts2_log.error(f'FAILED: Calling Queue() OK, _queue={_queue}')
        tel_log(f'ERROR: Failed to create queue, error={_e}', True, True)
        return '{}', -1

    # add target to queue
    try:
        _rts2_log.debug(f'Calling _queue.add_target()')
        _queue.add_target(_id)
        _rts2_log.debug(f'Called _queue.add_target() OK')
        tel_log(f'Added target(s) to queue OK', True, False)
    except Exception as _e:
        _rts2_log.error(f'ERROR: Calling _queue.add_target()')
        tel_log(f'ERROR: Failed to add target(s) to queue, error={_e}', True, True)
        return '{}', -1

    # load the queue
    try:
        _rts2_log.debug(f'Calling _queue.load()')
        _queue.load()
        _rts2_log.debug(f'Called _queue.load() OK')
        tel_log(f'Loaded queue OK', True, False)
    except Exception as _e:
        _rts2_log.error(f'ERROR: Calling _queue.load()')
        tel_log(f'ERROR: Failed to load queue, error={_e}', True, True)
        return '{}', -1

    # save the queue (in effect, send to rts2)
    try:
        _rts2_log.debug(f'Calling _queue.save()')
        _queue.save()
        _rts2_log.debug(f'Called _queue.save() OK')
        tel_log(f'Saved queue OK', True, False)
    except Exception as _e:
        _rts2_log.error(f'ERROR: Calling _queue.save()')
        tel_log(f'ERROR: Failed to save queue, error={_e}', True, True)
        return '{}', -1

    # return
    tel_log(f'Queued {_object_name} ({_ra_hms} {_dec_dms} {_exp_time}s {_num_exp}x {_filter_name}-band) OK', True, True)
    _rts2_log.debug(f'Queued {_object_name} ({_ra_hms} {_dec_dms} {_exp_time}s {_num_exp}x {_filter_name}-band) OK')
    _rts2_log.debug(f"kuiper_observe(_obsreq={_obsreq.__repr__()}, _user=()) ... exit")
    return _json, _id
