#!/usr/bin/env python3.7


# +
# import(s)
# -
from . import *
from astroplan import Observer
from astropy.coordinates import Angle, AltAz, EarthLocation, SkyCoord, get_moon, get_sun
from astropy.time import Time
from astropy import units as u
from datetime import datetime, timedelta

import argparse
import base64
import io
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import random
import re
import sys
import unicodedata


# +
# constant(s)
# -
AST__4_MINUTES = 360
AST__5_MINUTES = 289
AST__EAST = 90.0
AST__HORIZON = 0.0
AST__NADIR = -90.0
AST__NORTH = 0.0
AST__SOUTH = 180.0
AST__WEST = 270.0
AST__TWILIGHT_6 = -6.0
AST__TWILIGHT_12 = -12.0
AST__TWILIGHT_18 = -18.0
AST__ZENITH = 90.0

M_TO_FT = 3.28083
FT_TO_M = 1.0 / M_TO_FT

ISO__PATTERN = '[0-9]{4}-[0-9]{2}-[0-9]{2}[ T?][0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6}'

MAX__ALTITUDE = 8000.0
MAX__DECLINATION = 90.0
MAX__LATITUDE = 90.0
MAX__LONGITUDE = 360.0
MAX__RIGHT_ASCENSION = 360.0

MIN__ALTITUDE = 0.0
MIN__DECLINATION = -90.0
MIN__LATITUDE = -90.0
MIN__LONGITUDE = -360.0
MIN__RIGHT_ASCENSION = 0.0

VAL__NOT_OBSERVABLE = 0.0
VAL__OBSERVABLE = 1.0

RAN_SEED = random.seed()

UNI__DEGREE = unicodedata.lookup('DEGREE SIGN')
UNI__ARCMIN = unicodedata.lookup('PRIME')
UNI__ARCSEC = unicodedata.lookup('DOUBLE PRIME')
UNI__PROPORTIONAL = unicodedata.lookup('PROPORTIONAL TO')


# +
# default(s)
# -
DEF__BEGIN = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
DEF__DECLINATION = 0.0
DEF__DMS = '00:00:00.000 degrees'
DEF__END = (datetime.utcnow() + timedelta(30)).strftime("%Y-%m-%d %H:%M:%S.%f")
DEF__NDAYS = 1
DEF__OBJECTS = 'M51:NGC1365'
DEF__OBJECT = 'M51'
DEF__RIGHT_ASCENSION = 0.0
DEF__HMS = '00:00:00.000 hours'
DEF__TELESCOPE = 'kuiper'
DEF__TIME = Time.now()


# +
# data structure(s)
# -
TEL__NODES = {
    'bok': {
        'aka': 'Bok 90-inch',
        'altitude': 6795.8 * FT_TO_M,
        'astronomical_dusk': AST__TWILIGHT_12,
        'astronomical_twilight': AST__TWILIGHT_18,
        'declination_limit': 60.0,
        'elevation': 6795.0,
        'focal_length_m': 6.08,
        'focal_length_ft': 6.08 * M_TO_FT,
        'imager': {
            'name': '90Prime',
            'binning': 'None, 1x1, 2x2, 3x3',
            'dither': 'None, NxM, n-RA, n-Dec',
            'filters': 'U, B, V, R, I, Clear'
        },
        'spectrograph': {
            'name': 'BCSpec',
            'binning': 'None, 1x1, 2x2, 3x3',
            'filters': 'U, B, V, R, I, Clear'
        },
        'primary_imperial': 2.29 * M_TO_FT * 12.0,
        'latitude': 31.9629,
        'longitude': -111.6004,
        'max_airmass': 3.5,
        'max_moon_exclusion': 25.0,
        'primary_metric': 2.29,
        'min_airmass': 1.0,
        'min_moon_exclusion': 2.5,
        'name': 'Bok',
        'mount': 'Equatorial'
    },
    'kuiper': {
        'aka': 'Kuiper 61-inch',
        'altitude': 8235.0 * FT_TO_M,
        'astronomical_dusk': AST__TWILIGHT_12,
        'astronomical_twilight': AST__TWILIGHT_18,
        'declination_limit': 58.0,
        'elevation': 8235.0,
        'focal_length_m': 9.6,
        'focal_length_ft': 9.6 * M_TO_FT,
        'imager': {
            'name': 'Mont4k',
            'binning': 'None, 1x1, 2x2, 3x3, 4x4',
            'dither': 'None, NxM, n-RA, n-Dec',
            'filters': 'U, B, V, R, I, Clear'
        },
        'latitude': 32.4165,
        'longitude': -110.7345,
        'max_airmass': 3.5,
        'max_moon_exclusion': 45.0,
        'primary_imperial': 1.54 * M_TO_FT * 12.0,
        'primary_metric': 1.54,
        'min_airmass': 1.0,
        'min_moon_exclusion': 3.0,
        'name': 'Kuiper',
        'mount': 'Equatorial'
    },
    'mmt': {
        'aka': 'MMT 6.5m',
        'altitude': 8585.0 * FT_TO_M,
        'astronomical_dusk': AST__TWILIGHT_12,
        'astronomical_twilight': AST__TWILIGHT_18,
        'declination_limit': 58.0,
        'elevation': 8585.0,
        'focal_length_m': 9.6,
        'focal_length_ft': 9.6 * M_TO_FT,
        'spectrograph': {
            'name': 'BinoSpec',
            'binning': 'None, 1x1, 2x2, 3x3, 4x4',
            'filters': 'U, B, V, R, I, Clear'
        },
        'latitude': 31.6883,
        'longitude': -110.8850,
        'max_airmass': 3.5,
        'max_moon_exclusion': 45.0,
        'primary_imperial': 6.5 * M_TO_FT * 12.0,
        'primary_metric': 6.5,
        'min_airmass': 1.0,
        'min_moon_exclusion': 3.0,
        'name': 'MMT',
        'mount': 'Alt-Az'
    },
    'vatt': {
        'aka': 'Vatt 1.8-metre',
        'altitude': 10469.0 * FT_TO_M,
        'astronomical_dusk': AST__TWILIGHT_12,
        'astronomical_twilight': AST__TWILIGHT_18,
        'declination_limit': 60.0,
        'elevation': 10469.0,
        'focal_length_m': 16.48,
        'focal_length_ft': 16.48 * M_TO_FT,
        'imager': {
            'name': 'Vatt4k',
            'binning': 'None, 1x1, 2x2, 3x3, 4x4',
            'dither': 'None, NxM, n-RA, n-Dec',
            'filters': 'U, B, V, R, I, Clear'
        },
        'latitude': 32.7016,
        'longitude': -109.8719,
        'max_airmass': 3.5,
        'max_moon_exclusion': 25.0,
        'primary_imperial': 1.8 * M_TO_FT * 12.0,
        'primary_metric': 1.8,
        'min_airmass': 1.0,
        'min_moon_exclusion': 2.5,
        'name': 'Vatt',
        'mount': 'Alt-Az'
    }
}

