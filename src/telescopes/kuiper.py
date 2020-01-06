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
    tel_logger.critical(f'failed to load rts2solib, src={RTS2SOLIBSRC}, error={e}')


# +
# logging
# -
#tel_logger = UtilsLogger('RTS2-Logger').logger
#tel_logger.debug(f'PYTHONPATH = {PYTHONPATH}')
#tel_logger.debug(f'RTS2SOLIBPATH={RTS2SOLIBPATH}')
#tel_logger.debug(f'RTS2SOLIBSRC={RTS2SOLIBSRC}')


# +
# function: kuiper_observe()
# -
def kuiper_observe(_obsreq=None, _user=None):

    # check input(s)
    if _obsreq is None:
        tel_logger.error(f'invalid input, _obsreq={_obsreq}')
        return '{}', -1
    if _user is None:
        tel_logger.error(f'invalid input, _user={_user}')
        return '{}', -1
    tel_logger.debug(f"kuiper_observe(_obsreq={_obsreq.__repr__()}, _user=()) ... entry")

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
    tel_logger.debug(f'Queueing {_object_name} ({_ra_hms} {_dec_dms} {_exp_time}s {_num_exp}x {_filter_name}-band)')

    # create the target
    try:
        tel_logger.debug(f'Calling stellar()')
        _target = stellar(name=_observation_id[:4]+_object_name, ra=_ra_hms, dec=_dec_dms,
                          obs_info=[so_exposure(Filter=_filter_name, exptime=_exp_time, amount=_num_exp)],
                          artn_obs_id=_observation_id, artn_group_id=_group_id)
        tel_logger.debug(f'Called stellar() OK, _target={_target}')
    except Exception as _e:
        tel_logger.error(f'Failed calling stellar(), _target={_target}, error={_e}')
        return '{}', -1

    # create the json script
    try:
        tel_logger.debug(f'Calling _target.create_target_api()')
        _id = _target.create_target_api()
        tel_logger.debug(f'Called _target.create_target_api() OK, _id={_id}')
    except Exception as _e:
        tel_logger.error(f'Failed calling _target.create_target_api(), _id={_id}')
        return '{}', -1

    # dictify the target
    try:
        tel_logger.debug(f'Calling _target.dictify()')
        _json = _target.dictify()
        tel_logger.debug(f'Called _target.dictify() OK, _json={_json}')
    except Exception as _e:
        tel_logger.error(f'Failed calling _target.dictify(), _json={_json}')
        return '{}', -1

    # create queue
    try:
        tel_logger.debug(f'Calling Queue()')
        _queue = Queue(f'plan')
        tel_logger.debug(f'Called Queue() OK, _queue={_queue}')
    except Exception as _e:
        tel_logger.error(f'Failed calling Queue() OK, _queue={_queue}')
        return '{}', -1

    # add target to queue
    try:
        tel_logger.debug(f'Calling _queue.add_target()')
        _queue.add_target(_id)
        tel_logger.debug(f'Called _queue.add_target() OK')
    except Exception as _e:
        tel_logger.error(f'Failed calling _queue.add_target()')
        return '{}', -1

    # load the queue
    try:
        tel_logger.debug(f'Calling _queue.load()')
        _queue.load()
        tel_logger.debug(f'Called _queue.load() OK')
    except Exception as _e:
        tel_logger.error(f'Failed calling _queue.load()')
        return '{}', -1

    # save the queue (in effect, send to rts2)
    try:
        tel_logger.debug(f'Calling _queue.save()')
        _queue.save()
        tel_logger.debug(f'Called _queue.save() OK')
    except Exception as _e:
        tel_logger.error(f'Failed calling _queue.save()')
        return '{}', -1

    # return
    tel_log(f'Queued {_object_name} ({_ra_hms} {_dec_dms} {_exp_time}s {_num_exp}x {_filter_name}-band) OK', True, True)
    tel_logger.debug(f'Queued {_object_name} ({_ra_hms} {_dec_dms} {_exp_time}s {_num_exp}x {_filter_name}-band) OK')
    tel_logger.debug(f"kuiper_observe(_obsreq={_obsreq.__repr__()}, _user=()) ... exit")
    return _json, _id
