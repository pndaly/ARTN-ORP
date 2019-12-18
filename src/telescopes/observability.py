#!/usr/bin/env python3.7


# +
# import(s)
# -
from astroplan import Observer
from astropy.coordinates import Angle, AltAz, EarthLocation, SkyCoord, get_moon, get_sun
from astropy.time import Time
from datetime import timedelta
from datetime import datetime

import argparse
import astropy.units as u
import base64
import io
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import re
import sys
import unicodedata


# +
# constant(s)
# -
AST__4_MINUTES = 360
AST__5_MINUTES = 289
AST__AIRMASS_MIN = 1.0
AST__AIRMASS_MAX = 3.5
AST__FULL_MOON_EXCLUSION = 25.0
AST__DUSK = -12.0 * u.deg
AST__HORIZON = 0.0 * u.deg
AST__NEW_MOON_EXCLUSION = 2.5
AST__NORTH = 0.0 * u.deg
AST__SOUTH = 180.0 * u.deg
AST__TWILIGHT = -18.0 * u.deg
ISO__PATTERN = '[0-9]{4}-[0-9]{2}-[0-9]{2}[ T?][0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6}'
MIN__DEC = -90.0
MAX__DEC = 90.0
MIN__RA = 0.0
MAX__RA = 360.0
UNI__DEGREE = unicodedata.lookup('DEGREE SIGN')
UNI__PROPORTIONAL = unicodedata.lookup('PROPORTIONAL TO')


# +
# default(s)
# -
DEF__DATE = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
DEF__DEC = 0.0
DEF__END = (datetime.utcnow() + timedelta(30)).strftime("%Y-%m-%d %H:%M:%S.%f")
DEF__RA = 0.0
DEF__TIME = Time.now()
DEF__TIME_0_DAY = Time.now() + 0*u.day*np.linspace(0.0, 1.0, AST__5_MINUTES)
DEF__TIME_1_DAY = Time.now() + 1*u.day*np.linspace(0.0, 1.0, AST__5_MINUTES)


# +
# telescope(s)
# -
KUIPER_ALTITUDE = 2510.028 * u.m
KUIPER_LATITUDE = 32.4165 * u.deg
KUIPER_LONGITUDE = -110.7345 * u.deg
KUIPER_OBSERVATORY = EarthLocation(lat=KUIPER_LATITUDE, lon=KUIPER_LONGITUDE, height=KUIPER_ALTITUDE)
KUIPER_OBSERVER = Observer(location=KUIPER_OBSERVATORY, name="Kuiper", timezone="US/Arizona")


