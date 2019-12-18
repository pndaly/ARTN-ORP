#!/bin/sh


# +
# edit as required
# -
export ARTN_HOME=${1:-${PWD}}
export ARTN_BIN=${ARTN_HOME}/bin
export ARTN_ETC=${ARTN_HOME}/etc
export ARTN_LOGS=${ARTN_HOME}/logs
export ARTN_SRC=${ARTN_HOME}/src

export ARTN_DB_HOST="localhost"
export ARTN_DB_USER="artn"
export ARTN_DB_PASS="db_secret"
export ARTN_DB_NAME="artn"
export ARTN_DB_PORT=5432

export MAIL_SERVER=smtp.googlemail.com
export MAIL_PORT=587
export MAIL_USE_TLS=1
export MAIL_USE_SSL=1
export MAIL_USERNAME="artn@dev.null"
export MAIL_PASSWORD="db_secret"

export RTS2SOLIBPATH="${ARTN_SRC}/telescopes" # this is the path to the rts2_config.json file
export RTS2SOLIBSRC="${ARTN_SRC}/rts2solib"   # this is the path to the rts2solib code


# +
# PYTHONPATH
# -
if [[ -z "${PYTHONPATH}" ]]; then
  export PYTHONPATH=`pwd`
fi
export PYTHONPATH=${ARTN_HOME}:${ARTN_SRC}:${RTS2SOLIBSRC}:${PYTHONPATH}
