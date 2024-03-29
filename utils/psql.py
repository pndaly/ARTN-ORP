#!/usr/bin/env python3


# +
# import(s)
# -
from src import UtilsLogger

import argparse
import pprint
import psycopg2
import sys


# +
# dunder string(s)
# -
__doc__ = """

    % python3 psql.py --help

"""


# +
# constant(s)
# -
DEFAULT_COMMAND = f'SELECT * FROM obsreqs;'
FETCH_METHOD = ['fetchall', 'fetchone', 'fetchmany']
FETCH_MANY = 50
KEYS = ('authorization', 'command', 'database', 'method', 'nelms', 'port', 'server', 'verbose')
RESULTS_PER_PAGE = 50

ARTN_DB_AUTHORIZATION = f"artn:********"
# ARTN_DB_HOST = "scopenet.as.arizona.edu"
ARTN_DB_HOST = "scopenet"
ARTN_DB_NAME = "artn"
ARTN_DB_PORT = 5432
ARTN_CONNECT_MSG = f'{ARTN_DB_HOST}:{ARTN_DB_PORT}/{ARTN_DB_NAME} using {ARTN_DB_AUTHORIZATION}'


# +
# class: Psql()
# -
class Psql(object):

    # +
    # method: __init__()
    # -
    def __init__(self, authorization=ARTN_DB_AUTHORIZATION, database=ARTN_DB_NAME, 
                 port=ARTN_DB_PORT, server=ARTN_DB_HOST, logger=None):

        # get input(s)
        self.authorization = authorization
        self.database = database
        self.port = port
        self.server = server
        self.logger = logger

        # private variable(s)
        self.__connection = None
        self.__cursor = None
        self.__connection_string = None
        self.__result = None
        self.__results = None

    # +
    # decorator(s)
    # -
    @property
    def authorization(self):
        return self.__authorization

    @authorization.setter
    def authorization(self, authorization):
        self.__authorization = authorization if (
                isinstance(authorization, str) and authorization.strip() != f'' and
                f':' in authorization) else ARTN_DB_AUTHORIZATION
        self.__username, self.__password = self.__authorization.split(f':')

    @property
    def database(self):
        return self.__database

    @database.setter
    def database(self, database):
        self.__database = database if (isinstance(database, str) and database.strip() != f'') else ARTN_DB_NAME

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, port):
        self.__port = port if (isinstance(port, int) and port > 0) else int(ARTN_DB_PORT)

    @property
    def server(self):
        return self.__server

    @server.setter
    def server(self, server):
        self.__server = server if (isinstance(server, str) and server.strip() != f'') else ARTN_DB_HOST

    @property
    def logger(self):
        return self.__logger

    @logger.setter
    def logger(self, logger):
        self.__logger = logger

    # +
    # method: connect()
    # -
    def connect(self):
        """ connect to database """

        # set variable(s)
        self.__connection = None
        self.__connection_string = f"host='{self.__server}' dbname='{self.__database}' " \
            f"user='{self.__username}' password='{self.__password}'"
        self.__cursor = None

        # get connection
        if self.__logger:
            self.__logger.info(f'Connecting to {ARTN_CONNECT_MSG}')
        try:
            if self.__logger:
                self.__logger.info(f'{self.__connection_string}')
            self.__connection = psycopg2.connect(self.__connection_string)
        except Exception as e:
            self.__connection = None
            if self.__logger:
                self.__logger.error(f'failed connecting to {ARTN_CONNECT_MSG}, error={e}')
        else:
            if self.__logger:
                self.__logger.info(f'Connected to {ARTN_CONNECT_MSG}')

        # get cursor
        if self.__logger:
            self.__logger.info(f'Getting cursor for {ARTN_CONNECT_MSG}')
        try:
            self.__cursor = self.__connection.cursor()
        except Exception as e:
            self.__cursor = None
            if self.__logger:
                self.__logger.error(f'failed getting cursor for {ARTN_CONNECT_MSG}, error={e}')
        else:
            if self.__logger:
                self.__logger.info(f'Got cursor for {ARTN_CONNECT_MSG}')

    # +
    # method: disconnect()
    # -
    def disconnect(self):
        """ disconnect from database """

        # disconnect cursor
        if self.__cursor is not None:
            if self.__logger:
                self.__logger.info(f'Disconnecting cursor')
            self.__cursor.close()

        # disconnect connection
        if self.__connection is not None:
            if self.__logger:
                self.__logger.info(f'Disconnecting connection')
            self.__connection.close()

        # reset variable(s)
        self.__connection = None
        self.__cursor = None

    # +
    # method: fetchall()
    # -
    def fetchall(self, command=''):
        """ execute fetchall() command """

        # check input(s)
        if not isinstance(command, str) or command.strip() == '':
            if self.__logger:
                self.__logger.error(f'invalid input, command={command}')
            return f''

        # execute query
        if self.__logger:
            self.__logger.info(f'Executing "{command}"')
        try:
            self.__cursor.execute(command)
            self.__results = self.__cursor.fetchall()
        except Exception as _e:
            if self.__logger:
                self.__logger.error(f"error={_e}")
            self.__results = None
        if self.__logger:
            self.__logger.info(f'Executed "{command}"')

        # return result(s)
        return self.__results

    # +
    # method: fetchmany()
    # -
    def fetchmany(self, command='', number=0):
        """ execute fetchmany() command """

        # check input(s)
        if not isinstance(command, str) or command.strip() == '':
            if self.__logger:
                self.__logger.error(f'invalid input, command={command}')
            return f''
        if not isinstance(number, int) or number <= 0:
            if self.__logger:
                self.__logger.error(f'invalid input, number={number}')
            return f''

        # execute query
        if self.__logger:
            self.__logger.info(f'Executing "{command}"')
        try:
            self.__cursor.execute(command)
            self.__results = self.__cursor.fetchmany(number)
        except Exception as _e:
            if self.__logger:
                self.__logger.error(f"error={_e}")
            self.__results = None
        if self.__logger:
            self.__logger.info(f'Executed "{command}"')

        # return result(s)
        return self.__results

    # +
    # method: fetchone()
    # -
    def fetchone(self, command=''):
        """ execute fetchone() command """

        # check input(s)
        if not isinstance(command, str) or command.strip() == '':
            if self.__logger:
                self.__logger.error(f'invalid input, command={command}')
            return f''

        # execute query
        if self.__logger:
            self.__logger.info(f'Executing {command}')
        try:
            self.__cursor.execute(command)
            self.__result = self.__cursor.fetchone()
        except Exception as _e:
            if self.__logger:
                self.__logger.error(f"error={_e}")
            self.__result = None
        if self.__logger:
            self.__logger.info(f'Executed {command}')

        # return result
        return self.__result


