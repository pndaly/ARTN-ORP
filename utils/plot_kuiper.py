#!/usr/bin/env python3.7


# +
# import(s)
# -
from astropy.coordinates import get_moon, get_sun, SkyCoord, EarthLocation, AltAz
from astropy.time import Time
from astropy.utils import iers
from astropy.visualization import astropy_mpl_style
from datetime import datetime, timedelta

import argparse
import astropy.units as u
import functools
import numpy as np
import matplotlib.pyplot as plt
import math
import re
import warnings


# +
# initialize
# -
warnings.filterwarnings('ignore')
plt.style.use(astropy_mpl_style)


# +
# function(s)
# -
def get_time(_offset=0):
    return (datetime.now() + timedelta(days=_offset)).isoformat()


def get_utc(_offset=0):
    return (datetime.utcnow() + timedelta(days=_offset)).isoformat()


def utc_to_mjd(_iso=''):
    # noinspection PyBroadException
    try:
        return float(Time(_iso).mjd)
    except Exception:
        return float(math.nan)


def mjd_to_utc(_mjd=0.0):
    # noinspection PyBroadException
    try:
        return Time(_mjd+2400000.5, format='jd', precision=3).isot
    except Exception:
        return None


def time2string(_delta=0.0):
    if not isinstance(_delta, float) or _delta < 0.0:
        return ''
    _limit = [_v for _v in TIME_VALUES if _v <= _delta]
    if _limit:
        _limit = _limit[0]
    else:
        _limit = 1.0
    return f"{_delta/_limit:.2f} {TIME_SYMBOLS[TIME_VALUES.index(_limit)]}"


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args_in, **kwargs_in):
        _ts = float(utc_to_mjd(get_utc()))
        print(f'Calling  {func.__name__}()')
        try:
            _res = func(*args_in, **kwargs_in)
        except Exception as _e:
            print(f'Failed   {func.__name__}(), e={_e}')
            return None
        else:
            print(f'Called   {func.__name__}() OK')
            _delta = (float(utc_to_mjd(get_utc())) - _ts) * 86400.0
            print(f'         {func.__name__}() took {time2string(_delta)}')
            return _res
    return wrapper


# +
# constant(s)
# -
CAT_FILE = 'finals2000A'
CAT_DATE = utc_to_mjd(get_utc())
iers.IERS_A_URL = 'ftp://cddis.gsfc.nasa.gov/pub/products/iers/{CAT_FILE}.all'
KUIPER_ALTITUDE = 2510.028
KUIPER_LATITUDE = 32.4165
KUIPER_LONGITUDE = -110.7345
KUIPER = EarthLocation(lat=KUIPER_LATITUDE*u.deg, lon=KUIPER_LONGITUDE*u.deg, height=KUIPER_ALTITUDE*u.m)
PLOT_TYPES = ['Airmass', 'Night']
TIME_SYMBOLS = (u's', u'ms', u'\u00B5s', u'ns', u'ps', u'fs', u'as', u'zs', u'ys')
TIME_VALUES = tuple([math.pow(10, -3*i) for i in range(len(TIME_SYMBOLS))])
UTC_FORMAT = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}')


# +
# update catalog
# -
# _cat_file = os.path.abspath(os.path.expanduser(f"{os.getenv('HOME')}/.{CAT_FILE}.dat"))
# _cat_date = CAT_DATE
# if os.path.exists(_cat_file):
#     with open(_cat_file, 'r') as _fr:
#         _cat_date = float(_fr.read())
# print(f"_cat_date = {_cat_date}")
# print(f"CAT_DATE = {CAT_DATE}")
#
# if (float(CAT_DATE) - float(_cat_date)) > 7.0:
#     try:
#         # iers.IERS_A_URL = 'ftp://cddis.gsfc.nasa.gov/pub/products/iers/{CAT_FILE}.all'
#         astroplan.download_IERS_A()
#     except Exception:
#         print(f"Failed to update {_cat_file}")
#     try:
#         print(f"Updating {_cat_date}")
#         os.remove(_cat_file)
#         with open(_cat_file, 'w') as _fw:
#             _fw.write(f"{CAT_DATE}\n")
#     except Exception:
#         pass


# +
# time some thing(s)
# -
@timeit
def _time_wrapper(_utc=''):
    if not isinstance(_utc, str) or re.match(UTC_FORMAT, _utc) is None:
        return None
    return Time(f'{_utc}')


@timeit
def _midnight_wrapper(_utc=''):
    if not isinstance(_utc, str) or re.match(UTC_FORMAT, _utc) is None:
        return None
    return mjd_to_utc(math.floor(utc_to_mjd(_utc) + 1.0))


@timeit
def _coords_wrapper(_name=''):
    if not isinstance(_name, str) or _name.strip() == '':
        return None
    return SkyCoord.from_name(f'{_name}')


@timeit
def _altaz_wrapper(_target=None, _time=None):
    if _target is None or _time is None:
        return None
    return _target.transform_to(AltAz(obstime=_time, location=KUIPER))


@timeit
def _d_array_wrapper():
    # noinspection PyUnresolvedReferences
    return np.linspace(-12, 12, 400)*u.hour


@timeit
def _d_times_wrapper(_midnight=None, _d_array=None):
    return Time(_midnight)+_d_array


