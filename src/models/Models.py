#!/usr/bin/env python3


# +
# import(s)
# -
from src import *
from src.telescopes.factory import *
from src.telescopes.bok import *
from src.telescopes.kuiper import *
from src.telescopes.vatt import *

from astropy.time import Time
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import not_
from sqlalchemy.dialects.postgresql import JSONB
from time import time
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

import secrets
import json
import jwt
from . import validator

# +
# __doc__ string
# -
__doc__ = """

    import Models
    from Models import *
    from src.models import Models
    from src.models.Models import User, user_filters
    from src.models.Models import ObsReq, obsreq_filters

"""


# +
# constant(s)
# -
FALSE_VALUES = ['false', 'f', '0']
TRUE_VALUES = ['true', 't', '1']


# +
# initialize sqlalchemy (deferred)
# -
db = SQLAlchemy()


# +
# logging
# -
# logger = UtilsLogger('Models-Logger').logger
# logger.debug(f"Models logger initialized")


# +
# table validation api ingestion of obsreq2+obsexposure
# -
class _TableValidation():
    def __init__(self):
        self.valid = False
        self.errors = []
        self.valid_inst = {}


# +
# class: NightlyQueue(), inherits from UserMixin, db.Model
# -
class NightlyQueue(UserMixin, db.Model):
    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'nightlyqueue'
    _iso = get_iso()
    _mjd = float(iso_to_mjd(_iso))

    # +
    # table mapping
    # -
    # noinspection PyUnresolvedReferences
    id = db.Column(db.Integer, primary_key=True, index=True)
    # noinspection PyUnresolvedReferences
    night = db.Column(db.String(ARTN_CHAR_256), nullable=False)
    # noinspection PyUnresolvedReferences
    queued_iso = db.Column(db.DateTime, default=get_date_time(0), nullable=False)
    # noinspection PyUnresolvedReferences
    queued_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    telescope = db.Column(db.String(ARTN_CHAR_16), nullable=False)
    # noinspection PyUnresolvedReferences
    submitted = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    completed = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    completed_iso = db.Column(db.DateTime, nullable=True)
    # noinspection PyUnresolvedReferences
    completed_mjd = db.Column(db.Float, nullable=True)
    # noinspection PyUnresolvedReferences
    interrupt = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    queuetype = db.Column(db.Integer, default=0, nullable=False)


# +
# class: NightlyQueue(), inherits from UserMixin, db.Model
# -
class NightlyQueueExposure(UserMixin, db.Model):
    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'nightlyqueueexposure'
    _iso = get_iso()
    _mjd = float(iso_to_mjd(_iso))

    # +
    # table mapping
    # -
    # noinspection PyUnresolvedReferences
    id = db.Column(db.Integer, primary_key=True, index=True)
    # noinspection PyUnresolvedReferences
    obsreqid = db.Column(db.Integer, nullable=False)
    # noinspection PyUnresolvedReferences
    nightlyqueueid = db.Column(db.Integer, nullable=False)
    # noinspection PyUnresolvedReferences
    queueorder = db.Column(db.Integer, nullable=True)
    # noinspection PyUnresolvedReferences
    rts2_id = db.Column(db.Integer, nullable=False)
    # noinspection PyUnresolvedReferences
    starttime = db.Column(db.DateTime, nullable=True)
    # noinspection PyUnresolvedReferences
    endtime = db.Column(db.DateTime, nullable=True)
    # noinspection PyUnresolvedReferences
    rts2start_t = db.Column(db.Integer, nullable=True)
    # noinspection PyUnresolvedReferences
    rts2end_t = db.Column(db.Integer, nullable=True)
    # noinspection PyUnresolvedReferences
    unscheduled = db.Column(db.Boolean, default=False)
    # noinspection PyUnresolvedReferences
    schedule_log = db.Column(db.String(ARTN_CHAR_256), nullable=False)
    # noinspection PyUnresolvedReferences
    filename = db.Column(db.String(ARTN_CHAR_256), nullable=True, default='')
    # noinspection PyUnresolvedReferences
    overhead = db.Column(db.Float, nullable=False, default=0.0)
    # noinspection PyUnresolvedReferences
    currently_being_observed = db.Column(db.Boolean, nullable=False, default=False)