# +
# function: airmass_plot_day()
# -
def airmass_plot_day(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False):

    # check input(s)
    ra = DEF__RA if not isinstance(ra, float) else ra
    ra = MIN__RA if ra < MIN__RA else ra
    ra = MAX__RA if ra > MAX__RA else ra
    dec = DEF__DEC if not isinstance(dec, float) else dec
    dec = MIN__DEC if dec < MIN__DEC else dec
    dec = MAX__DEC if dec > MAX__DEC else dec
    date = DEF__DATE if (not isinstance(date, str) or date.strip() == '' or not re.search(ISO__PATTERN, date)) else date
    from_now = False if not isinstance(from_now, bool) else from_now

    # set default(s)
    _ndays = 1
    _title = f'{_ndays} Day for position RA={ra}{UNI__DEGREE} Dec={dec}{UNI__DEGREE}'
    _time_now = Time.now()
    _start = Time(date) if from_now else Time(date.split()[0])
    _start = Time(_start.iso)
    _start = Time(_start) + (_ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))

    _ra_hms = Angle(ra, unit=u.deg).hms
    _HH, _MM, _SS = _ra_hms[0], _ra_hms[1], _ra_hms[2],
    _dec_dms = Angle(dec, unit=u.deg).dms
    _dd, _mm, _ss = _dec_dms[0], _dec_dms[1], _dec_dms[2],
    _file = f"{int(_HH):02d}H{int(_MM):02d}M{int(_SS):02d}S-{int(_dd):02d}d{int(_mm):02d}m{int(_ss):02d}s.png"

    # modify to reference frame and get airmass
    _frame = AltAz(obstime=_start, location=KUIPER_OBSERVATORY)
    _radecs = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    _altaz = _radecs.transform_to(_frame)

    # extract axes
    _time_axis = _start[(_altaz.secz <= AST__AIRMASS_MAX) & (_altaz.secz >= AST__AIRMASS_MIN)]
    _airmass_axis = _altaz.secz[(_altaz.secz <= AST__AIRMASS_MAX) & (_altaz.secz >= AST__AIRMASS_MIN)]

    # plot it
    fig, ax = plt.subplots()
    ax.plot_date(_time_axis.plot_date, _airmass_axis, 'r-')
    ax.plot_date([_time_now.plot_date, _time_now.plot_date], [-999, 999], 'y--')
    xfmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    plt.gcf().autofmt_xdate()
    ax.set_ylim([AST__AIRMASS_MAX, AST__AIRMASS_MIN])
    ax.set_xlim([_start.datetime[0], _start.datetime[-1]])
    ax.set_title(f'{_title}\n{_file}')
    ax.set_ylabel(f'Airmass ({UNI__PROPORTIONAL} secZ)')
    ax.set_xlabel(f'{date.split()[0]} HH:MM (UTC)')
    buf = io.BytesIO()
    plt.savefig(f'{_file}')
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    data = buf.getvalue()
    return f'data:image/png;base64,{base64.b64encode(data).decode()}'


# +
# function: airmass_plot_dates()
# -
def airmass_plot_dates(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, end=DEF__END):

    # check input(s)
    ra = DEF__RA if not isinstance(ra, float) else ra
    ra = MIN__RA if ra < MIN__RA else ra
    ra = MAX__RA if ra > MAX__RA else ra
    dec = DEF__DEC if not isinstance(dec, float) else dec
    dec = MIN__DEC if dec < MIN__DEC else dec
    dec = MAX__DEC if dec > MAX__DEC else dec
    date = DEF__DATE if (not isinstance(date, str) or date.strip() == '' or not re.search(ISO__PATTERN, date)) else date
    end = DEF__END if (not isinstance(end, str) or end.strip() == '' or not re.search(ISO__PATTERN, end)) else end

    # get default(s)
    _time_now = Time.now()
    _end = Time(Time(end.split()[0]).iso)
    _start = Time(Time(date.split()[0]).iso)
    _ndays = int(_end.mjd - _start.mjd)
    _start = Time(_start) + (_ndays * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))
    _title = f'{_ndays} Day(s) for position RA={ra}{UNI__DEGREE} Dec={dec}{UNI__DEGREE}'

    _ra_hms = Angle(ra, unit=u.deg).hms
    _HH, _MM, _SS = _ra_hms[0], _ra_hms[1], _ra_hms[2],
    _dec_dms = Angle(dec, unit=u.deg).dms
    _dd, _mm, _ss = _dec_dms[0], _dec_dms[1], _dec_dms[2],
    _file = f"{int(_HH):02d}H{int(_MM):02d}M{int(_SS):02d}S-{int(_dd):02d}d{int(_mm):02d}m{int(_ss):02d}s.png"

    # modify to reference frame and get airmass
    _frame = AltAz(obstime=_start, location=KUIPER_OBSERVATORY)
    _radecs = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    _altaz = _radecs.transform_to(_frame)

    # extract axes
    _time_axis = _start[(_altaz.secz <= AST__AIRMASS_MAX) & (_altaz.secz >= AST__AIRMASS_MIN)]
    _airmass_axis = _altaz.secz[(_altaz.secz <= AST__AIRMASS_MAX) & (_altaz.secz >= AST__AIRMASS_MIN)]

    # plot it
    fig, ax = plt.subplots()
    ax.plot_date(_time_axis.plot_date, _airmass_axis, 'r-')
    ax.plot_date([_time_now.plot_date, _time_now.plot_date], [-999, 999], 'y--')
    xfmt = mdates.DateFormatter('%d-%m-%y %H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    plt.gcf().autofmt_xdate()
    ax.set_ylim([AST__AIRMASS_MAX, AST__AIRMASS_MIN])
    ax.set_xlim([_start.datetime[0], _start.datetime[-1]])
    ax.set_title(f'{_title}\n{_file}')
    ax.set_ylabel(f'Airmass ({UNI__PROPORTIONAL} secZ)')
    ax.set_xlabel('Time (UTC)')
    buf = io.BytesIO()
    plt.savefig(f'{_file}')
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    data = buf.getvalue()
    return f'data:image/png;base64,{base64.b64encode(data).decode()}'


# +
# function: get_date_time()
# -
def get_date_time(offset=0):
    return datetime.now() + timedelta(days=offset)


# +
# function: get_date_utctime()
# -
def get_date_utctime(offset=0):
    return datetime.utcnow() + timedelta(days=offset)


# +
# function: moon_distance()
# -
def moon_distance(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False):

    # check input(s)
    ra = DEF__RA if not isinstance(ra, float) else ra
    ra = MIN__RA if ra < MIN__RA else ra
    ra = MAX__RA if ra > MAX__RA else ra
    dec = DEF__DEC if not isinstance(dec, float) else dec
    dec = MIN__DEC if dec < MIN__DEC else dec
    dec = MAX__DEC if dec > MAX__DEC else dec
    date = DEF__DATE if (not isinstance(date, str) or date.strip() == '' or not re.search(ISO__PATTERN, date)) else date
    from_now = False if not isinstance(from_now, bool) else from_now

    # set default(s)
    _sep = None
    _time = Time(date) if from_now else Time(date.split()[0])
    _time = Time(_time.iso)
    _time = Time(_time) + (1.0 * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))

    # noinspection PyBroadException
    try:
        _moon_coord = get_moon(_time, location=KUIPER_OBSERVATORY)
        _obj_radec = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        _sep = _obj_radec.separation(_moon_coord).deg
    except Exception:
        _sep = np.linspace(math.nan, math.nan, AST__5_MINUTES)

    # return array
    return _sep