# +
# function: psql()
# -
def psql(iargs=None):

    # check input(s)
    if iargs is None or iargs is {} or not isinstance(iargs, dict):
        raise Exception(f'invalid input(s), iargs={iargs}')
    if not all(_k in iargs for _k in KEYS):
        raise Exception(f'invalid dictionary, iargs={iargs}')

    # set default(s)
    _authorization = iargs['authorization'].strip()
    _command = iargs['command'].strip()
    _database = iargs['database'].strip()
    _method = iargs['method'].strip().lower()
    _nelms = int(iargs['nelms'])
    _port = int(iargs['port'])
    _server = iargs['server'].strip()
    _verbose = bool(iargs['verbose'])

    #  create logger
    _logger = UtilsLogger('psql').logger if _verbose else None

    # instantiate class
    try:
        _t = Psql(_authorization, _database, _port, _server, _logger)
    except Exception as e:
        raise Exception(f'failed to create class, error={e}')
    if _verbose:
        _logger.info(f'Psql(authorization={_t.authorization}, database={_t.database}, '
                     f'port={_t.port}, server={_t.server}, logger={_t.logger}) created OK')

    # do something
    if _t:

        # connect
        _t.connect()

        # select
        if _method == 'fetchall':
            _all = _t.fetchall(_command)
            if _all:
                if _verbose:
                    _logger.debug(f'_t.fetchall(\"{_command}\"), returns:')
                pprint.pprint(f'{_all}')

        elif _method == 'fetchone':
            _one = _t.fetchone(_command)
            if _one:
                if _verbose:
                    _logger.info(f'_t.fetchone(\"{_command}\"), returns:')
                pprint.pprint(f'{_one}')

        elif _method == 'fetchmany':
            _many = _t.fetchmany(_command, _nelms)
            if _many:
                if _verbose:
                    _logger.info(f'_t.fetchmany(\"{_command}\", {_nelms}), returns:')
                pprint.pprint(f'{_many}')

        # disconnect
        _t.disconnect()


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _parser = argparse.ArgumentParser(description=f'Test PostGresQL Database Connection',
                                      formatter_class=argparse.RawTextHelpFormatter)
    _parser.add_argument(f'-a', f'--authorization', default=f'{ARTN_DB_AUTHORIZATION}',
                         help=f"""database authorization=<str>:<str>, defaults to '%(default)s'""")
    _parser.add_argument(f'-c', f'--command', default=DEFAULT_COMMAND,
                         help=f"""database command=<str>, defaults to \"%(default)s\"""")
    _parser.add_argument(f'-d', f'--database', default=f'{ARTN_DB_NAME}',
                         help=f"""database name=<str>, defaults to '%(default)s'""")
    _parser.add_argument(f'-m', f'--method', default=f'{FETCH_METHOD[1]}',
                         help=f"""database method=<str>, in {FETCH_METHOD} defaults to %(default)s""")
    _parser.add_argument(f'-n', f'--nelms', default=FETCH_MANY,
                         help=f"""database nelms=<int> (for fetchmany) defaults to %(default)s""")
    _parser.add_argument(f'-p', f'--port', default=int(ARTN_DB_PORT),
                         help=f"""database port=<int>, defaults to %(default)s""")
    _parser.add_argument(f'-s', f'--server', default=f'{ARTN_DB_HOST}',
                         help=f"""database server=<address>,  defaults to '%(default)s'""")
    _parser.add_argument(f'-v', f'--verbose', default=False, action='store_true', 
                         help=f'if present, produce more verbose output')
    args = _parser.parse_args()

    # execute
    if args:
        psql(dict(vars(args)))
    else:
        raise Exception(f'Insufficient command line arguments specified\nUse: python3 {sys.argv[0]} --help')