# +
# class: ObsTarget(), inherits from UserMixin, db.Model
# -
class ObsTarget(UserMixin, db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'obstarget'
    _iso = get_iso()
    _mjd = float(iso_to_mjd(_iso))

    # +
    # table mapping
    # -
    # noinspection PyUnresolvedReferences
    id = db.Column(db.Integer, primary_key=True, index=True)
    # noinspection PyUnresolvedReferences
    username = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    created_iso = db.Column(db.DateTime, default=_iso, nullable=False)
    # noinspection PyUnresolvedReferences
    created_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    object_name = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    ra_hms = db.Column(db.String(ARTN_CHAR_16), nullable=False)
    # noinspection PyUnresolvedReferences
    ra_deg = db.Column(db.Float, default=math.nan, nullable=False)
    # noinspection PyUnresolvedReferences
    dec_dms = db.Column(db.String(ARTN_CHAR_16), nullable=False)
    # noinspection PyUnresolvedReferences
    dec_deg = db.Column(db.Float, default=math.nan, nullable=False)


# +
# class: ObsReq2(), inherits from UserMixin, db.Model
# -
class ObsReq2(UserMixin, db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'obsreq2'
    _iso = get_iso()
    _mjd = float(iso_to_mjd(_iso))

    # +
    # table mapping
    # -
    # noinspection PyUnresolvedReferences
    id = db.Column(db.Integer, primary_key=True, index=True)
    # noinspection PyUnresolvedReferences
    username = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    pi = db.Column(db.String(ARTN_CHAR_256), nullable=False)
    # noinspection PyUnresolvedReferences
    priority = db.Column(db.String(ARTN_CHAR_16), default='Routine', nullable=False)
    # noinspection PyUnresolvedReferences
    priority_value = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    created_iso = db.Column(db.DateTime, default=_iso, nullable=False)
    # noinspection PyUnresolvedReferences
    created_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    object_name = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    ra_hms = db.Column(db.String(ARTN_CHAR_16), nullable=False)
    # noinspection PyUnresolvedReferences
    ra_deg = db.Column(db.Float, default=math.nan, nullable=False)
    # noinspection PyUnresolvedReferences
    dec_dms = db.Column(db.String(ARTN_CHAR_16), nullable=False)
    # noinspection PyUnresolvedReferences
    dec_deg = db.Column(db.Float, default=math.nan, nullable=False)
    # noinspection PyUnresolvedReferences
    observation_id = db.Column(db.String(ARTN_CHAR_128), default=get_unique_hash(), nullable=False, unique=True)
    # noinspection PyUnresolvedReferences
    begin_iso = db.Column(db.DateTime, default=get_date_time(), nullable=False)
    # noinspection PyUnresolvedReferences
    begin_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    end_iso = db.Column(db.DateTime, default=get_date_time(30), nullable=False)
    # noinspection PyUnresolvedReferences
    end_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    airmass = db.Column(db.Float, default=1.0, nullable=False)
    # noinspection PyUnresolvedReferences
    lunarphase = db.Column(db.String(ARTN_CHAR_16), default='Dark', nullable=False)
    # noinspection PyUnresolvedReferences
    moonphase = db.Column(db.Float, default=0.0, nullable=False)
    # noinspection PyUnresolvedReferences
    photometric = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    guiding = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    non_sidereal = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    telescope = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    instrument = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    rts2_doc = db.Column(JSONB, default={}, nullable=False)
    # noinspection PyUnresolvedReferences
    rts2_id = db.Column(db.Integer, default=-1, nullable=False)
    # noinspection PyUnresolvedReferences
    queued = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    queued_iso = db.Column(db.DateTime, default=get_date_time(0), nullable=False)
    # noinspection PyUnresolvedReferences
    queued_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    completed = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    completed_iso = db.Column(db.DateTime, default=get_date_time(0), nullable=False)
    # noinspection PyUnresolvedReferences
    completed_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    binning = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    dither = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    cadence = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    non_sidereal_json = db.Column(JSONB, default={}, nullable=False)

    # noinspection PyUnresolvedReferences
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @staticmethod
    def validate_json(payload, user):
        v = _TableValidation()
        o = ObsReq2()

        #user should be validated before coming here
        #   default those values
        o.username=user.username
        o.pi=f'{user.firstname} {user.lastname}, {user.affiliation}'

        if 'telescope' in payload.keys():
            valid, msg = validator.validate_payload_field_inlist(payload, 'telescope', ['Kuiper'])
            if valid:
                o.telescope = payload['telescope']
            else:
                v.errors.append(msg)
        else:
            o.telescope = 'Kuiper'

        if 'instrument' in payload.keys():
            value = payload['instrument']
            try:
                valid, msg = validator.validate_payload_field_inlist(payload, 'instrument', ARTN_VALID_INSTRUMENT[o.telescope])
                if valid:
                    o.instrument = payload['instrument']
                else:
                    v.errors.append(msg)
            except:
                pass
        else:
            o.instrument = 'Mont4k'

        if 'object_name' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'object_name', str)
            if valid:
                o.object_name = val
            else:
                v.errors.append(msg)
        else:
            v.errors.append('Field \'{}\' is required'.format('object_name'))

        if 'ra' in payload.keys():
            ra_decimal, ra_hms, valid = validator.validate_ra(payload['ra'])
            if valid:
                o.ra_deg = ra_decimal
                o.ra_hms = ra_hms
            else:
                v.errors.append('Invalid format for field \'ra\'. Must be decimal degrees, or str HMS')
        else:
            v.errors.append('Field \'{}\' is required'.format('ra'))
        
        if 'dec' in payload.keys():
            dec_decimal, dec_dms, valid = validator.validate_dec(payload['dec'])
            if valid:
                try:
                    if dec_decimal > TEL__DEC__LIMIT[f'{o.telescope.lower()}']:
                        v.errors.append(f"ERROR: requested declination {dec_decimal:.3f} > {TEL__DEC__LIMIT[o.telescope.lower()]} limit "
                        f"for {o.telescope} telescope")
                    else:
                        o.dec_deg = dec_decimal
                        o.dec_dms = dec_dms
                except:
                    pass
            else:
                v.errors.append('Invalid format for field \'dec\'. Must be decimal degrees, or str DMS')
        else:
            v.errors.append('Field \'{}\' is required'.format('dec'))

        if 'airmass' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'airmass', float)
            if valid:
                if val < 3.01 and val >=1.0:
                    o.object_name = val
                else:
                    v.errors.append('Invalid Value for field \'airmass\'. Must be >= 1.0 and < 3.0')
            else:
                v.errors.append(msg)
        else:
            o.airmass = 2.2
        
        if 'begin' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'begin', datetime, fmt='%Y-%m-%d %H:%M:%S')
            if valid:
                o.begin_iso = val.strftime('%Y-%m-%d %H:%M:%S')
                o.begin_mjd = float(iso_to_mjd(o.begin_iso))
            else:
                v.errors.append(msg)
        else:
            o.begin_iso = get_date_utctime()
            o.begin_mjd = float(iso_to_mjd(o.begin_iso))

        if 'end' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'end', datetime, fmt='%Y-%m-%d %H:%M:%S')
            if valid:
                o.end_iso = val.strftime('%Y-%m-%d %H:%M:%S')
                o.end_mjd = float(iso_to_mjd(o.end_iso))
            else:
                v.errors.append(msg)
        else:
            o.end_iso = get_date_utctime(30)
            o.end_mjd = float(iso_to_mjd(o.end_iso))

        _sign = -1.0 if random.uniform(-1.0, 1.0) < 0.0 else 1.0
        if 'lunarphase' in payload.keys():
            valid, msg = validator.validate_payload_field_inlist(payload, 'lunarphase', ['Dark', 'Grey', 'Bright', 'mBright', 'Any'])
            if valid:
                o.lunarphase = payload['lunarphase']
                if o.lunarphase == 'Dark':
                    o.moonphase = _sign * random.uniform(0.0, 5.5)
                elif o.lunarphase == 'Grey':
                    o.moonphase = _sign * random.uniform(5.5, 8.5)
                else:
                    o.moonphase = _sign * random.uniform(8.5, 15.0)
            else:
                v.errors.append(msg)
        else:
            o.lunarphase = 'Any'
            o.moonphase = _sign * random.uniform(8.5, 15.0)

        if 'priority' in payload.keys():
            valid, msg = validator.validate_payload_field_inlist(payload, 'priority', ['Routine', 'Urgent', 'ToO'])
            if valid:
                o.priority = payload['priority']
                if o.priority == 'Routine':
                    o.priority_value = 5
                if o.priority == 'Urgent':
                    o.priority_value = 3
                if o.priority == 'ToO':
                    o.priority_value = 2
            else:
                v.errors.append(msg)
        else:
            o.priority = 'Routine'
            o.priority_value = 5

        if 'photometric' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'photometric', bool)
            if valid:
                o.photometric = val
            else:
                v.errors.append(msg)
        else:
            o.photometric = False

        if 'guiding' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'guiding', bool)
            if valid:
                o.guiding = val
            else:
                v.errors.append(msg)
        else:
            o.guiding = False

        if 'binning' in payload.keys():
            valid, msg = validator.validate_payload_field_inlist(payload, 'binning', ['4x4', '3x3', '2x2', '1x1'])
            if value in ['4x4', '3x3', '2x2', '1x1']:
                o.binning = payload['binning']
            else:
                v.errors.append(msg)
        else:
            o.binning = '4x4'

        if 'dither' in payload.keys():
            valid, msg = validator.validate_payload_field_inlist(payload, 'dither', ['None', 'n-RA', 'nDec', 'NxM'])
            if valid:
                o.dither = payload['dither']
            else:
                v.errors.append(msg)
        else:
            o.dither = 'None'

        if 'cadence' in payload.keys():
            value = payload['cadence']
            if value in ['Once', 'Daily', 'BisInDie', 'Weekly', 'Monthly']:
                o.cadence = value
            else:
                v.errors.append('Invalid Value for field \'cadence\'. Must be \'Once\', \'Daily\', \'BisInDie\', \'Weekly\', or \'Monthly\'')
        else:
            o.cadence = 'Once'

        if 'non_sidereal_json' in payload.keys() and len(payload['non_sidereal_json'].keys()):
            value = payload['non_sidereal_json']
            if isinstance(value, dict):
                valid_nsj = {'RA_BiasRate':[float,None], 'Dec_BiasRate':[float,None], 'ObjectRate':[float,None], 'PositionAngle':[float,None], 'UTC_At_Position':[datetime,'%Y-%m-%dT%H:%M:%S.%f']}
                keys = value.keys()
                valkeys = valid_nsj.keys()
                if all([key in valid_nsj.keys() and validator.isvalidInstance(val, valid_nsj[key][0], valid_nsj[key][1]) for key,val in value.items()]):
                    o.non_sidereal = True
                    o.non_sidereal_json = value
                else:
                    v.errors.append('Invalid format for field \'non_sidereal_json\'. Must be in the format of: {"RA_BiasRate": "0.0", "Dec_BiasRate": "0.0", "ObjectRate": "0.0", ' \
             '"PositionAngle": "0.0", "UTC_At_Position": "YYYY-MM-DDThh:mm:ss.s"}')
            else:
                v.errors.append('Invalid format for field \'non_sidereal_json\'. Must be in the format of: {"RA_BiasRate": "0.0", "Dec_BiasRate": "0.0", "ObjectRate": "0.0", ' \
             '"PositionAngle": "0.0", "UTC_At_Position": "YYYY-MM-DDThh:mm:ss.s"}')
        else:
            o.non_sidereal = False
            o.non_sidereal_json = {}

        o.priority_value
        o.created_iso = get_iso()
        o.created_mjd = float(iso_to_mjd(o.created_iso))
        o.observation_id = get_unique_hash()
        o.queued = False
        o.queued_iso = ARTN_ZERO_ISO
        o.queued_mjd = ARTN_ZERO_MJD
        o.completed = False
        o.completed_iso = ARTN_ZERO_ISO
        o.completed_mjd = ARTN_ZERO_MJD
        o.rts2_id = -1
        o.rts2_doc = {}


        #ARTN_ALLOWED_HEADERS_V2 = ('username', 'telescope', 'instrument', 'object_name', 'ra', 'dec',
        #                   'airmass', 'lunarphase', 'priority', 'photometric', 'guiding', 'non_sidereal',
        #                   'begin', 'end', 'binning', 'dither', 'cadence', 'non_sidereal_json')

        #returns Obsreq2, the valid class, and valid=True/False
        return o, v, len(v.errors) == 0

    # +
    # property: pretty_serialized()
    # -
    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    # +
    # method: serialized()
    # -
    def serialized(self, queuedonly=False):
        _exposures = ObsExposure.query.filter_by(obsreqid=self.id).all()
        
        if queuedonly:
            _exposures_serialized = [x.serialized() for x in _exposures if x.queued and not x.completed]
        else:
            _exposures_serialized = [x.serialized() for x in _exposures]
        
        _d = {
            'id': self.id,
            'username': self.username,
            'pi': self.pi,
            'created_iso': f'{self.created_iso}',
            'created_mjd': f'{self.created_mjd:.6f}',
            'observation_id': self.observation_id,
            'priority': self.priority,
            'priority_value': self.priority_value,
            'object_name': self.object_name,
            'ra_hms': self.ra_hms,
            'ra_deg': f'{self.ra_deg:.3f}',
            'dec_dms': self.dec_dms,
            'dec_deg': f'{self.dec_deg:.3f}',
            'begin_iso': f'{self.begin_iso}',
            'begin_mjd': f'{self.begin_mjd:.6f}',
            'end_iso': f'{self.end_iso}',
            'end_mjd': f'{self.end_mjd:.6f}',
            'airmass': f'{self.airmass:.2f}',
            'lunarphase': self.lunarphase,
            'moonphase': f'{self.moonphase:.1f}',
            'photometric': True if str(self.photometric).lower() in TRUE_VALUES else False,
            'guiding': True if str(self.guiding).lower() in TRUE_VALUES else False,
            'non_sidereal': True if str(self.non_sidereal).lower() in TRUE_VALUES else False,
            'binning': self.binning,
            'dither': self.dither,
            'cadence': self.cadence,
            'telescope': self.telescope,
            'instrument': self.instrument,
            'queued': True if str(self.queued).lower() in TRUE_VALUES else False,
            'queued_iso': self.queued_iso,
            'queued_mjd': self.queued_mjd,
            'completed': True if str(self.completed).lower() in TRUE_VALUES else False,
            'completed_iso': self.completed_iso,
            'completed_mjd': self.completed_mjd,
            'rts2_doc': str(self.rts2_doc),
            'rts2_id': int(self.rts2_id),
            'non_sidereal_json': str(self.non_sidereal_json),
            'user_id': self.user_id,
            'exposures':_exposures_serialized
        }
        return _d


    def stellar_dictify(self, _exposures=None):
        if _exposures == None:
            _exposures = ObsExposure.query.filter_by(obsreqid=self.id, queued=True, completed=False).all()
        thedict = {
            "name"  : self.object_name,
            "ra"    : self.ra_hms,
            "dec"   : self.dec_dms,
            "obs_id"    : self.rts2_id,
            "obs_info" : []
        }
        for obs in _exposures:
            thedict['obs_info'].append({
                "obsexpid": obs.id,
                "Filter"  : obs.filter_name,
                "exptime" : obs.exp_time,
                "amount"  : obs.num_exp,
            })

        self.rts2_doc = thedict
    # +
    # (overload) method: __str__()
    # -
    def __str__(self):
        return self.id

    # +
    # (overload) method: __repr__()
    # -
    def __repr__(self):
        _s = self.serialized()
        return f'<ObsReq {_s}>'

    # +
    # (static) method: serialize_list()
    # -
    @staticmethod
    def serialize_list(s_records):
        return [_s.serialized() for _s in s_records]