@timeit
def _d_frame_wrapper(_d_times=None, _location=None):
    return AltAz(obstime=_d_times, location=_location)


@timeit
def _d_sun_wrapper(_d_times=None, _d_frame=None):
    return get_sun(_d_times).transform_to(_d_frame)


@timeit
def _d_moon_wrapper(_d_times=None, _d_frame=None):
    return get_moon(_d_times).transform_to(_d_frame)


@timeit
def _d_altazs_wrapper(_target=None, _d_frame=None):
    return _target.transform_to(_d_frame)


# +
# function: plot()
# -
def plot(_name='', _plot='', _utc='', _verbose=True):

    # check input(s)
    if not isinstance(_name, str) or _name.strip() == '':
        raise Exception(f'Invalid argument, _name={_name}')
    if not isinstance(_plot, str) or _plot.lower() not in [_x.lower() for _x in PLOT_TYPES]:
        raise Exception(f'Invalid argument, _plot={_plot}')
    if not isinstance(_utc, str) or re.match(UTC_FORMAT, _utc) is None:
        raise Exception(f'Invalid argument, _utc={_utc}')
    _verbose = _verbose if isinstance(_verbose, bool) else False

    # convert (with timing)
    _time = _time_wrapper(f'{_utc}')
    _midnight = _midnight_wrapper(f'{_utc}')
    _target = _coords_wrapper(f'{_name}')
    _target_altaz = _altaz_wrapper(_target, _time)

    # select plot
    if _plot.lower() == 'airmass':

        try:
            # calculate
            # noinspection PyUnresolvedReferences
            _m_array = np.linspace(-2, 10, 100)*u.hour
            _m_times = Time(_midnight)+_m_array
            _m_frame = AltAz(obstime=_m_times, location=KUIPER)
            _m_altazs = _target.transform_to(_m_frame)
            _m_airmass = _m_altazs.secz
            if _verbose:
                print(f"_m_array = {_m_array}")
                print(f"_m_times = {_m_times}")
                print(f"_m_frame = {_m_frame}")
                print(f"_m_altazs = {_m_altazs}")
                print(f"_m_airmass = {_m_airmass}")

            # plot
            plt.plot(_m_array, _m_airmass)
            plt.xlim(-2, 10)
            plt.ylim(1, 4)
            plt.xlabel('Hours from Midnight')
            plt.ylabel('Airmass [Sec(z)]')
            plt.show()
        except Exception:
            raise Exception(f'Invalid airmass plot, _name={_name}')

    elif _plot.lower() == 'night':

        try:
            # calculate
            # _d_array = np.linspace(-12, 12, 400)*u.hour
            _d_array = _d_array_wrapper()

            # _d_times = Time(_midnight)+_d_array
            _d_times = _d_times_wrapper(_midnight, _d_array)

            # _d_frame = AltAz(obstime=_d_times, location=KUIPER)
            _d_frame = _d_frame_wrapper(_d_times, KUIPER)

            # _d_sun = get_sun(_d_times).transform_to(_d_frame)
            _d_sun = _d_sun_wrapper(_d_times, _d_frame)

            # _d_moon = get_moon(_d_times).transform_to(_d_frame)
            _d_moon = _d_moon_wrapper(_d_times, _d_frame)

            # _d_altazs = _target.transform_to(_d_frame)
            _d_altazs = _d_altazs_wrapper(_target, _d_frame)

            # if _verbose:
            #    print(f"_d_array = {_d_array}")
            #    print(f"_d_times = {_d_times}")
            #    print(f"_d_frame = {_d_frame}")
            #    print(f"_d_sun = {_d_sun}")
            #    print(f"_d_moon = {_d_moon}")
            #    print(f"_d_altazs = {_d_altazs}")

            # plot
            plt.plot(_d_array, _d_sun.alt, color='r', label='Sun')
            plt.plot(_d_array, _d_moon.alt, color=[0.75]*3, ls='--', label='Moon')
            plt.scatter(_d_array, _d_altazs.alt, c=_d_altazs.az, label=f'{_name}', lw=0, s=8, cmap='viridis')
            plt.fill_between(_d_array.to('hr').value, 0, 90, _d_sun.alt < -0*u.deg, color='0.5', zorder=0)
            plt.fill_between(_d_array.to('hr').value, 0, 90, _d_sun.alt < -18*u.deg, color='k', zorder=0)
            plt.colorbar().set_label('Azimuth [deg]')
            plt.legend(loc='upper left')
            plt.xlim(-12, 12)
            plt.xticks(np.arange(13)*2 - 12)
            plt.ylim(0, 90)
            plt.xlabel('Hours from Midnight')
            plt.ylabel('Altitude [deg]')
            plt.show()
        except Exception:
            raise Exception(f'Invalid night plot, _name={_name}')


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Read Database File', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--name', default='M33', help="""Object name, default=%(default)s""")
    _p.add_argument(f'--plot', default=PLOT_TYPES[1], help=f"""Plot type, default=%(default)s, one of {PLOT_TYPES}""")
    _p.add_argument(f'--utc', default=get_utc(), help="""UTC date/time, default=%(default)s""")
    _p.add_argument(f'--verbose', default=False, action='store_true', help=f'if present, produce more verbose output')
    args = _p.parse_args()
    plot(_name=args.name, _plot=args.plot, _utc=args.utc, _verbose=bool(args.verbose))
