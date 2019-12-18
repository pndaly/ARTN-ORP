#!/bin/sh


# +
# edit as required
# -
export ORP_HOME=${1:-${PWD}}
export ORP_APP_HOST=${2:-"locahost"}
export ORP_APP_PORT=${3:-5000}
export ORP_BIN=${ORP_HOME}/bin
export ORP_ETC=${ORP_HOME}/etc
export ORP_LOGS=${ORP_HOME}/logs
export ORP_SRC=${ORP_HOME}/src
export ORP_UTILS=${ORP_HOME}/utils


# +
# PYTHONPATH
# -
if [[ -z "${PYTHONPATH}" ]]; then
  export PYTHONPATH=`pwd`
fi
export PYTHONPATH=${ORP_HOME}:${ORP_SRC}:${PYTHONPATH}
