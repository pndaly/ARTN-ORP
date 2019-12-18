#!/usr/bin/env python3.7


# +
# import(s)
# -
import argparse
import base64
import os


# +
# function: read_png()
# -
def read_png(_file=''):

    # check input(s)
    _file = os.path.abspath(os.path.expanduser(_file))
    if not os.path.exists(_file):
        raise Exception(f'Invalid argument, _file={_file}')

    # read file
    with open(f"{_file}", "rb") as f:
        print(f'data:image/png;base64,{base64.b64encode(f.read()).decode()}')


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Read PNG File', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--file', default='', help=f'input file')
    args = _p.parse_args()
    read_png(args.file)
