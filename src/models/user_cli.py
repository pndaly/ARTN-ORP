#!/usr/bin/env python3.7


# +
# import(s)
# -
from src import *
from src.models.Models import User
from src.models.Models import user_filters
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import argparse
import sys


# +
# __doc__ string
# -
__doc__ = """

  CLI:
    % python3.7 user_cli.py --help

"""


# +
# user_cli_db()
# -
def user_cli_db(iargs=None):

    # check input(s)
    if iargs is None:
        raise Exception(f'Insufficient command line arguments specified\nUse: python3.7 {sys.argv[0]} --help')

    # set default(s)
    request_args = {}

    # get input(s)
    if iargs.id:
        request_args['id'] = f'{iargs.id}'
    if iargs.id__gte:
        request_args['id__gte'] = int(f'{iargs.id__gte}')
    if iargs.id__lte:
        request_args['id__lte'] = f'{iargs.id__lte}'
    if iargs.firstname:
        request_args['firstname'] = f'{iargs.firstname}'
    if iargs.lastname:
        request_args['lastname'] = f'{iargs.lastname}'
    if iargs.username:
        request_args['username'] = f'{iargs.username}'
    if iargs.email:
        request_args['email'] = f'{iargs.email}'
    if iargs.affiliation:
        request_args['affiliation'] = f'{iargs.affiliation}'
    if iargs.created_iso__gte:
        request_args['created_iso__gte'] = f'{iargs.created_iso__gte}'
    if iargs.created_iso__lte:
        request_args['created_iso__lte'] = f'{iargs.created_iso__lte}'
    if iargs.created_mjd__gte:
        request_args['created_mjd__gte'] = f'{iargs.created_mjd__gte}'
    if iargs.created_mjd__lte:
        request_args['created_mjd__lte'] = f'{iargs.created_mjd__lte}'
    if iargs.last_seen_iso__gte:
        request_args['last_seen_iso__gte'] = f'{iargs.last_seen_iso__gte}'
    if iargs.last_seen_iso__lte:
        request_args['last_seen_iso__lte'] = f'{iargs.last_seen_iso__lte}'
    if iargs.last_seen_mjd__gte:
        request_args['last_seen_mjd__gte'] = f'{iargs.last_seen_mjd__gte}'
    if iargs.last_seen_mjd__lte:
        request_args['last_seen_mjd__lte'] = f'{iargs.last_seen_mjd__lte}'
    if iargs.is_admin:
        request_args['is_admin'] = f'{iargs.is_admin}'
    if iargs.is_disabled:
        request_args['is_disabled'] = f'{iargs.is_disabled}'

    # connect to database
    try:
        engine = create_engine(f'postgresql+psycopg2://{ARTN_DB_USER}:{ARTN_DB_PASS}@'
                               f'{ARTN_DB_HOST}:{ARTN_DB_PORT}/{ARTN_DB_NAME}')
        get_session = sessionmaker(bind=engine)
        session = get_session()
    except Exception:
        raise Exception('Failed to connect to database')

    if iargs.verbose:
        print(f'request_args = {request_args}')
    # execute query
    try:
        query = session.query(User)
        query = user_filters(query, request_args)
        query = query.order_by(User.id.desc())
        if iargs.verbose:
            print(f'query = {query}')
    except Exception:
        raise Exception('Failed to execute query')

    # output result(s)
    res = ''
    for _e in User.serialize_list(query.all()):
        _s = ''.join("{}='{}' ".format(str(k), str(v)) for k, v in _e.items())[:-1]
        res = f'{res}\n{_s}'
    return res[1:] if (res != '' and res[0] == '\n') else res


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Query User Database', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--id', help=f'id <int>')
    _p.add_argument(f'--id__gte', help=f'id >= <int>')
    _p.add_argument(f'--id__lte', help=f'id <= <int>')
    _p.add_argument(f'--firstname', help=f'firstname <str>')
    _p.add_argument(f'--lastname', help=f'lastname <str>')
    _p.add_argument(f'--username', help=f'username <str>')
    _p.add_argument(f'--email', help=f'email <str>')
    _p.add_argument(f'--affiliation', help=f'affiliation <str>')
    _p.add_argument(f'--created_iso__gte', help=f'created_iso >= <YYYY-MM-DD>')
    _p.add_argument(f'--created_iso__lte', help=f'created_iso <= <YYYY-MM-DD>')
    _p.add_argument(f'--created_mjd__gte', help=f'created_mjd >= <float>')
    _p.add_argument(f'--created_mjd__lte', help=f'created_mjd <= <float>')
    _p.add_argument(f'--last_seen_iso__gte', help=f'last_seen_iso >= <YYYY-MM-DD>')
    _p.add_argument(f'--last_seen_iso__lte', help=f'last_seen_iso <= <YYYY-MM-DD>')
    _p.add_argument(f'--last_seen_mjd__gte', help=f'last_seen_mjd >= <float>')
    _p.add_argument(f'--last_seen_mjd__lte', help=f'last_seen_mjd <= <float>')
    _p.add_argument(f'--is_admin', help=f'is_admin == <bool>')
    _p.add_argument(f'--is_disabled', help=f'is_disabled == <bool>')
    _p.add_argument(f'--verbose', default=False, action='store_true', help=f'if present, produce more verbose output')

    # execute
    print(f"{user_cli_db(_p.parse_args())}")