TEL__AKA = {_k: _v['aka'] for _k, _v in TEL__NODES.items() if 'aka' in _v}
TEL__ALTITUDE = {_k: _v['altitude'] for _k, _v in TEL__NODES.items() if 'altitude' in _v}
TEL__DEC__LIMIT = {_k: _v['declination_limit'] for _k, _v in TEL__NODES.items() if 'declination_limit' in _v}
TEL__DUSK = {_k: _v['astronomical_dusk'] for _k, _v in TEL__NODES.items() if 'astronomical_dusk' in _v}
TEL__LATITUDE = {_k: _v['latitude'] for _k, _v in TEL__NODES.items() if 'latitude' in _v}
TEL__LONGITUDE = {_k: _v['longitude'] for _k, _v in TEL__NODES.items() if 'longitude' in _v}
TEL__MAX__AIRMASS = {_k: _v['max_airmass'] for _k, _v in TEL__NODES.items() if 'max_airmass' in _v}
TEL__MAX__MOONEX = {_k: _v['max_moon_exclusion'] for _k, _v in TEL__NODES.items() if 'max_moon_exclusion' in _v}
TEL__MIN__AIRMASS = {_k: _v['min_airmass'] for _k, _v in TEL__NODES.items() if 'min_airmass' in _v}
TEL__MIN__MOONEX = {_k: _v['min_moon_exclusion'] for _k, _v in TEL__NODES.items() if 'min_moon_exclusion' in _v}
TEL__NAME = [_k.lower() for _k in TEL__NODES]
TEL__RANDOM = random.randrange(0, len(TEL__NODES), 1)
TEL__TWILIGHT = {_k: _v['astronomical_twilight'] for _k, _v in TEL__NODES.items() if 'astronomical_twilight' in _v}