# +
# function: moon_distance_plot()
# -
def moon_distance_plot(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False):

    # set default(s)
    _sep = moon_distance(ra, dec, date, from_now)
    _time = Time(date) if from_now else Time(date.split()[0])
    _time = Time(_time.iso)
    _time = Time(_time) + (1.0 * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))

    _sub_title = f'RA={ra}{UNI__DEGREE} Dec={dec}{UNI__DEGREE}'
    _ra_hms = Angle(ra, unit=u.deg).hms
    _HH, _MM, _SS = _ra_hms[0], _ra_hms[1], _ra_hms[2], 
    _dec_dms = Angle(dec, unit=u.deg).dms
    _dd, _mm, _ss = _dec_dms[0], _dec_dms[1], _dec_dms[2], 
    _title = f"{int(_HH):02d}H{int(_MM):02d}M{int(_SS):02d}S-" \
             f"{int(_dd):02d}d{int(_mm):02d}m{int(_ss):02d}s"
    _file = f'MoonDistance-{_title}.png'

    # plot it
    fig, ax = plt.subplots()
    ax.plot_date(_time.plot_date, _sep, 'r-')
    ax.plot_date([Time.now().plot_date, Time.now().plot_date], [-999, 999], 'y--')
    xfmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    plt.gcf().autofmt_xdate()
    ax.set_ylim([min(_sep), max(_sep)])
    ax.set_xlim([_time.datetime[0], _time.datetime[-1]])
    ax.set_title(f'{_title}\n{_sub_title}')
    ax.set_ylabel(f'Moon Distance ({UNI__DEGREE})')
    ax.set_xlabel('Time (UTC)')
    buf = io.BytesIO()
    plt.savefig(f'{_file}')
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    data = buf.getvalue()
    return f'data:image/png;base64,{base64.b64encode(data).decode()}'