# +
# class: ObsExposure(), inherits from UserMixin, db.Model
# -
class ObsExposure(UserMixin, db.Model):
    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'obsexposure'
    _iso = get_iso()
    _mjd = float(iso_to_mjd(_iso))

    # +
    # table mapping
    # -
    # noinspection PyUnresolvedReferences
    id = db.Column(db.Integer, primary_key=True, index=True)
    # noinspection PyUnresolvedReferences
    obsreqid = db.Column(db.Integer, nullable=False)
    # noinspection PyUnresolvedReferences
    filter_name = db.Column(db.String(ARTN_CHAR_24), default='V', nullable=False)
    # noinspection PyUnresolvedReferences
    exp_time = db.Column(db.Float, default=0.0, nullable=False)
    # noinspection PyUnresolvedReferences
    num_exp = db.Column(db.Integer, default=1, nullable=False)
    # noinspection PyUnresolvedReferences
    completed = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    queued = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    filename = db.Column(db.String(ARTN_CHAR_256), default="", nullable=True)

    @staticmethod
    def validate_json(payload):
        v = _TableValidation()
        o = ObsExposure()

        if 'filter' in payload.keys():
            valid, msg = validator.validate_payload_field_inlist(payload, 'filter', ['U', 'B', 'V', 'R', 'I', 'Clear', 'Halpha'])
            if valid:
                o.filter_name = payload['filter']
            else:
                v.errors.append(msg)
        else:
            v.errors.append('Field \'{}\' is required'.format('filter'))

        if 'exp_time' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'exp_time', int)
            if valid:
                o.exp_time = val
            else:
                v.errors.append(msg)
        else:
            v.errors.append('Field \'{}\' is required'.format('exp_time'))

        if 'num_exp' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'num_exp', int)
            if valid:
                o.num_exp = val
            else:
                v.errors.append(msg)
        else:
            v.errors.append('Field \'{}\' is required'.format('num_exp'))


        if 'obsreqid' in payload.keys():
            val, valid, msg = validator.validate_payload_field(payload, 'obsreqid', int)
            if valid:
                o.obsreqid = val
            else:
                v.errors.append(msg)
        else:
            v.errors.append('Field \'{}\' is required'.format('obsreqid'))


        o.completed = False
        o.queued = False

        return o, v, len(v.errors) == 0


    def serialized(self):
        _d = {
            'id':self.id,
            'obsreqid':self.obsreqid,
            'filter_name':self.filter_name,
            'exp_time':self.exp_time,
            'num_exp':self.num_exp,
            'completed':str(self.completed),
            'queued':str(self.queued)
        }
        return _d

    @staticmethod
    def ObsExposuresFromPage(form):
        exposures = []
        for expid, filter_name, exp_time, num_exp in zip(
                form.getlist('expid'),
                form.getlist('filter_name'),
                form.getlist('exp_time'),
                form.getlist('num_exp'),
            ):

            if  str(expid) == "" or str(expid) == "None":
                exposures.append(
                    ObsExposure(
                        filter_name=filter_name,
                        exp_time=exp_time,
                        num_exp=num_exp,
                    )
                )
            else:
                exposures.append(
                    ObsExposure(
                        id=int(expid),
                        filter_name=filter_name,
                        exp_time=exp_time,
                        num_exp=num_exp,
                    )
                )
        return exposures