# +
# (factory) class: Telescope()
# -
# noinspection PyBroadException
class Telescope(object):

    # +
    # method: __init__
    # -
    def __init__(self, name=''):

        # get input(s)
        self.name = name

        # set default(s)
        self.__simulation = False
        self.__altitude = TEL__ALTITUDE[f'{self.__name}']
        self.__latitude = TEL__LATITUDE[f'{self.__name}']
        self.__longitude = TEL__LONGITUDE[f'{self.__name}']
        self.__observatory = EarthLocation(
            lat=self.__latitude * u.deg, lon=self.__longitude * u.deg, height=self.__altitude * u.m)
        self.__observer = Observer(location=self.__observatory, name=self.__name, timezone='US/Arizona')

    # +
    # Decorator(s) for getter(s) and setter(s)
    # -
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name=''):
        self.__name = name.lower() if (isinstance(name, str) and name.lower() in TEL__NAME) else DEF__TELESCOPE

    @property
    def simulation(self):
        return self.__simulation

    @simulation.setter
    def simulation(self, simulation=False):
        tel_logger.critical(f"simulation.setter()> simulation={simulation}, type={type(simulation)}")
        self.__simulation = simulation if isinstance(simulation, bool) else False

    # +
    # getter(s) with no setter(s)
    # -
    @property
    def observer(self):
        return self.__observer

    @property
    def observatory(self):
        return self.__observatory

    # +
    # method: airmass_plot()
    # -
    def airmass_plot(self, _ra=DEF__RIGHT_ASCENSION, _dec=DEF__DECLINATION, _date=DEF__BEGIN,
                     _ndays=DEF__NDAYS, _from_now=False):
        """ returns an image of airmass for object for several days """

        # check input(s)
        tel_log(f"airmass_plot> entry at {Time.now()}", True, False)
        tel_log(f"airmass_plot> _ra={_ra:.3f}, _dec={_dec:.3f}, _date={_date}, "
                f"_ndays={_ndays}, _from_now={_from_now}", True, False)
        _ra = _ra if isinstance(_ra, float) else DEF__RIGHT_ASCENSION
        _ra = _ra if _ra > MIN__RIGHT_ASCENSION else MIN__RIGHT_ASCENSION
        _ra = _ra if _ra < MAX__RIGHT_ASCENSION else MAX__RIGHT_ASCENSION
        _dec = _dec if isinstance(_dec, float) else DEF__DECLINATION
        _dec = _dec if _dec > MIN__DECLINATION else MIN__DECLINATION
        _dec = _dec if _dec < MAX__DECLINATION else MAX__DECLINATION
        _date = _date if (isinstance(_date, str) and re.search(ISO__PATTERN, _date)) else DEF__BEGIN
        _ndays = _ndays if isinstance(_ndays, int) else DEF__NDAYS
        _ndays = _ndays if _ndays > 0 else DEF__NDAYS
        _from_now = _from_now if isinstance(_from_now, bool) else False
        tel_log(f"airmass_plot> _ra={_ra:.3f}, _dec={_dec:.3f}, _date={_date}, "
                f"_ndays={_ndays}, _from_now={_from_now}", True, False)

        # set default(s)
        _time_now = Time.now()
        if 'T' in _date:
            _start = Time(_date) if _from_now else Time(_date.split('T')[0])
        else:
            _start = Time(_date) if _from_now else Time(_date.split()[0])
        _now = Time(_start.iso)
        _start = Time(_start.iso)
        _start = Time(_start) + (_ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))
        _title = f"Airmass [{_ndays} Day(s)]"

        _ra_hms = Angle(_ra, unit=u.deg).hms
        _HH, _MM, _SS = _ra_hms[0], _ra_hms[1], _ra_hms[2]
        _sign = '-' if str(_dec)[0] == '-' else '+'
        _dec_dms = Angle(_dec, unit=u.deg).dms
        _dd, _mm, _ss = abs(_dec_dms[0]), abs(_dec_dms[1]), abs(_dec_dms[2])
        _sub_title = f"RA={int(_HH):02d}:{int(_MM):02d}:{int(_SS):02d} ({_ra:.3f}{UNI__DEGREE}), " \
                     f"Dec={_sign}{int(_dd):02d}{UNI__DEGREE}{int(_mm):02d}{UNI__ARCMIN}{int(_ss):02d}{UNI__ARCSEC} " \
                     f"({_dec:.3f}{UNI__DEGREE})"

        # modify to reference frame and get airmass
        _frame = AltAz(obstime=_start, location=self.__observatory)
        _radecs = SkyCoord(ra=_ra*u.deg, dec=_dec*u.deg)
        _altaz = _radecs.transform_to(_frame)

        # extract axes
        _max_airmass = TEL__MAX__AIRMASS[f'{self.__name.lower()}']
        _min_airmass = TEL__MIN__AIRMASS[f'{self.__name.lower()}']
        _time_axis = _start[(_altaz.secz <= _max_airmass) & (_altaz.secz >= _min_airmass)]
        _airmass_axis = _altaz.secz[(_altaz.secz <= _max_airmass) & (_altaz.secz >= _min_airmass)]

        # plot it
        fig, ax = plt.subplots()
        ax.plot_date(_time_axis.plot_date, _airmass_axis, 'r-')
        ax.plot_date([_time_now.plot_date, _time_now.plot_date], [-999, 999], 'y--')
        xfmt = mdates.DateFormatter('%H:%M')
        ax.xaxis.set_major_formatter(xfmt)
        plt.gcf().autofmt_xdate()
        ax.set_ylim([_max_airmass, _min_airmass])
        ax.set_xlim([_start.datetime[0], _start.datetime[-1]])
        ax.set_title(f'{_title}\n{_sub_title}')
        ax.set_ylabel(f'Airmass ({UNI__PROPORTIONAL} secZ)')
        ax.set_xlabel(f"{str(_now).split()[0]} (UTC)")
        buf = io.BytesIO()
        # plt.savefig(f'{_file}')
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        data = buf.getvalue()
        tel_log(f"airmass_plot> exit at {Time.now()}", True, False)
        return f'data:image/png;base64,{base64.b64encode(data).decode()}'

    # +
    # method: dump()
    # -
    def dump(self):
        """ dump internal variable(s) """
        _str = f'self={self}'
        _str = f'{_str}\nself.__name={self.__name}'
        _str = f'{_str}\nself__.altitude={self.__altitude}'
        _str = f'{_str}\nself.__latitude={self.__latitude}'
        _str = f'{_str}\nself.__longitude={self.__longitude}'
        _str = f'{_str}\nself.__observatory={self.__observatory}'
        _str = f'{_str}\nself.__observer={self.__observer}'
        _str = f'{_str}\nself.__simulation={self.__simulation}'
        for _k, _v in TEL__NODES[f"{self.__name}"].items():
            _str = f'{_str}\n{_k}={_v}'
        return _str

    # +
    # method: moon_coordinates()
    # -
    def moon_coordinates(self, date=DEF__BEGIN, ndays=DEF__NDAYS, from_now=False):
        """ returns an array of (ra, dec, distance) for moon over several days """

        # check input(s)
        date = date if (isinstance(date, str) and re.search(ISO__PATTERN, date)) else DEF__BEGIN
        ndays = ndays if isinstance(ndays, int) else DEF__NDAYS
        ndays = ndays if ndays > 0 else DEF__NDAYS
        from_now = from_now if isinstance(from_now, bool) else False

        # set default(s)
        _time = Time(date) if from_now else Time(date.split()[0])
        _time = Time(_time.iso)
        _time = Time(_time) + (ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES*ndays))

        # noinspection PyBroadException
        try:
            return get_moon(_time, location=self.__observatory)
        except Exception:
            return None

    # +
    # method: moon_coordinates_now()
    # -
    def moon_coordinates_now(self):
        """ returns (ra, dec, distance) for moon now """
        return self.moon_coordinates(f'{self.get_date_utctime(0)}', ndays=1, from_now=True)[0]

    # +
    # method: moon_coordinates_today()
    # -
    def moon_coordinates_today(self):
        """ returns (ra, dec, distance) for moon now """
        return self.moon_coordinates(f'{self.get_date_utctime(0)}', ndays=1, from_now=False)

    # +
    # method: moon_exclusion()
    # -
    def moon_exclusion(self, date=DEF__BEGIN, ndays=DEF__NDAYS, from_now=False):
        """ returns an array of moon exclusion angles from object for several days """

        # check input(s)
        date = date if (isinstance(date, str) and re.search(ISO__PATTERN, date)) else DEF__BEGIN
        ndays = ndays if isinstance(ndays, int) else DEF__NDAYS
        ndays = ndays if ndays > 0 else DEF__NDAYS
        from_now = from_now if isinstance(from_now, bool) else False

        # set default(s)
        _excl = None
        _time = Time(date) if from_now else Time(date.split()[0])
        _time = Time(_time.iso)
        _time = Time(_time) + (ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES*ndays))

        _moon_lower = TEL__MIN__MOONEX[f'{self.__name.lower()}']
        _moon_upper = TEL__MAX__MOONEX[f'{self.__name.lower()}'] - _moon_lower

        # get illumination and moon alt-az for time
        _illuminati = self.__observer.moon_illumination(_time)
        _lunar_altaz = self.__observer.moon_altaz(_time)

        # noinspection PyBroadException
        try:
            for _i in range(len(_lunar_altaz)):
                if _lunar_altaz[_i].alt <= 0:
                    # noinspection PyUnresolvedReferences
                    _illuminati[_i] = 0.0
            _excl = (_moon_lower + _moon_upper * _illuminati)
        except Exception:
            _excl = ndays * np.linspace(math.nan, math.nan, AST__5_MINUTES*ndays)

        # return result
        return _excl

    # +
    # method: moon_exclusion_now()
    # -
    def moon_exclusion_now(self):
        """ returns the value of the moon exclusion angle from object right now """
        return self.moon_exclusion(f'{self.get_date_utctime(0)}', ndays=1, from_now=True)[0]

    # +
    # method: moon_exclusion_today()
    # -
    def moon_exclusion_today(self):
        """ returns an array of moon exclusion angles from object for today """
        return self.moon_exclusion(f'{self.get_date_utctime(0)}', ndays=1, from_now=False)

    # +
    # method: moon_separation()
    # -
    def moon_separation(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION, date=DEF__BEGIN,
                        ndays=DEF__NDAYS, from_now=False):
        """ returns an array of moon separation angles from object for several days """

        # check input(s)
        ra = ra if isinstance(ra, float) else DEF__RIGHT_ASCENSION
        ra = ra if ra > MIN__RIGHT_ASCENSION else MIN__RIGHT_ASCENSION
        ra = ra if ra < MAX__RIGHT_ASCENSION else MAX__RIGHT_ASCENSION
        dec = dec if isinstance(dec, float) else DEF__DECLINATION
        dec = dec if dec > MIN__DECLINATION else MIN__DECLINATION
        dec = dec if dec < MAX__DECLINATION else MAX__DECLINATION
        date = date if (isinstance(date, str) and re.search(ISO__PATTERN, date)) else DEF__BEGIN
        ndays = ndays if isinstance(ndays, int) else DEF__NDAYS
        ndays = ndays if ndays > 0 else DEF__NDAYS
        from_now = from_now if isinstance(from_now, bool) else False

        # set default(s)
        _sep = None
        _time = Time(date) if from_now else Time(date.split()[0])
        _time = Time(_time.iso)
        _time = Time(_time) + (ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES*ndays))

        # noinspection PyBroadException
        try:
            _moon_coord = get_moon(_time, location=self.__observatory)
            _obj_radec = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
            _sep = _obj_radec.separation(_moon_coord).deg
        except Exception:
            _sep = ndays * np.linspace(math.nan, math.nan, AST__5_MINUTES*ndays)

        # return array
        return _sep

    # +
    # method: moon_separation_now()
    # -
    def moon_separation_now(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION):
        """ returns the value of the moon separation angle from object right now """
        return self.moon_separation(ra, dec, f'{self.get_date_utctime(0)}', ndays=1, from_now=True)[0]

    # +
    # method: moon_separation_today()
    # -
    def moon_separation_today(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION):
        """ returns an array of moon separation angles from object for today """
        return self.moon_separation(ra, dec, f'{self.get_date_utctime(0)}', ndays=1, from_now=False)

    # +
    # (override static) method: observe()
    # -
    @staticmethod
    def observe(**kwargs):
        pass

    # +
    # method: observable()
    # -
    def observable(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION, date=DEF__BEGIN,
                   ndays=DEF__NDAYS, from_now=False):
        """ returns an array of observability flags for object for several days """

        # check input(s)
        ra = ra if isinstance(ra, float) else DEF__RIGHT_ASCENSION
        ra = ra if ra > MIN__RIGHT_ASCENSION else MIN__RIGHT_ASCENSION
        ra = ra if ra < MAX__RIGHT_ASCENSION else MAX__RIGHT_ASCENSION
        dec = dec if isinstance(dec, float) else DEF__DECLINATION
        dec = dec if dec > MIN__DECLINATION else MIN__DECLINATION
        dec = dec if dec < MAX__DECLINATION else MAX__DECLINATION
        date = date if (isinstance(date, str) and re.search(ISO__PATTERN, date)) else DEF__BEGIN
        ndays = ndays if isinstance(ndays, int) else DEF__NDAYS
        ndays = ndays if ndays > 0 else DEF__NDAYS
        from_now = from_now if isinstance(from_now, bool) else False

        # set default(s)
        _obs = np.linspace(math.nan, math.nan, AST__5_MINUTES*ndays)
        _time = Time(date) if from_now else Time(date.split()[0])
        _time = Time(_time.iso)

        # get arrays for moon exclusion, separation and UTC time
        _mex = self.moon_exclusion(date=_time.iso, ndays=ndays, from_now=from_now)
        _msp = self.moon_separation(ra=ra, dec=dec, date=_time.iso, ndays=ndays, from_now=from_now)
        _time = Time(_time) + (ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES*ndays))

        # modify to reference frame and get solar position
        _frame = AltAz(obstime=_time, location=self.__observatory)
        _radecs = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
        _altaz = _radecs.transform_to(_frame)
        _solar_altaz = get_sun(_time).transform_to(_altaz)

        # get limit(s)
        _max_airmass = TEL__MAX__AIRMASS[f'{self.__name.lower()}']
        _min_airmass = TEL__MIN__AIRMASS[f'{self.__name.lower()}']
        _dusk = TEL__DUSK[f'{self.__name.lower()}'] * u.deg
        _twilight = TEL__TWILIGHT[f'{self.__name.lower()}'] * u.deg
        _horizon = AST__HORIZON * u.deg
        _north = AST__NORTH * u.deg
        _south = AST__SOUTH * u.deg

        # noinspection PyBroadException
        try:
            for i in range(len(_altaz)):

                # the Sun has risen, so not observable
                if _solar_altaz[i].alt >= _horizon:
                    _obs[i] = VAL__NOT_OBSERVABLE

                # morning or evening twilight, might be observable
                elif _twilight <= _solar_altaz.alt[i] < _horizon:

                    # the Sun is in the East, it must be rising so we are in morning twilight
                    if _north <= _solar_altaz[i].az <= _south:
                        _obs[i] = VAL__NOT_OBSERVABLE
                    # the Sun is in the West, it must be setting so we are in evening twilight
                    else:
                        _obs[i] = VAL__OBSERVABLE

                else:
                    _obs[i] = VAL__OBSERVABLE

                # modify for airmass or exclusion
                if _altaz.secz[i] >= _max_airmass:
                    _obs[i] = VAL__NOT_OBSERVABLE
                elif _msp[i] <= _mex[i]:
                    _obs[i] = VAL__NOT_OBSERVABLE

        except Exception:
            _obs = np.linspace(math.nan, math.nan, AST__5_MINUTES*ndays)

        # return result
        return _obs

    # +
    # method: observable_now()
    # -
    def observable_now(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION):
        """ returns the value of the observability flag for object for right now """
        return self.observable(ra, dec, f'{self.get_date_utctime(0)}', ndays=1, from_now=True)[0]

    # +
    # method: observable_today()
    # -
    def observable_today(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION):
        """ returns an array of observability flags for object for today """
        return self.observable(ra, dec, f'{self.get_date_utctime(0)}', ndays=1, from_now=False)

    # +
    # method: solar_separation()
    # -
    @staticmethod
    def solar_separation(ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION, date=DEF__BEGIN,
                         ndays=DEF__NDAYS, from_now=False):
        """ returns an array of solar separation angles from object for several days """

        # check input(s)
        ra = ra if isinstance(ra, float) else DEF__RIGHT_ASCENSION
        ra = ra if ra > MIN__RIGHT_ASCENSION else MIN__RIGHT_ASCENSION
        ra = ra if ra < MAX__RIGHT_ASCENSION else MAX__RIGHT_ASCENSION
        dec = dec if isinstance(dec, float) else DEF__DECLINATION
        dec = dec if dec > MIN__DECLINATION else MIN__DECLINATION
        dec = dec if dec < MAX__DECLINATION else MAX__DECLINATION
        date = date if (isinstance(date, str) and re.search(ISO__PATTERN, date)) else DEF__BEGIN
        ndays = ndays if isinstance(ndays, int) else DEF__NDAYS
        ndays = ndays if ndays > 0 else DEF__NDAYS
        from_now = from_now if isinstance(from_now, bool) else False

        # set default(s)
        _sep = None
        _time = Time(date) if from_now else Time(date.split()[0])
        _time = Time(_time.iso)
        _time = Time(_time) + (ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES*ndays))

        # noinspection PyBroadException
        try:
            _obj_radec = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
            _solar_coord = get_sun(_time).transform_to(_obj_radec)
            _sep = _obj_radec.separation(_solar_coord).deg
        except Exception:
            _sep = ndays * np.linspace(math.nan, math.nan, AST__5_MINUTES*ndays)

        # return array
        return _sep

    # +
    # method: solar_separation_now()
    # -
    def solar_separation_now(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION):
        """ returns the value of the solar separation angle from object right now """
        return self.solar_separation(ra, dec, f'{self.get_date_utctime(0)}', ndays=1, from_now=True)[0]

    # +
    # method: solar_separation_today()
    # -
    def solar_separation_today(self, ra=DEF__RIGHT_ASCENSION, dec=DEF__DECLINATION):
        """ returns an array of solar separation angles from object for today """
        return self.solar_separation(ra, dec, f'{self.get_date_utctime(0)}', ndays=1, from_now=False)

    # +
    # function: get_astropy_coords()
    # -
    @staticmethod
    def get_astropy_coords(name=DEF__OBJECT):
        """ get co-ordinates of known object via astropy """

        # check input(s)
        name = name if (isinstance(name, str) and name.strip().lower() != '') else DEF__OBJECT

        # noinspection PyBroadException
        try:
            _coord = SkyCoord.from_name(name)
            return float(_coord.ra.degree), float(_coord.dec.degree)
        except Exception:
            return float(math.nan), float(math.nan)

    # +
    # (static) method: get_date_time()
    # -
    @staticmethod
    def get_date_time(offset=0):
        offset = offset if isinstance(offset, int) else 0
        return datetime.now() + timedelta(days=offset)

    # +
    # (static) method: get_date_utctime()
    # -
    @staticmethod
    def get_date_utctime(offset=0):
        offset = offset if isinstance(offset, int) else 0
        return datetime.utcnow() + timedelta(days=offset)

    # +
    # (static) method: dec_2_dms()
    # -
    @staticmethod
    def dec_2_dms(dec=DEF__DECLINATION):
        """ converts digital Dec to (d,m,s) tuple """

        # check input(s)
        dec = dec if isinstance(dec, float) else DEF__DECLINATION
        dec = dec if dec > MIN__DECLINATION else MIN__DECLINATION
        dec = dec if dec < MAX__DECLINATION else MAX__DECLINATION
        _dec_dms = Angle(dec, unit=u.deg).dms

        # return result
        return _dec_dms[0], _dec_dms[1], _dec_dms[2]

    # +
    # (static) method: deg_2_rad()
    # -
    @staticmethod
    def deg_2_rad(_degrees=0.0):
        """ converts degrees to radians """

        try:
            return math.radians(_degrees)
        except Exception:
            return float(math.nan)

    # +
    # method: dec_to_decimal()
    # -
    @staticmethod
    def dms_2_dec(dms=''):
        """ converts dd:mm:ss.sss into a decimal """

        # check input(s)
        dms = dms if (isinstance(dms, str) and dms.strip() != '' and ':' in dms) else DEF__DMS
        dms = dms if ('degrees' in dms) else f'{dms} degrees'

        try:
            return float(Angle(dms).degree)
        except Exception:
            return float(math.nan)

    # +
    # method: hms_2_ra()
    # -
    @staticmethod
    def hms_2_ra(hms=''):
        """ converts hh:mm:ss.sss into a decimal """

        # check input(s)
        hms = hms if (isinstance(hms, str) and hms.strip() != '' and ':' in hms) else DEF__HMS
        hms = hms if ('hours' in hms) else f'{hms} hours'

        # noinspection PyBroadException
        try:
            return float(Angle(hms).degree)
        except Exception:
            return float(math.nan)

    # +
    # (static) method: ra_2_hms()
    # -
    @staticmethod
    def ra_2_hms(ra=DEF__RIGHT_ASCENSION):
        """ converts digital RA to (h,m,s) tuple """

        # check input(s)
        ra = ra if isinstance(ra, float) else DEF__RIGHT_ASCENSION
        ra = ra if ra > MIN__RIGHT_ASCENSION else MIN__RIGHT_ASCENSION
        ra = ra if ra < MAX__RIGHT_ASCENSION else MAX__RIGHT_ASCENSION
        _ra_hms = Angle(ra, unit=u.deg).hms

        # return result
        return _ra_hms[0], _ra_hms[1], _ra_hms[2]

    # +
    # (static) method: rad_2_deg()
    # -
    @staticmethod
    def rad_2_deg(_radians=0.0):
        """ converts radians to degrees """

        # noinspection PyPep8
        try:
            return math.degrees(_radians)
        except Exception:
            return float(math.nan)

    # +
    # (static) method: sky_separation()
    # -
    @staticmethod
    def sky_separation(ra1=DEF__RIGHT_ASCENSION, dec1=DEF__DECLINATION,
                       ra2=DEF__RIGHT_ASCENSION, dec2=DEF__DECLINATION):
        """ returns angular separation (in degrees) of 2 objects """

        # check input(s
        ra1 = ra1 if isinstance(ra1, float) else DEF__RIGHT_ASCENSION
        ra1 = ra1 if ra1 > MIN__RIGHT_ASCENSION else MIN__RIGHT_ASCENSION
        ra1 = ra1 if ra1 < MAX__RIGHT_ASCENSION else MAX__RIGHT_ASCENSION
        dec1 = dec1 if isinstance(dec1, float) else DEF__DECLINATION
        dec1 = dec1 if dec1 > MIN__DECLINATION else MIN__DECLINATION
        dec1 = dec1 if dec1 < MAX__DECLINATION else MAX__DECLINATION
        ra2 = ra2 if isinstance(ra2, float) else DEF__RIGHT_ASCENSION
        ra2 = ra2 if ra2 > MIN__RIGHT_ASCENSION else MIN__RIGHT_ASCENSION
        ra2 = ra2 if ra2 < MAX__RIGHT_ASCENSION else MAX__RIGHT_ASCENSION
        dec2 = dec2 if isinstance(dec2, float) else DEF__DECLINATION
        dec2 = dec2 if dec2 > MIN__DECLINATION else MIN__DECLINATION
        dec2 = dec2 if dec2 < MAX__DECLINATION else MAX__DECLINATION

        # return result
        try:
            c1 = SkyCoord(ra=ra1 * u.deg, dec=dec1 * u.deg)
            c2 = SkyCoord(ra=ra2 * u.deg, dec=dec2 * u.deg)
            sep = c1.separation(c2)
            return float(sep.degree)
        except Exception:
            return float(math.nan)