# +
# function: moon_distance_now()
# -
def moon_distance_now(ra=DEF__RA, dec=DEF__DEC):
    return moon_distance(ra, dec, f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")}', from_now=True)[0]


# +
# function: moon_distance_today()
# -
def moon_distance_today(ra=DEF__RA, dec=DEF__DEC):
    return moon_distance(ra, dec, f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")}', from_now=False)


# +
# function: moon_exclusion()
# -
def moon_exclusion(date=DEF__DATE, from_now=False):

    # check input(s)
    date = DEF__DATE if (not isinstance(date, str) or date.strip() == '' or not re.search(ISO__PATTERN, date)) else date
    from_now = False if not isinstance(from_now, bool) else from_now

    # set default(s)
    _excl = None
    _time = Time(date) if from_now else Time(date.split()[0])
    _time = Time(_time.iso)
    _time = Time(_time) + (1.0 * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))
    _moon_lower = AST__NEW_MOON_EXCLUSION
    _moon_upper = AST__FULL_MOON_EXCLUSION - AST__NEW_MOON_EXCLUSION

    # get illumination and moon alt-az for time
    _illuminati = KUIPER_OBSERVER.moon_illumination(_time)
    _lunar_altaz = KUIPER_OBSERVER.moon_altaz(_time)

    # noinspection PyBroadException
    try:
        for _i in range(len(_lunar_altaz)):
            if _lunar_altaz[_i].alt <= 0:
                # noinspection PyUnresolvedReferences
                _illuminati[_i] = 0.0
        _excl = (_moon_lower + _moon_upper * _illuminati)
    except Exception:
        _excl = np.linspace(math.nan, math.nan, AST__5_MINUTES)

    # return result
    return _excl


# +
# function: moon_exclusion_plot()
# -
def moon_exclusion_plot(date=DEF__DATE, from_now=False):

    # set default(s)
    _excl = moon_exclusion(date, from_now)
    _time = Time(date) if from_now else Time(date.split()[0])
    _time = Time(_time.iso)
    _time = Time(_time) + (1.0 * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))
    _title = f"Moon Exclusion Zones"
    _sub_title = f'{date.split()[0]}'
    _file = f"MoonExclusion-{_sub_title}.png"

    # plot it
    fig, ax = plt.subplots()
    ax.plot_date(_time.plot_date, _excl, 'r-')
    ax.plot_date([Time.now().plot_date, Time.now().plot_date], [-999, 999], 'y--')
    xfmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    plt.gcf().autofmt_xdate()
    ax.set_ylim([min(_excl)*0.9, max(_excl)*1.1])
    ax.set_xlim([_time.datetime[0], _time.datetime[-1]])
    ax.set_title(f'{_title}\n{_sub_title}')
    ax.set_ylabel(f'Moon Exclusion ({UNI__DEGREE})')
    ax.set_xlabel('Time (UTC)')
    buf = io.BytesIO()
    plt.savefig(f'{_file}.png')
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    data = buf.getvalue()
    return f'data:image/png;base64,{base64.b64encode(data).decode()}'