# +
# class: ObsReq(), inherits from UserMixin, db.Model
# -
class ObsReq(UserMixin, db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'obsreqs'
    _iso = get_iso()
    _mjd = float(iso_to_mjd(_iso))

    # +
    # table mapping
    # -
    # noinspection PyUnresolvedReferences
    id = db.Column(db.Integer, primary_key=True, index=True)
    # noinspection PyUnresolvedReferences
    username = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    pi = db.Column(db.String(ARTN_CHAR_256), nullable=False)
    # noinspection PyUnresolvedReferences
    created_iso = db.Column(db.DateTime, default=_iso, nullable=False)
    # noinspection PyUnresolvedReferences
    created_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    group_id = db.Column(db.String(ARTN_CHAR_128), default=get_unique_hash(), nullable=False, unique=True)
    # noinspection PyUnresolvedReferences
    observation_id = db.Column(db.String(ARTN_CHAR_128), default=get_unique_hash(), nullable=False, unique=True)
    # noinspection PyUnresolvedReferences
    priority = db.Column(db.String(ARTN_CHAR_16), default='Routine', nullable=False)
    # noinspection PyUnresolvedReferences
    priority_value = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    object_name = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    ra_hms = db.Column(db.String(ARTN_CHAR_16), nullable=False)
    # noinspection PyUnresolvedReferences
    ra_deg = db.Column(db.Float, default=math.nan, nullable=False)
    # noinspection PyUnresolvedReferences
    dec_dms = db.Column(db.String(ARTN_CHAR_16), nullable=False)
    # noinspection PyUnresolvedReferences
    dec_deg = db.Column(db.Float, default=math.nan, nullable=False)
    # noinspection PyUnresolvedReferences
    begin_iso = db.Column(db.DateTime, default=get_date_time(), nullable=False)
    # noinspection PyUnresolvedReferences
    begin_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    end_iso = db.Column(db.DateTime, default=get_date_time(30), nullable=False)
    # noinspection PyUnresolvedReferences
    end_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    airmass = db.Column(db.Float, default=1.0, nullable=False)
    # noinspection PyUnresolvedReferences
    lunarphase = db.Column(db.String(ARTN_CHAR_16), default='Dark', nullable=False)
    # noinspection PyUnresolvedReferences
    moonphase = db.Column(db.Float, default=0.0, nullable=False)
    # noinspection PyUnresolvedReferences
    photometric = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    guiding = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    non_sidereal = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    filter_name = db.Column(db.String(ARTN_CHAR_24), default='V', nullable=False)
    # noinspection PyUnresolvedReferences
    exp_time = db.Column(db.Float, default=0.0, nullable=False)
    # noinspection PyUnresolvedReferences
    num_exp = db.Column(db.Integer, default=1, nullable=False)
    # noinspection PyUnresolvedReferences
    binning = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    dither = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    cadence = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    telescope = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    instrument = db.Column(db.String(ARTN_CHAR_16), default='Any', nullable=False)
    # noinspection PyUnresolvedReferences
    rts2_doc = db.Column(JSONB, default={}, nullable=False)
    # noinspection PyUnresolvedReferences
    rts2_id = db.Column(db.Integer, default=-1, nullable=False)
    # noinspection PyUnresolvedReferences
    queued = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    queued_iso = db.Column(db.DateTime, default=get_date_time(0), nullable=False)
    # noinspection PyUnresolvedReferences
    queued_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    completed = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    completed_iso = db.Column(db.DateTime, default=get_date_time(0), nullable=False)
    # noinspection PyUnresolvedReferences
    completed_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    non_sidereal_json = db.Column(JSONB, default={}, nullable=False)

    # noinspection PyUnresolvedReferences
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # +
    # property: pretty_serialized()
    # -
    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    # +
    # method: serialized()
    # -
    def serialized(self):
        _d = {
            'id': int(self.id),
            'username': self.username,
            'pi': self.pi,
            'created_iso': f'{self.created_iso}',
            'created_mjd': f'{self.created_mjd:.6f}',
            'group_id': self.group_id,
            'observation_id': self.observation_id,
            'priority': self.priority,
            'priority_value': f'{self.priority_value:.6f}',
            'object_name': self.object_name,
            'ra_hms': self.ra_hms,
            'ra_deg': f'{self.ra_deg:.3f}',
            'dec_dms': self.dec_dms,
            'dec_deg': f'{self.dec_deg:.3f}',
            'begin_iso': f'{self.begin_iso}',
            'begin_mjd': f'{self.begin_mjd:.6f}',
            'end_iso': f'{self.end_iso}',
            'end_mjd': f'{self.end_mjd:.6f}',
            'airmass': f'{self.airmass:.2f}',
            'lunarphase': self.lunarphase,
            'moonphase': f'{self.moonphase:.1f}',
            'photometric': True if str(self.photometric).lower() in TRUE_VALUES else False,
            'guiding': True if str(self.guiding).lower() in TRUE_VALUES else False,
            'non_sidereal': True if str(self.non_sidereal).lower() in TRUE_VALUES else False,
            'filter_name': self.filter_name,
            'exp_time': f'{self.exp_time:.1f}',
            'num_exp': int(self.num_exp),
            'binning': self.binning,
            'dither': self.dither,
            'cadence': self.cadence,
            'telescope': self.telescope,
            'instrument': self.instrument,
            'queued': True if str(self.queued).lower() in TRUE_VALUES else False,
            'queued_iso': self.queued_iso.isoformat(),
            'queued_mjd': self.queued_mjd,
            'completed': True if str(self.completed).lower() in TRUE_VALUES else False,
            'completed_iso': self.completed_iso.isoformat(),
            'completed_mjd': self.completed_mjd,
            'rts2_doc': str(self.rts2_doc),
            'rts2_id': int(self.rts2_id),
            'non_sidereal_json': str(self.non_sidereal_json),
            'user_id': self.user_id
        }
        return _d

    # +
    # (overload) method: __str__()
    # -
    def __str__(self):
        return self.id

    # +
    # (overload) method: __repr__()
    # -
    def __repr__(self):
        _s = self.serialized()
        return f'<ObsReq {_s}>'

    # +
    # (static) method: serialize_list()
    # -
    @staticmethod
    def serialize_list(s_records):
        return [_s.serialized() for _s in s_records]


# +
# class: User(), inherits from UserMixin, db.Model
# -
# noinspection PyBroadException
class User(UserMixin, db.Model):

    # +
    # member variable(s)
    # -

    # define table name
    __tablename__ = 'users'
    _iso = get_iso()
    _mjd = iso_to_mjd(_iso)

    # +
    # table mapping
    # -
    # noinspection PyUnresolvedReferences
    id = db.Column(db.Integer, primary_key=True, index=True)
    # noinspection PyUnresolvedReferences
    firstname = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    lastname = db.Column(db.String(ARTN_CHAR_64), nullable=False)
    # noinspection PyUnresolvedReferences
    username = db.Column(db.String(ARTN_CHAR_64), nullable=False, unique=True)
    # noinspection PyUnresolvedReferences
    hashword = db.Column(db.String(ARTN_CHAR_128), nullable=False)
    # noinspection PyUnresolvedReferences
    passphrase = db.Column(db.String(ARTN_CHAR_128), nullable=False)
    # noinspection PyUnresolvedReferences
    email = db.Column(db.String(ARTN_CHAR_128), nullable=False, unique=True)
    # noinspection PyUnresolvedReferences
    affiliation = db.Column(db.String(ARTN_CHAR_256), nullable=False)
    # noinspection PyUnresolvedReferences
    created_iso = db.Column(db.DateTime, default=_iso, nullable=False)
    # noinspection PyUnresolvedReferences
    created_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    avatar = db.Column(db.String(ARTN_CHAR_128))
    # noinspection PyUnresolvedReferences
    about_me = db.Column(db.String(ARTN_CHAR_256))
    # noinspection PyUnresolvedReferences
    last_seen_iso = db.Column(db.DateTime, default=_iso, nullable=False)
    # noinspection PyUnresolvedReferences
    last_seen_mjd = db.Column(db.Float, default=_mjd, nullable=False)
    # noinspection PyUnresolvedReferences
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    is_disabled = db.Column(db.Boolean, default=False, nullable=False)
    # noinspection PyUnresolvedReferences
    api_token = db.Column(db.String(ARTN_CHAR_128))

    # noinspection PyUnresolvedReferences
    obsreqs = db.relationship('ObsReq', backref='author', lazy='dynamic')

    # +
    # property: pretty_serialized()
    # -
    @property
    def pretty_serialized(self):
        return json.dumps(self.serialized(), indent=2)

    # +
    # method: set_password()
    # -
    def set_password(self, password=''):
        self.hashword = generate_password_hash(password)

    # +
    # method: check_password()
    # -
    def check_password(self, password=''):
        return check_password_hash(self.hashword, password)

    # +
    # method: get_avatar()
    # -
    def get_avatar(self, size=64):
        return f'{self.avatar}?d=identicon&s={size}'

    # +
    # method: get_reset_password_token()
    # -
    def get_reset_password_token(self, expires_in=604800):
        return jwt.encode({'reset_password': self.id, 'exp': time()+expires_in},
                          ARTN_SECRET_KEY, algorithm='HS256').decode('utf-8')

    # +
    # method: get_confirm_registration_token()
    # -
    def get_confirm_registration_token(self, expires_in=604800):
        return jwt.encode({'confirm_registration': self.id, 'exp': time()+expires_in},
                          ARTN_SECRET_KEY, algorithm='HS256').decode('utf-8')

    
    def set_apitoken(self):
        self.api_token = secrets.token_urlsafe(28)

    
    def check_apitoken(self, token):
        return token == self.api_token    


    # +
    # method: serialized()
    # -
    def serialized(self):
        _d = {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'username': self.username,
            'hashword': self.hashword,
            'passphrase': self.passphrase,
            'email': self.email,
            'affiliation': self.affiliation,
            'created_iso': self.created_iso,
            'created_mjd': self.created_mjd,
            'avatar': self.avatar,
            'about_me': self.about_me,
            'last_seen_iso': self.last_seen_iso,
            'last_seen_mjd': self.last_seen_mjd,
            'is_admin': True if str(self.is_admin).lower() in TRUE_VALUES else False,
            'is_disabled': True if str(self.is_disabled).lower() in TRUE_VALUES else False
        }
        # logger.debug(f"User() serialized: {_d}")
        return _d

    # +
    # (overload) method: __str__()
    # -
    def __str__(self):
        return self.id

    # +
    # (overload) method: __repr__()
    # -
    def __repr__(self):
        _s = self.serialized()
        return f'<Users {_s}>'

    # +
    # (static) method: verify_reset_password_token()
    # -
    @staticmethod
    def verify_reset_password_token(token=None):
        try:
            return User.query.get(jwt.decode(token, ARTN_SECRET_KEY, algorithms=['HS256'])['reset_password'])
        except Exception:
            return None

    # +
    # (static) method: verify_confirm_registration_token()
    # -
    @staticmethod
    def verify_confirm_registration_token(token=None):
        try:
            return User.query.get(jwt.decode(token, ARTN_SECRET_KEY, algorithms=['HS256'])['confirm_registration'])
        except Exception:
            return None

    # +
    # (static) method: serialize_list()
    # -
    @staticmethod
    def serialize_list(s_records):
        return [_s.serialized() for _s in s_records]


# +
# function: obsreq_filters()
# -
def obsreq2_filters(query, request_args):

    # obsreq records with id = value (API: ?id=20)
    if request_args.get('id'):
        query = query.filter(ObsReq2.id == int(request_args['id']))

    # obsreq records with id <= value (API: ?id__lte=20)
    if request_args.get('id__lte'):
        query = query.filter(ObsReq2.id <= int(request_args['id__lte']))

    # obsreq records with id >= value (API: ?id__gte=20)
    if request_args.get('id__gte'):
        query = query.filter(ObsReq2.id >= int(request_args['id__gte']))

    # obsreq records with username like value (API: ?username=demo)
    if request_args.get('username'):
        query = query.filter(ObsReq2.username.ilike(f"%{request_args['username']}%"))

    # obsreq records with username not like value (API: ?exclude_username=demo)
    if request_args.get('exclude_username'):
        query = query.filter(not_(ObsReq2.username.ilike(f"%{request_args['exclude_username']}%")))

    # obsreq records with pi like value (API: ?pi=demo)
    if request_args.get('pi'):
        query = query.filter(ObsReq2.pi.ilike(f"%{request_args['pi']}%"))

    # obsreq records with a created_iso >= date (API: ?created_iso__gte=2018-07-17)
    if request_args.get('created_iso__gte'):
        a_time = Time(request_args['created_iso__gte'], format='isot')
        query = query.filter(ObsReq2.created_mjd >= float(a_time.mjd))

    # obsreq records with a created_iso <= date (API: ?created_iso__lte=2018-07-17)
    if request_args.get('created_iso__lte'):
        a_time = Time(request_args['created_iso__lte'], format='isot')
        query = query.filter(ObsReq2.created_mjd <= float(a_time.mjd))

    # obsreq records with created_mjd >= value (API: ?created_mjd__gte=58526.54609935184998903)
    if request_args.get('created_mjd__gte'):
        query = query.filter(ObsReq2.created_mjd >= float(request_args['created_mjd__gte']))

    # obsreq records with created_mjd <= value (API: ?created_mjd__lte=58526.54609935184998903)
    if request_args.get('created_mjd__lte'):
        query = query.filter(ObsReq2.created_mjd <= float(request_args['created_mjd__lte']))

    # obsreq records with group_id like value (API: ?group_id=abcd)
    if request_args.get('group_id'):
        query = query.filter(ObsReq2.group_id.ilike(f"%{request_args['group_id']}%"))

    # obsreq records with observation_id like value (API: ?observation_id=abcd)
    if request_args.get('observation_id'):
        query = query.filter(ObsReq2.observation_id.ilike(f"%{request_args['observation_id']}%"))

    # obsreq records with priority like value (API: ?priority=Routine)
    if request_args.get('priority'):
        query = query.filter(ObsReq2.priority.ilike(f"%{request_args['priority']}%"))

    # obsreq records with priority_value >= value (API: ?priority_value__gte=58526.54609935184998903)
    if request_args.get('priority_value__gte'):
        query = query.filter(ObsReq2.priority_value >= float(request_args['priority_value__gte']))

    # obsreq records with priority_value <= value (API: ?priority_value__lte=58526.54609935184998903)
    if request_args.get('priority_value__lte'):
        query = query.filter(ObsReq2.priority_value <= float(request_args['priority_value__lte']))

    # obsreq records with object_name like value (API: ?object_name=abcd)
    if request_args.get('object_name'):
        query = query.filter(ObsReq2.object_name.ilike(f"%{request_args['object_name']}%"))

    # obsreq records with ra_hms like value (API: ?ra_hms=12:12:12)
    if request_args.get('ra_hms'):
        query = query.filter(ObsReq2.ra_hms.ilike(f"%{request_args['ra_hms']}%"))

    # obsreq records with ra_deg >= value (API: ?ra_deg__gte=58526.54609935184998903)
    if request_args.get('ra_deg__gte'):
        query = query.filter(ObsReq2.ra_deg >= float(request_args['ra_deg__gte']))

    # obsreq records with ra_deg <= value (API: ?ra_deg__lte=58526.54609935184998903)
    if request_args.get('ra_deg__lte'):
        query = query.filter(ObsReq2.ra_deg <= float(request_args['ra_deg__lte']))

    # obsreq records with dec_dms like value (API: ?dec_dms=30:30:30)
    if request_args.get('dec_dms'):
        query = query.filter(ObsReq2.dec_dms.ilike(f"%{request_args['dec_dms']}%"))

    # obsreq records with dec_deg >= value (API: ?dec_deg__gte=58526.54609935184998903)
    if request_args.get('dec_deg__gte'):
        query = query.filter(ObsReq2.dec_deg >= float(request_args['dec_deg__gte']))

    # obsreq records with dec_deg >= value (API: ?dec_deg__lte=58526.54609935184998903)
    if request_args.get('dec_deg__lte'):
        query = query.filter(ObsReq2.dec_deg <= float(request_args['dec_deg__lte']))

    # obsreq records with a begin_iso >= date (API: ?begin_iso__gte=2018-07-17)
    if request_args.get('begin_iso__gte'):
        a_time = Time(request_args['begin_iso__gte'], format='isot')
        query = query.filter(ObsReq2.begin_mjd >= float(a_time.mjd))

    # obsreq records with a begin_iso <= date (API: ?begin_iso__lte=2018-07-17)
    if request_args.get('begin_iso__lte'):
        a_time = Time(request_args['begin_iso__lte'], format='isot')
        query = query.filter(ObsReq2.begin_mjd <= float(a_time.mjd))

    # obsreq records with begin_mjd >= value (API: ?begin_mjd__gte=58526.54609935184998903)
    if request_args.get('begin_mjd__gte'):
        query = query.filter(ObsReq2.begin_mjd >= float(request_args['begin_mjd__gte']))

    # obsreq records with begin_mjd <= value (API: ?begin_mjd__lte=58526.54609935184998903)
    if request_args.get('begin_mjd__lte'):
        query = query.filter(ObsReq2.begin_mjd <= float(request_args['begin_mjd__lte']))

    # obsreq records with a end_iso >= date (API: ?end_iso__gte=2018-07-17)
    if request_args.get('end_iso__gte'):
        a_time = Time(request_args['end_iso__gte'], format='isot')
        query = query.filter(ObsReq2.end_mjd >= float(a_time.mjd))

    # obsreq records with a end_iso <= date (API: ?end_iso__lte=2018-07-17)
    if request_args.get('end_iso__lte'):
        a_time = Time(request_args['end_iso__lte'], format='isot')
        query = query.filter(ObsReq2.end_mjd <= float(a_time.mjd))

    # obsreq records with end_mjd >= value (API: ?end_mjd__gte=58526.54609935184998903)
    if request_args.get('end_mjd__gte'):
        query = query.filter(ObsReq2.end_mjd >= float(request_args['end_mjd__gte']))

    # obsreq records with end_mjd <= value (API: ?end_mjd__lte=58526.54609935184998903)
    if request_args.get('end_mjd__lte'):
        query = query.filter(ObsReq2.end_mjd <= float(request_args['end_mjd__lte']))

    # obsreq records with airmass >= value (API: ?airmass__gte=58526.54609935184998903)
    if request_args.get('airmass__gte'):
        query = query.filter(ObsReq2.airmass >= float(request_args['airmass__gte']))

    # obsreq records with airmass <= value (API: ?airmass__lte=58526.54609935184998903)
    if request_args.get('airmass__lte'):
        query = query.filter(ObsReq2.airmass <= float(request_args['airmass__lte']))

    # obsreq records with lunarphase like value (API: ?lunarphase=Dark)
    if request_args.get('lunarphase'):
        query = query.filter(ObsReq2.lunarphase.ilike(f"%{request_args['lunarphase']}%"))

    # obsreq records with moonphase >= value (API: ?moonphase__gte=58526.54609935184998903)
    if request_args.get('moonphase__gte'):
        query = query.filter(ObsReq2.moonphase >= float(request_args['moonphase__gte']))

    # obsreq records with moonphase <= value (API: ?moonphase__lte=58526.54609935184998903)
    if request_args.get('moonphase__lte'):
        query = query.filter(ObsReq2.moonphase <= float(request_args['moonphase__lte']))

    # obsreq records with photometric = boolean (API: ?photometric=True)
    if request_args.get('photometric'):
        query = query.filter(ObsReq2.photometric == request_args.get('photometric').lower() in TRUE_VALUES)

    # obsreq records with guiding = boolean (API: ?guiding=True)
    if request_args.get('guiding'):
        query = query.filter(ObsReq2.guiding == request_args.get('guiding').lower() in TRUE_VALUES)

    # obsreq records with non_sidereal = boolean (API: ?non_sidereal=True)
    if request_args.get('non_sidereal'):
        if request_args.get('non_sidereal').lower() in TRUE_VALUES:
            query = query.filter(ObsReq2.non_sidereal is True)
        else:
            query = query.filter(ObsReq2.non_sidereal is False)

    # obsreq records with filter_name like value (API: ?filter=V)
    #if request_args.get('filter_name'):
    #    query = query.filter(ObsReq.filter_name.ilike(f"%{request_args['filter_name']}%"))

    # obsreq records with exp_time >= value (API: ?exp_time__gte=58526.54609935184998903)
    #if request_args.get('exp_time__gte'):
    #    query = query.filter(ObsReq.exp_time >= float(request_args['exp_time__gte']))

    # obsreq records with exp_time <= value (API: ?exp_time__lte=58526.54609935184998903)
    #if request_args.get('exp_time__lte'):
    #    query = query.filter(ObsReq.exp_time <= float(request_args['exp_time__lte']))

    # obsreq records with num_exp >= value (API: ?num_exp__gte=20)
    #if request_args.get('num_exp__gte'):
    #    query = query.filter(ObsReq.num_exp >= int(request_args['num_exp__gte']))

    # obsreq records with num_exp <= value (API: ?num_exp__lte=20)
    #if request_args.get('num_exp__lte'):
    #    query = query.filter(ObsReq.num_exp <= int(request_args['num_exp__lte']))

    # obsreq records with binning like value (API: ?binning=1x1)
    if request_args.get('binning'):
        query = query.filter(ObsReq2.binning.ilike(f"%{request_args['binning']}%"))

    # obsreq records with dither like value (API: ?dither=1x1)
    if request_args.get('dither'):
        query = query.filter(ObsReq2.dither.ilike(f"%{request_args['dither']}%"))

    # obsreq records with cadence like value (API: ?cadence=Once)
    if request_args.get('cadence'):
        query = query.filter(ObsReq2.cadence.ilike(f"%{request_args['cadence']}%"))

    # obsreq records with telescope like value (API: ?telescope=Kuiper)
    if request_args.get('telescope'):
        query = query.filter(ObsReq2.telescope.ilike(f"%{request_args['telescope']}%"))

    # obsreq records with instrument like value (API: ?instrument=Mont4k)
    if request_args.get('instrument'):
        query = query.filter(ObsReq2.instrument.ilike(f"%{request_args['instrument']}%"))

    # obsreq records with queued = boolean (API: ?queued=True)
    if request_args.get('queued'):
        query = query.filter(ObsReq2.queued == request_args.get('queued').lower() in TRUE_VALUES)

    # obsreq records with completed = boolean (API: ?completed=True)
    if request_args.get('completed'):
        query = query.filter(ObsReq2.completed == request_args.get('completed').lower() in TRUE_VALUES)

    # obsreq records with rts2_doc__key (API: ?rts2_doc__key=obs_info)
    if request_args.get('rts2_doc__key'):
        query = query.filter(ObsReq2.rts2_doc[f"{request_args['rts2_doc__key']}"].astext != '')

    # obsreq records with rts2_id <= value (API: ?rts2_id__lte=20)
    if request_args.get('rts2_id__lte'):
        query = query.filter(ObsReq2.rts2_id <= int(request_args['rts2_id__lte']))

    # obsreq records with rts2_id >= value (API: ?rts2_id__gte=20)
    if request_args.get('rts2_id__gte'):
        query = query.filter(ObsReq2.rts2_id >= int(request_args['rts2_id__gte']))

    # obsreq records with non_sidereal__key (API: ?non_sidereal__key=RA_BiasRate)
    if request_args.get('non_sidereal__key'):
        query = query.filter(ObsReq2.non_sidereal_json[f"{request_args['non_sidereal__key']}"].astext != '')

    # obsreq records with user_id <= value (API: ?user_id__lte=20)
    if request_args.get('user_id__lte'):
        query = query.filter(ObsReq2.user_id <= int(request_args['user_id__lte']))

    # obsreq records with user_id >= value (API: ?user_id__gte=20)
    if request_args.get('user_id__gte'):
        query = query.filter(ObsReq2.user_id >= int(request_args['user_id__gte']))

    # sort results
    if request_args.get('sort_field') and request_args.get('sort_order'):
        if request_args['sort_order'].lower() == 'descending':
            query = query.order_by(getattr(ObsReq2, request_args['sort_field']).desc())
        else:
            query = query.order_by(getattr(ObsReq2, request_args['sort_field']).asc())

    # return query
    return query

# +
# function: obsreq_filters()
# -
def obsreq_filters(query, request_args):

    # obsreq records with id = value (API: ?id=20)
    if request_args.get('id'):
        query = query.filter(ObsReq.id == int(request_args['id']))

    # obsreq records with id <= value (API: ?id__lte=20)
    if request_args.get('id__lte'):
        query = query.filter(ObsReq.id <= int(request_args['id__lte']))

    # obsreq records with id >= value (API: ?id__gte=20)
    if request_args.get('id__gte'):
        query = query.filter(ObsReq.id >= int(request_args['id__gte']))

    # obsreq records with username like value (API: ?username=demo)
    if request_args.get('username'):
        query = query.filter(ObsReq.username.ilike(f"%{request_args['username']}%"))

    # obsreq records with username not like value (API: ?exclude_username=demo)
    if request_args.get('exclude_username'):
        query = query.filter(not_(ObsReq.username.ilike(f"%{request_args['exclude_username']}%")))

    # obsreq records with pi like value (API: ?pi=demo)
    if request_args.get('pi'):
        query = query.filter(ObsReq.pi.ilike(f"%{request_args['pi']}%"))

    # obsreq records with a created_iso >= date (API: ?created_iso__gte=2018-07-17)
    if request_args.get('created_iso__gte'):
        a_time = Time(request_args['created_iso__gte'], format='isot')
        query = query.filter(ObsReq.created_mjd >= float(a_time.mjd))

    # obsreq records with a created_iso <= date (API: ?created_iso__lte=2018-07-17)
    if request_args.get('created_iso__lte'):
        a_time = Time(request_args['created_iso__lte'], format='isot')
        query = query.filter(ObsReq.created_mjd <= float(a_time.mjd))

    # obsreq records with created_mjd >= value (API: ?created_mjd__gte=58526.54609935184998903)
    if request_args.get('created_mjd__gte'):
        query = query.filter(ObsReq.created_mjd >= float(request_args['created_mjd__gte']))

    # obsreq records with created_mjd <= value (API: ?created_mjd__lte=58526.54609935184998903)
    if request_args.get('created_mjd__lte'):
        query = query.filter(ObsReq.created_mjd <= float(request_args['created_mjd__lte']))

    # obsreq records with group_id like value (API: ?group_id=abcd)
    if request_args.get('group_id'):
        query = query.filter(ObsReq.group_id.ilike(f"%{request_args['group_id']}%"))

    # obsreq records with observation_id like value (API: ?observation_id=abcd)
    if request_args.get('observation_id'):
        query = query.filter(ObsReq.observation_id.ilike(f"%{request_args['observation_id']}%"))

    # obsreq records with priority like value (API: ?priority=Routine)
    if request_args.get('priority'):
        query = query.filter(ObsReq.priority.ilike(f"%{request_args['priority']}%"))

    # obsreq records with priority_value >= value (API: ?priority_value__gte=58526.54609935184998903)
    if request_args.get('priority_value__gte'):
        query = query.filter(ObsReq.priority_value >= float(request_args['priority_value__gte']))

    # obsreq records with priority_value <= value (API: ?priority_value__lte=58526.54609935184998903)
    if request_args.get('priority_value__lte'):
        query = query.filter(ObsReq.priority_value <= float(request_args['priority_value__lte']))

    # obsreq records with object_name like value (API: ?object_name=abcd)
    if request_args.get('object_name'):
        query = query.filter(ObsReq.object_name.ilike(f"%{request_args['object_name']}%"))

    # obsreq records with ra_hms like value (API: ?ra_hms=12:12:12)
    if request_args.get('ra_hms'):
        query = query.filter(ObsReq.ra_hms.ilike(f"%{request_args['ra_hms']}%"))

    # obsreq records with ra_deg >= value (API: ?ra_deg__gte=58526.54609935184998903)
    if request_args.get('ra_deg__gte'):
        query = query.filter(ObsReq.ra_deg >= float(request_args['ra_deg__gte']))

    # obsreq records with ra_deg <= value (API: ?ra_deg__lte=58526.54609935184998903)
    if request_args.get('ra_deg__lte'):
        query = query.filter(ObsReq.ra_deg <= float(request_args['ra_deg__lte']))

    # obsreq records with dec_dms like value (API: ?dec_dms=30:30:30)
    if request_args.get('dec_dms'):
        query = query.filter(ObsReq.dec_dms.ilike(f"%{request_args['dec_dms']}%"))

    # obsreq records with dec_deg >= value (API: ?dec_deg__gte=58526.54609935184998903)
    if request_args.get('dec_deg__gte'):
        query = query.filter(ObsReq.dec_deg >= float(request_args['dec_deg__gte']))

    # obsreq records with dec_deg >= value (API: ?dec_deg__lte=58526.54609935184998903)
    if request_args.get('dec_deg__lte'):
        query = query.filter(ObsReq.dec_deg <= float(request_args['dec_deg__lte']))

    # obsreq records with a begin_iso >= date (API: ?begin_iso__gte=2018-07-17)
    if request_args.get('begin_iso__gte'):
        a_time = Time(request_args['begin_iso__gte'], format='isot')
        query = query.filter(ObsReq.begin_mjd >= float(a_time.mjd))

    # obsreq records with a begin_iso <= date (API: ?begin_iso__lte=2018-07-17)
    if request_args.get('begin_iso__lte'):
        a_time = Time(request_args['begin_iso__lte'], format='isot')
        query = query.filter(ObsReq.begin_mjd <= float(a_time.mjd))

    # obsreq records with begin_mjd >= value (API: ?begin_mjd__gte=58526.54609935184998903)
    if request_args.get('begin_mjd__gte'):
        query = query.filter(ObsReq.begin_mjd >= float(request_args['begin_mjd__gte']))

    # obsreq records with begin_mjd <= value (API: ?begin_mjd__lte=58526.54609935184998903)
    if request_args.get('begin_mjd__lte'):
        query = query.filter(ObsReq.begin_mjd <= float(request_args['begin_mjd__lte']))

    # obsreq records with a end_iso >= date (API: ?end_iso__gte=2018-07-17)
    if request_args.get('end_iso__gte'):
        a_time = Time(request_args['end_iso__gte'], format='isot')
        query = query.filter(ObsReq.end_mjd >= float(a_time.mjd))

    # obsreq records with a end_iso <= date (API: ?end_iso__lte=2018-07-17)
    if request_args.get('end_iso__lte'):
        a_time = Time(request_args['end_iso__lte'], format='isot')
        query = query.filter(ObsReq.end_mjd <= float(a_time.mjd))

    # obsreq records with end_mjd >= value (API: ?end_mjd__gte=58526.54609935184998903)
    if request_args.get('end_mjd__gte'):
        query = query.filter(ObsReq.end_mjd >= float(request_args['end_mjd__gte']))

    # obsreq records with end_mjd <= value (API: ?end_mjd__lte=58526.54609935184998903)
    if request_args.get('end_mjd__lte'):
        query = query.filter(ObsReq.end_mjd <= float(request_args['end_mjd__lte']))

    # obsreq records with airmass >= value (API: ?airmass__gte=58526.54609935184998903)
    if request_args.get('airmass__gte'):
        query = query.filter(ObsReq.airmass >= float(request_args['airmass__gte']))

    # obsreq records with airmass <= value (API: ?airmass__lte=58526.54609935184998903)
    if request_args.get('airmass__lte'):
        query = query.filter(ObsReq.airmass <= float(request_args['airmass__lte']))

    # obsreq records with lunarphase like value (API: ?lunarphase=Dark)
    if request_args.get('lunarphase'):
        query = query.filter(ObsReq.lunarphase.ilike(f"%{request_args['lunarphase']}%"))

    # obsreq records with moonphase >= value (API: ?moonphase__gte=58526.54609935184998903)
    if request_args.get('moonphase__gte'):
        query = query.filter(ObsReq.moonphase >= float(request_args['moonphase__gte']))

    # obsreq records with moonphase <= value (API: ?moonphase__lte=58526.54609935184998903)
    if request_args.get('moonphase__lte'):
        query = query.filter(ObsReq.moonphase <= float(request_args['moonphase__lte']))

    # obsreq records with photometric = boolean (API: ?photometric=True)
    if request_args.get('photometric'):
        query = query.filter(ObsReq.photometric == request_args.get('photometric').lower() in TRUE_VALUES)

    # obsreq records with guiding = boolean (API: ?guiding=True)
    if request_args.get('guiding'):
        query = query.filter(ObsReq.guiding == request_args.get('guiding').lower() in TRUE_VALUES)

    # obsreq records with non_sidereal = boolean (API: ?non_sidereal=True)
    if request_args.get('non_sidereal'):
        if request_args.get('non_sidereal').lower() in TRUE_VALUES:
            query = query.filter(ObsReq.non_sidereal is True)
        else:
            query = query.filter(ObsReq.non_sidereal is False)

    # obsreq records with filter_name like value (API: ?filter=V)
    if request_args.get('filter_name'):
        query = query.filter(ObsReq.filter_name.ilike(f"%{request_args['filter_name']}%"))

    # obsreq records with exp_time >= value (API: ?exp_time__gte=58526.54609935184998903)
    if request_args.get('exp_time__gte'):
        query = query.filter(ObsReq.exp_time >= float(request_args['exp_time__gte']))

    # obsreq records with exp_time <= value (API: ?exp_time__lte=58526.54609935184998903)
    if request_args.get('exp_time__lte'):
        query = query.filter(ObsReq.exp_time <= float(request_args['exp_time__lte']))

    # obsreq records with num_exp >= value (API: ?num_exp__gte=20)
    if request_args.get('num_exp__gte'):
        query = query.filter(ObsReq.num_exp >= int(request_args['num_exp__gte']))

    # obsreq records with num_exp <= value (API: ?num_exp__lte=20)
    if request_args.get('num_exp__lte'):
        query = query.filter(ObsReq.num_exp <= int(request_args['num_exp__lte']))

    # obsreq records with binning like value (API: ?binning=1x1)
    if request_args.get('binning'):
        query = query.filter(ObsReq.binning.ilike(f"%{request_args['binning']}%"))

    # obsreq records with dither like value (API: ?dither=1x1)
    if request_args.get('dither'):
        query = query.filter(ObsReq.dither.ilike(f"%{request_args['dither']}%"))

    # obsreq records with cadence like value (API: ?cadence=Once)
    if request_args.get('cadence'):
        query = query.filter(ObsReq.cadence.ilike(f"%{request_args['cadence']}%"))

    # obsreq records with telescope like value (API: ?telescope=Kuiper)
    if request_args.get('telescope'):
        query = query.filter(ObsReq.telescope.ilike(f"%{request_args['telescope']}%"))

    # obsreq records with instrument like value (API: ?instrument=Mont4k)
    if request_args.get('instrument'):
        query = query.filter(ObsReq.instrument.ilike(f"%{request_args['instrument']}%"))

    # obsreq records with queued = boolean (API: ?queued=True)
    if request_args.get('queued'):
        query = query.filter(ObsReq.queued == request_args.get('queued').lower() in TRUE_VALUES)

    # obsreq records with completed = boolean (API: ?completed=True)
    if request_args.get('completed'):
        query = query.filter(ObsReq.completed == request_args.get('completed').lower() in TRUE_VALUES)

    # obsreq records with rts2_doc__key (API: ?rts2_doc__key=obs_info)
    if request_args.get('rts2_doc__key'):
        query = query.filter(ObsReq.rts2_doc[f"{request_args['rts2_doc__key']}"].astext != '')

    # obsreq records with rts2_id <= value (API: ?rts2_id__lte=20)
    if request_args.get('rts2_id__lte'):
        query = query.filter(ObsReq.rts2_id <= int(request_args['rts2_id__lte']))

    # obsreq records with rts2_id >= value (API: ?rts2_id__gte=20)
    if request_args.get('rts2_id__gte'):
        query = query.filter(ObsReq.rts2_id >= int(request_args['rts2_id__gte']))

    # obsreq records with non_sidereal__key (API: ?non_sidereal__key=RA_BiasRate)
    if request_args.get('non_sidereal__key'):
        query = query.filter(ObsReq.non_sidereal_json[f"{request_args['non_sidereal__key']}"].astext != '')

    # obsreq records with user_id <= value (API: ?user_id__lte=20)
    if request_args.get('user_id__lte'):
        query = query.filter(ObsReq.user_id <= int(request_args['user_id__lte']))

    # obsreq records with user_id >= value (API: ?user_id__gte=20)
    if request_args.get('user_id__gte'):
        query = query.filter(ObsReq.user_id >= int(request_args['user_id__gte']))

    # sort results
    if request_args.get('sort_field') and request_args.get('sort_order'):
        if request_args['sort_order'].lower() == 'descending':
            query = query.order_by(getattr(ObsReq, request_args['sort_field']).desc())
        else:
            query = query.order_by(getattr(ObsReq, request_args['sort_field']).asc())

    # return query
    return query


# +
# function: user_filters()
# -
def user_filters(query, request_args=None):

    # user records with id = value (API: ?id=20)
    if request_args.get('id'):
        query = query.filter(User.id == int(request_args['id']))

    # user records with id >= value (API: ?id__gte=20)
    if request_args.get('id__gte'):
        query = query.filter(User.id >= int(request_args['id__gte']))

    # user records with id <= value (API: ?id__lte=20)
    if request_args.get('id__lte'):
        query = query.filter(User.id <= int(request_args['id__lte']))

    # user records with firstname like value (API: ?firstname=demo)
    if request_args.get('firstname'):
        query = query.filter(User.firstname.ilike(f"%{request_args['firstname']}%"))

    # user records with lastname like value (API: ?lastname=demo)
    if request_args.get('lastname'):
        query = query.filter(User.lastname.ilike(f"%{request_args['lastname']}%"))

    # user records with username like value (API: ?username=demo)
    if request_args.get('username'):
        query = query.filter(User.username.ilike(f"%{request_args['username']}%"))

    # user records with email like value (API: ?email=demo@example.com)
    if request_args.get('email'):
        query = query.filter(User.email.ilike(f"%{request_args['email']}%"))

    # user records with affiliation like value (API: ?affiliation='Example Inc')
    if request_args.get('affiliation'):
        query = query.filter(User.affiliation.ilike(f"%{request_args['affiliation']}%"))

    # user records with a created_iso >= date (API: ?created_iso__gte=2018-07-17)
    if request_args.get('created_iso__gte'):
        a_time = Time(request_args['created_iso__gte'], format='isot')
        query = query.filter(User.created_mjd >= float(a_time.mjd))

    # user records with a created_iso <= date (API: ?created_iso__lte=2018-07-17)
    if request_args.get('created_iso__lte'):
        a_time = Time(request_args['created_iso__lte'], format='isot')
        query = query.filter(User.created_mjd <= float(a_time.mjd))

    # user records with created_mjd >= value (API: ?created_mjd__gte=58526.54609935184998903)
    if request_args.get('created_mjd__gte'):
        query = query.filter(User.created_mjd >= float(request_args['created_mjd__gte']))

    # user records with created_mjd <= value (API: ?created_mjd__lte=58526.54609935184998903)
    if request_args.get('created_mjd__lte'):
        query = query.filter(User.created_mjd <= float(request_args['created_mjd__lte']))

    # user records with a last_seen_iso >= date (API: ?last_seen_iso__gte=2018-07-17)
    if request_args.get('last_seen_iso__gte'):
        a_time = Time(request_args['last_seen_iso__gte'], format='isot')
        query = query.filter(User.last_seen_mjd >= float(a_time.mjd))

    # user records with a last_seen_iso <= date (API: ?last_seen_iso__lte=2018-07-17)
    if request_args.get('last_seen_iso__lte'):
        a_time = Time(request_args['last_seen_iso__lte'], format='isot')
        query = query.filter(User.last_seen_mjd <= float(a_time.mjd))

    # user records with last_seen_mjd >= value (API: ?last_seen_mjd__gte=58526.54609935184998903)
    if request_args.get('last_seen_mjd__gte'):
        query = query.filter(User.last_seen_mjd >= float(request_args['last_seen_mjd__gte']))

    # user records with last_seen_mjd <= value (API: ?last_seen_mjd__lte=58526.54609935184998903)
    if request_args.get('last_seen_mjd__lte'):
        query = query.filter(User.last_seen_mjd <= float(request_args['last_seen_mjd__lte']))

    # user records with is_admin == bool (API: ?is_admin=True)
    if request_args.get('is_admin'):
        query = query.filter(User.is_admin == request_args.get('is_admin').lower() in TRUE_VALUES)

    # user records with is_disabled == bool (API: ?is_disabled=False)
    if request_args.get('is_disabled'):
        query = query.filter(User.is_disabled == request_args.get('is_disabled').lower() in TRUE_VALUES)

    # sort results
    if request_args.get('sort_field') and request_args.get('sort_order'):
        if request_args['sort_order'].lower() == 'descending':
            query = query.order_by(getattr(ObsReq, request_args['sort_field']).desc())
        else:
            query = query.order_by(getattr(ObsReq, request_args['sort_field']).asc())

    # return query
    return query