# +
# function: _telescope_factory()
# -
def _telescope_factory(iargs=None):

    # check input(s)
    if iargs is None:
        tel_log('ERROR: invalid input, iargs={iargs}', True, False)
        return

    # set default(s)
    objects = iargs.objects.strip().upper() if \
        (isinstance(iargs.objects, str) and iargs.objects.strip().lower() != '') else DEF__OBJECTS
    telescope = iargs.telescope.strip().lower() if \
        (isinstance(iargs.telescope, str) and iargs.telescope.strip().lower() in TEL__NAME) else DEF__TELESCOPE
    verbose = iargs.verbose if isinstance(iargs.verbose, bool) else False

    # noinspection PyBroadException
    try:
        if verbose:
            print(f"Instantiating Telescope(name='{telescope}')")
        _t = Telescope(name=f'{telescope}')
        if verbose:
            print(f"Instantiated Telescope(name='{telescope}')")
    except Exception as _e:
        if verbose:
            print(f"Failed instantiating Telescope(name='{telescope}')")
        tel_log(f'ERROR: error detected, e={_e}', True, False)
        return
    else:
        if verbose:
            print(_t.dump())

    # get co-ordinates of at least 2 objects
    _reference = 'IC4329A'
    _coordinates = []
    _objects = objects.strip().split(':')
    _objects.append(_reference)
    for _obj in _objects:
        _ra, _dec = _t.get_astropy_coords(_obj)
        _coordinates.append((_ra, _dec))
    if verbose:
        print(f"_objects = {_objects}, _coordinates = {_coordinates}")

    # get reference coords
    _ref_ra, _ref_dec = _coordinates[-1][0], _coordinates[-1][1]
    _ref_hms, _ref_dms = _t.ra_2_hms(_ref_ra), _t.dec_2_dms(_ref_dec)
    _ref_sign = '+' if (str(_ref_dms[0])[0]).isdigit() else '-'
    _ref_hms_s, _ref_dms_s = f"{int(_ref_hms[0])}:{int(_ref_hms[1])}:{_ref_hms[2]:.2f}", \
                             f"{_ref_sign}{abs(int(_ref_dms[0]))}:{abs(int(_ref_dms[1]))}:{abs(_ref_dms[2]):.2f}"

    # example(s) of the API
    print(f"Moon exclusion zone = {_t.moon_exclusion_now()}")
    _date = f'{_t.get_date_utctime(0)}'
    for _i, _v in enumerate(_objects):
        _ra = _coordinates[_i][0]
        _dec = _coordinates[_i][1]
        _hms = _t.ra_2_hms(_ra)
        _dms = _t.dec_2_dms(_dec)
        _sign = '+' if (str(_dms[0])[0]).isdigit() else '-'
        _hms_s = f"{int(_hms[0])}:{int(_hms[1])}:{_hms[2]:.2f}"
        _dms_s = f"{_sign}{abs(int(_dms[0]))}:{abs(int(_dms[1]))}:{abs(_dms[2]):.2f}"
        _moon_coords = _t.moon_coordinates_now()
        print(f"{_v:8s}>> Moon now: _moon_coords = {_moon_coords}")
        print(f"{_v:8s}>> Moon now: RA={_moon_coords.ra}, Dec={_moon_coords.dec}, Distance={_moon_coords.distance}")
        print(f"{_v:8s}>> RA={_hms_s}, Dec={_dms_s} (RA={_ra:.2f} degrees, Dec={_dec:.2f} degrees) at {_date}")
        print(f"{_v:8s}>> Moon separation ({_ra:.3f}, {_dec:.3f}) = {_t.moon_separation_now(ra=_ra, dec=_dec):.3f}")
        print(f"{_v:8s}>> Solar separation ({_ra:.3f}, {_dec:.3f}) = {_t.solar_separation_now(ra=_ra, dec=_dec):.3f}")
        print(f"{_v:8s}>> Observable now ({_ra:.3f}, {_dec:.3f}) = {bool(_t.observable_now(ra=_ra, dec=_dec))}")
        print(f"{_v:8s}>> Sky separation from {_reference} (RA={_ref_hms_s}, Dec={_ref_dms_s}) = "
              f"{_t.sky_separation(_ra, _dec, _ref_ra, _ref_dec)}")


# +
# main()
# -
if __name__ == '__main__':

    # noinspection PyBroadException
    try:
        # import(s)
        from src import get_iers, ASTROPLAN_IERS_URL
        get_iers(_url='https://datacenter.iers.org/data/9/finals2000A.all')
    except Exception:
        pass

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Telescope Factory',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--telescope', default=TEL__NAME[TEL__RANDOM],
                    help=f"Telescope, default='%(default)s', choices={TEL__NAME}")
    _p.add_argument(f'--objects', default=DEF__OBJECTS,
                    help=f"Object names, default='%(default)s'")
    _p.add_argument(f'--verbose', default=False, action='store_true',
                    help=f'if present, produce more verbose output')
    _p.set_defaults(func=_telescope_factory)

    # noinspection PyBroadException
    try:
        # execute
        args = _p.parse_args()
        args.func(args)
    except Exception:
        print(f'Use: python3 {sys.argv[0]}\n--help for more information')