# +
# function: moon_exclusion_now()
# -
def moon_exclusion_now():
    return moon_exclusion(f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")}', from_now=False)[0]


# +
# function: moon_exclusion_today()
# -
def moon_exclusion_today():
    return moon_exclusion(f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")}', from_now=False)


# +
# function: observable()
# -
def observable(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False):

    # check input(s)
    ra = DEF__RA if not isinstance(ra, float) else ra
    ra = MIN__RA if ra < MIN__RA else ra
    ra = MAX__RA if ra > MAX__RA else ra
    dec = DEF__DEC if not isinstance(dec, float) else dec
    dec = MIN__DEC if dec < MIN__DEC else dec
    dec = MAX__DEC if dec > MAX__DEC else dec
    date = DEF__DATE if (not isinstance(date, str) or date.strip() == '' or not re.search(ISO__PATTERN, date)) else date
    from_now = False if not isinstance(from_now, bool) else from_now

    # set default(s)
    _obs = np.linspace(math.nan, math.nan, AST__5_MINUTES)
    _time_now = Time.now()
    _time = Time(date) if from_now else Time(date.split()[0])
    _time = Time(_time.iso)
    _time = Time(_time) + (1.0 * u.day * np.linspace(0.0, 1.0, AST__5_MINUTES))

    _exclusion = moon_exclusion(_time)
    _distance = moon_distance(ra, dec, _time)

    # modify to reference frame and get solar position
    _frame = AltAz(obstime=_time, location=KUIPER_OBSERVATORY)
    _radecs = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    _altaz = _radecs.transform_to(_frame)
    _solar_altaz = get_sun(_time).transform_to(_altaz)

    # noinspection PyBroadException
    try:
        for _i in range(len(_solar_altaz)):
            if _solar_altaz[_i].alt >= AST__HORIZON:
                _obs[_i] = False
            elif AST__TWILIGHT < _solar_altaz[_i].alt < AST__HORIZON:
                if AST__NORTH < _solar_altaz[_i].az < AST__SOUTH:
                    # morning twilight
                    _obs[_i] = False
                else:
                    # evening twilight
                    if _altaz[_i].secz > AST__AIRMASS_MAX or _distance[_i] < _exclusion[_i]:
                        _obs[_i] = False
                    else:
                        _obs[_i] = True
            else:
                # sun is below horizon and not in a twilight zone
                if _altaz[_i].secz > AST__AIRMASS_MAX or _distance[_i] < _exclusion[_i]:
                    _obs[_i] = False
                else:
                    _obs[_i] = True

    except Exception:
        _excl = np.linspace(math.nan, math.nan, AST__5_MINUTES)

    # plot it
    fig, ax = plt.subplots()
    ax.plot_date(_time.plot_date, _obs, 'r-')
    ax.plot_date([_time_now.plot_date, _time_now.plot_date], [-999, 999], 'y--')
    xfmt = mdates.DateFormatter('%d-%m-%y %H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    plt.gcf().autofmt_xdate()
    ax.set_ylim([-0.5, 1.5])
    ax.set_xlim([_time.datetime[0], _time.datetime[-1]])
    # ax.set_title(f'{_title}\n{_sub_title}')
    ax.set_ylabel('Observability')
    ax.set_xlabel('Time UTC')
    buf = io.BytesIO()
    # plt.savefig(f'{_file}')
    plt.savefig(f'observability.png')
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    data = buf.getvalue()

    # return result
    return f'data:image/png;base64,{base64.b64encode(data).decode()}'


# +
# function: observable_now()
# -
def observable_now(ra=DEF__RA, dec=DEF__DEC):

    # check input(s)
    ra = DEF__RA if not isinstance(ra, float) else ra
    ra = MIN__RA if ra < MIN__RA else ra
    ra = MAX__RA if ra > MAX__RA else ra
    dec = DEF__DEC if not isinstance(dec, float) else dec
    dec = MIN__DEC if dec < MIN__DEC else dec
    dec = MAX__DEC if dec > MAX__DEC else dec

    # set default(s)
    _time = Time.now()
    _exn = moon_exclusion(_time)
    _mdn = moon_distance(ra, dec, _time)

    # modify to reference frame and get solar position
    _frame = AltAz(obstime=_time, location=KUIPER_OBSERVATORY)
    _radecs = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    _altaz = _radecs.transform_to(_frame)
    _solar_altaz = get_sun(_time).transform_to(_altaz)

    # return result
    if _solar_altaz.alt >= AST__HORIZON:
        # sun is above horizon
        return False
    elif AST__TWILIGHT < _solar_altaz.alt < AST__HORIZON:
        if AST__NORTH < _solar_altaz.az < AST__SOUTH:
            # morning twilight
            return False
        else:
            # evening twilight
            if _altaz.secz > AST__AIRMASS_MAX or _mdn < _exn:
                return False
            else:
                return True
    else:
        # sun is below horizon and not in a twilight zone
        if _altaz.secz > AST__AIRMASS_MAX or _mdn < _exn:
            return False
        else:
            return True


# +
# function: observable_today()
# -
def observable_today(ra=DEF__RA, dec=DEF__DEC):

    # check input(s)
    ra = DEF__RA if not isinstance(ra, float) else ra
    ra = MIN__RA if ra < MIN__RA else ra
    ra = MAX__RA if ra > MAX__RA else ra
    dec = DEF__DEC if not isinstance(dec, float) else dec
    dec = MIN__DEC if dec < MIN__DEC else dec
    dec = MAX__DEC if dec > MAX__DEC else dec

    # set default(s)
    _time = Time.now() + 1*u.day*np.linspace(0.0, 1.0, AST__5_MINUTES)
    _ex = moon_exclusion(_time)
    _md = moon_distance(ra, dec, _time)

    # modify to reference frame and get solar position
    _frame = AltAz(obstime=_time, location=KUIPER_OBSERVATORY)
    _radecs = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    _altaz = _radecs.transform_to(_frame)
    _solar_altaz = get_sun(_time).transform_to(_altaz)

    # noinspection PyBroadException
    try:
        for _i in range(len(_altaz)):
            if (AST__DUSK < _solar_altaz[_i] < AST__HORIZON) and \
                    (_altaz.secz[_i] < AST__AIRMASS_MAX) and (_md[_i] > _ex[_i]):
                return True
            elif (AST__TWILIGHT < _solar_altaz[_i] < AST__DUSK) and \
                    (_altaz.secz[_i] < AST__AIRMASS_MAX) and \
                    (_md[_i] > _ex[_i]):
                return True
            elif (AST__TWILIGHT < _solar_altaz[_i]) and \
                    (_altaz.secz[_i] < AST__AIRMASS_MAX) and \
                    (_md[_i] > _ex[_i]):
                return True
            else:
                return False
    except Exception:
        return False


# +
# function: sky_distance()
# -
def sky_distance(ra1=DEF__RA, dec1=DEF__DEC, ra2=DEF__RA, dec2=DEF__DEC):
    return np.arccos(np.sin(np.deg2rad(dec1))*np.sin(np.deg2rad(dec2)) +
                     np.cos(np.deg2rad(dec1))*np.cos(np.deg2rad(dec2))*np.cos(np.deg2rad(ra1) - np.deg2rad(ra2)))


# +
# command line wrappers()
# -
def _get_date_time(iargs=None):
    if iargs is not None:
        print(get_date_time(offset=int(iargs.offset)))


def _get_date_utctime(iargs=None):
    if iargs is not None:
        print(get_date_utctime(offset=int(iargs.offset)))


def _airmass_plot_day(iargs=None):
    if iargs is not None:
        print(airmass_plot_day(float(iargs.ra), float(iargs.dec), f'{iargs.date}', bool(iargs.from_now)))


def _airmass_plot_dates(iargs=None):
    if iargs is not None:
        _end = (datetime.utcnow() + timedelta(int(iargs.ndays))).strftime("%Y-%m-%d %H:%M:%S.%f")
        print(airmass_plot_dates(float(iargs.ra), float(iargs.dec), f'{iargs.date}', f'{_end}'))


def _moon_distance(iargs=None):
    if iargs is not None:
        print(moon_distance(float(iargs.ra), float(iargs.dec), f'{iargs.date}', bool(iargs.from_now)))


def _moon_distance_plot(iargs=None):
    if iargs is not None:
        print(moon_distance_plot(float(iargs.ra), float(iargs.dec), f'{iargs.date}', bool(iargs.from_now)))


def _moon_distance_now(iargs=None):
    if iargs is not None:
        print(moon_distance_now(float(iargs.ra), float(iargs.dec)))


def _moon_distance_today(iargs=None):
    if iargs is not None:
        print(moon_distance_today(float(iargs.ra), float(iargs.dec)))


def _moon_exclusion(iargs=None):
    if iargs is not None:
        print(moon_exclusion(f'{iargs.date}', bool(iargs.from_now)))


def _moon_exclusion_plot(iargs=None):
    if iargs is not None:
        print(moon_exclusion_plot(f'{iargs.date}', bool(iargs.from_now)))


def _moon_exclusion_now(iargs=None):
    if iargs is not None:
        print(moon_exclusion_now())


def _moon_exclusion_today(iargs=None):
    if iargs is not None:
        print(moon_exclusion_today())


def _observable(iargs=None):
    if iargs is not None:
        print(observable(float(iargs.ra), float(iargs.dec), f'{iargs.date}', bool(iargs.from_now)))


def _observable_now(iargs=None):
    if iargs is not None:
        print(observable_now(float(iargs.ra), float(iargs.dec)))


def _observable_today(iargs=None):
    if iargs is not None:
        print(observable_today(float(iargs.ra), float(iargs.dec)))


def _sky_distance(iargs=None):
    if iargs is not None:
        print(sky_distance(float(iargs.ra1), float(iargs.dec1), float(iargs.ra2), float(iargs.dec2)))


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Check object visibility',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _sp = _p.add_subparsers()

    # add sub-parser for airmass_plot_day(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False)
    _sp_0 = _sp.add_parser('airmass_plot_day', description="Plot airmass for day",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_0.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_0.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_0.add_argument(f'--date', default=DEF__DATE, help=f"Date Start (str), default='%(default)s'")
    _sp_0.add_argument(f'--from-now', default=False, action='store_true',
                       help=f'if present, calculates results from current time')
    _sp_0.set_defaults(func=_airmass_plot_day)

    # add sub-parser for airmass_plot_dates(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, end=DEF__END)
    _sp_1 = _sp.add_parser('airmass_plot_dates', description="Plot airmass for dates",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_1.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_1.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_1.add_argument(f'--date', default=DEF__DATE, help=f"Date Start (str), default='%(default)s'")
    _sp_1.add_argument(f'--ndays', default=1, help=f"Number of days (int), default=%(default)s")
    _sp_1.set_defaults(func=_airmass_plot_dates)

    # add sub-parser for get_date_time(offset=0)
    _sp_2 = _sp.add_parser('get_date_time', description="Get date/time with/without offset",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_2.add_argument(f'--offset', default=0, help=f"Offset in days (int), default=%(default)s")
    _sp_2.set_defaults(func=_get_date_time)

    # add sub-parser for get_date_utctime(offset=0)
    _sp_3 = _sp.add_parser('get_date_utctime', description="Get UTC date/time with/without offset",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_3.add_argument(f'--offset', default=0, help=f"Offset in days (int), default=%(default)s")
    _sp_3.set_defaults(func=_get_date_utctime)

    # add sub-parser for moon_distance(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False)
    _sp_4 = _sp.add_parser('moon_distance', description="Get moon distance for date",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_4.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_4.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_4.add_argument(f'--date', default=DEF__DATE, help=f"Date (str), default='%(default)s'")
    _sp_4.add_argument(f'--from-now', default=False, action='store_true',
                       help=f'if present, calculates results from current time')
    _sp_4.set_defaults(func=_moon_distance)

    # add sub-parser for moon_distance_now(ra=DEF__RA, dec=DEF__DEC)
    _sp_5 = _sp.add_parser('moon_distance_now', description="Get moon distance now",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_5.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_5.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_5.set_defaults(func=_moon_distance_now)

    # add sub-parser for moon_distance_plot(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False)
    _sp_6 = _sp.add_parser('moon_distance_plot', description="Plot moon distance for date",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_6.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_6.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_6.add_argument(f'--date', default=DEF__DATE, help=f"Date Start (str), default='%(default)s'")
    _sp_6.add_argument(f'--from-now', default=False, action='store_true',
                       help=f'if present, calculates results from current time')
    _sp_6.set_defaults(func=_moon_distance_plot)

    # add sub-parser for moon_distance_today(ra=DEF__RA, dec=DEF__DEC)
    _sp_7 = _sp.add_parser('moon_distance_today', description="Get moon distance for today",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_7.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_7.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_7.set_defaults(func=_moon_distance_today)

    # add sub-parser for moon_exclusion(date=DEF__DATE, from_now=False)
    _sp_8 = _sp.add_parser('moon_exclusion', description="Plot moon exclusion for date",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_8.add_argument(f'--date', default=DEF__DATE, help=f"Date Start (str), default='%(default)s'")
    _sp_8.add_argument(f'--from-now', default=False, action='store_true',
                       help=f'if present, calculates results from current time')
    _sp_8.set_defaults(func=_moon_exclusion)

    # add sub-parser for moon_exclusion_plot(date=DEF__DATE, from_now=False)
    _sp_8a = _sp.add_parser('moon_exclusion_plot', description="Plot moon exclusion for date",
                            formatter_class=argparse.RawTextHelpFormatter)
    _sp_8a.add_argument(f'--date', default=DEF__DATE, help=f"Date Start (str), default='%(default)s'")
    _sp_8a.add_argument(f'--from-now', default=False, action='store_true',
                        help=f'if present, calculates results from current time')
    _sp_8a.set_defaults(func=_moon_exclusion_plot)

    # add sub-parser for moon_exclusion_now()
    _sp_9 = _sp.add_parser('moon_exclusion_now', description="Plot moon exclusion now",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_9.set_defaults(func=_moon_exclusion_now)

    # add sub-parser for moon_exclusion_today()
    _sp_a = _sp.add_parser('moon_exclusion_today', description="Plot moon exclusion for today",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_a.set_defaults(func=_moon_exclusion_today)

    # add sub-parser for observable(ra=DEF__RA, dec=DEF__DEC, date=DEF__DATE, from_now=False)
    _sp_b = _sp.add_parser('observable', description="Get object observability for date",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_b.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_b.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_b.add_argument(f'--date', default=DEF__DATE, help=f"Date Start (str), default='%(default)s'")
    _sp_b.add_argument(f'--from-now', default=False, action='store_true',
                       help=f'if present, calculates results from current time')
    _sp_b.set_defaults(func=_observable)

    # add sub-parser for observable_now(ra=DEF__RA, dec=DEF__DEC)
    _sp_c = _sp.add_parser('observable_now', description="Get object observability now",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_c.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_c.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_c.set_defaults(func=_observable_now)

    # add sub-parser for observable_today(ra=DEF__RA, dec=DEF__DEC)
    _sp_d = _sp.add_parser('observable_today', description="Get object observability for date",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_d.add_argument(f'--ra', default=DEF__RA, help=f"Right Ascension (deg), default=%(default)s")
    _sp_d.add_argument(f'--dec', default=DEF__DEC, help=f"Declination (deg), default=%(default)s")
    _sp_d.set_defaults(func=_observable_today)

    # add sub-parser for sky_distance(ra1=DEF__RA, dec1=DEF__DEC, ra2=DEF__RA, dec2=DEF__DEC)
    _sp_e = _sp.add_parser('sky_distance', description="Get separation between objects",
                           formatter_class=argparse.RawTextHelpFormatter)
    _sp_e.add_argument(f'--ra1', default=DEF__RA, help=f"Right Ascension 1 (deg), default=%(default)s")
    _sp_e.add_argument(f'--dec1', default=DEF__DEC, help=f"Declination 1 (deg), default=%(default)s")
    _sp_e.add_argument(f'--ra2', default=DEF__RA, help=f"Right Ascension 2 (deg), default=%(default)s")
    _sp_e.add_argument(f'--dec2', default=DEF__DEC, help=f"Declination 2 (deg), default=%(default)s")
    _sp_e.set_defaults(func=_sky_distance)

    # noinspection PyBroadException
    try:
        args = _p.parse_args()
        args.func(args)
    except Exception:
        print(f'Use: python3 {sys.argv[0]}\n--help for more information')
