
# +
# import(s)
# -
import os

# v1.0
_author_ = ['P. N. Daly']
_comment_ = ['Initial version']
_date_ = ['01/01/2019']
_email_ = ['pndaly@email.arizona.edu']
_organization_ = ['Steward Observatory']
_version_ = ['1.0']

# v1.1
_author_.append('P. N. Daly')
_comment_.append('Support file uploads')
_date_.append('02/01/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.1')

# v1.2
_author_.append('P. N. Daly')
_comment_.append('Support JSON / Non-sidereal observations')
_date_.append('03/01/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.2')

# v1.3
_author_.append('P. N. Daly')
_comment_.append('Add airmass plots')
_date_.append('04/01/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.3')

# v1.4
_author_.append('P. N. Daly')
_comment_.append('Add observation history button')
_date_.append('05/01/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.4')

# v1.5
_author_.append('P. N. Daly')
_comment_.append('Code maintenance tidy-up')
_date_.append('06/01/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.5')

# v1.6
_author_.append('P. N. Daly')
_comment_.append('File uploads from bash script and standalone file upload checking')
_date_.append('07/01/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.6')

# v1.7
_author_.append('P. N. Daly')
_comment_.append('Moved logout button, added version route and updated api documentation')
_date_.append('10/28/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.7')

# v1.8
_author_.append('P. N. Daly')
_comment_.append('Re-worked view_observable, fixed airmass plots')
_date_.append('10/31/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.8')


# v1.9
_author_.append('P. N. Daly')
_comment_.append('Enabled binning up to 4x4')
_date_.append('11/05/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('1.9')


# v2.0
_author_.append('P. N. Daly')
_comment_.append('Added links for download scripts, fixed update observation record for binning')
_date_.append('12/05/2019')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('2.0')


# v2.1
_author_.append('P. N. Daly')
_comment_.append('Added clear sky maps, re-worked control section of page(s)')
_date_.append('01/14/2020')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('2.1')


# v2.2
_author_.append('P. N. Daly')
_comment_.append('Added new telescope objects and simulation mode')
_date_.append('01/20/2020')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('2.2')


# v2.3
_author_.append('P. N. Daly')
_comment_.append('Added user history form and rudimentary night log')
_date_.append('01/24/2020')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('2.3')


# v2.4
_author_.append('P. N. Daly')
_comment_.append('Completed night log with optional PDF output')
_date_.append('01/31/2020')
_email_.append('pndaly@email.arizona.edu')
_organization_.append('Steward Observatory')
_version_.append('2.4')


# reverse list(s)
_author_.reverse()
_comment_.reverse()
_date_.reverse()
_email_.reverse()
_organization_.reverse()
_version_.reverse()


# +
# function: get_history()
# -
def get_history(_file='', _copy='', _list=None):
    _h = f'\n{_file}\n{_copy}\n'
    for _a, _c, _d, _e, _o, _v in list(_list):
        _h += f'{_d}: v{_v} - {_c} ({_a}, {_e}, {_o})\n'
    return _h


# +
# get history
# -
HISTORY = get_history(
    f'Project: {os.getenv("ARTN-ORP")}.', 
    f'\u00a9 2018\u20142020 {_organization_[0]}. All rights reserved. Released under the GPL v3.\n',
    zip(_author_, _comment_, _date_, _email_, _organization_, _version_)
)
HISTORY_HTML = f'<span style="white-space: pre-wrap">{HISTORY}</span>'
