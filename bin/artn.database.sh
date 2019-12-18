#!/bin/sh


# +
#
# Name:        artn.database.sh
# Description: ARTN Database Control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190415
# Execute:     % bash artn.database.sh --help
#
# -


# +
# default(s) - edit as required
# -
def_db_name="artn"
def_db_pass="db_secret"
def_db_host="localhost:5432"
def_db_user="artn"

dry_run=0


# +
# variable(s)
# -
artn_db_name="${def_db_name}"
artn_db_pass="${def_db_pass}"
artn_db_host="${def_db_host}"
artn_db_user="${def_db_user}"


# +
# utility functions
# -
write_blue () {
  BLUE='\033[0;34m'
  NCOL='\033[0m'
  printf "${BLUE}${1}${NCOL}\n"
}
write_red () {
  RED='\033[0;31m'
  NCOL='\033[0m'
  printf "${RED}${1}${NCOL}\n"
}
write_yellow () {
  YELLOW='\033[0;33m'
  NCOL='\033[0m'
  printf "${YELLOW}${1}${NCOL}\n"
}
write_green () {
  GREEN='\033[0;32m'
  NCOL='\033[0m'
  printf "${GREEN}${1}${NCOL}\n"
}
write_cyan () {
  CYAN='\033[0;36m'
  NCOL='\033[0m'
  printf "${CYAN}${1}${NCOL}\n"
}
usage () {
  write_blue   ""                                                                                                 2>&1
  write_blue   "ARTN Database Control"                                                                            2>&1
  write_blue   ""                                                                                                 2>&1
  write_green  "Use:"                                                                                             2>&1
  write_green  "  %% bash $0 --database=<str> --hostname=<str:int> --password=<str> --username=<str> [--dry-run]" 2>&1
  write_yellow ""                                                                                                 2>&1
  write_yellow "Input(s):"                                                                                        2>&1
  write_yellow "  --database=<str>,      where <str> is the database name,               default=${def_db_name}"  2>&1
  write_yellow "  --hostname=<str:int>,  where <str> is the database hostname and port,  default=${def_db_host}"  2>&1
  write_yellow "  --password=<str>,      where <str> is the database password,           default=${def_db_pass}"  2>&1
  write_yellow "  --username=<str>,      where <str> is the database username,           default=${def_db_user}"  2>&1
  write_yellow ""                                                                                                 2>&1
  write_cyan   "Flag(s):"                                                                                         2>&1
  write_cyan   "  --dry-run,             show (but do not execute) commands,             default=false"           2>&1
  write_cyan   ""                                                                                                 2>&1
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --database*|--DATABASE*)
      artn_db_name=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    --password*|--PASSWORD*)
      artn_db_pass=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --username*|--USERNAME*)
      artn_db_user=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --hostname*|--HOSTNAME*)
      artn_db_host=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --help|*)
      usage
      exit 0
      ;;
  esac
done


# +
# check and (re)set variable(s)
# -
if [[ -z ${artn_db_name} ]]; then
  artn_db_name=${def_db_name}
fi
if [[ -z ${artn_db_host} ]]; then
  artn_db_host=${def_db_host}
fi
if [[ -z ${artn_db_pass} ]]; then
  artn_db_pass=${def_db_pass}
fi
if [[ -z ${artn_db_user} ]]; then
  artn_db_user=${def_db_user}
fi


# +
# write file to create database
# -
_host=$(echo ${artn_db_host} | cut -d':' -f1)
_port=$(echo ${artn_db_host} | cut -d':' -f2)
_os=`echo $(uname -sr) | cut -d' ' -f1`

if [[ "${_os}" == "Darwin" ]]; then
  PSQL_CMD="psql --echo-all -h ${_host} -p ${_port}"
else
  PSQL_CMD="sudo -u postgres psql --echo-all -h ${_host} -p ${_port}"
fi

if [[ -f /tmp/artn.database.sh ]]; then
  rm -f /tmp/artn.database.sh
fi

echo "#!/bin/sh"                                                                              >> /tmp/artn.database.sh 2>&1
echo "${PSQL_CMD} << EOF"                                                                     >> /tmp/artn.database.sh 2>&1
echo "DROP DATABASE IF EXISTS ${artn_db_name};"                                               >> /tmp/artn.database.sh 2>&1
echo "DROP USER IF EXISTS ${artn_db_user};"                                                   >> /tmp/artn.database.sh 2>&1
echo "CREATE ROLE ${artn_db_user} LOGIN SUPERUSER CREATEDB CREATEROLE REPLICATION BYPASSRLS;" >> /tmp/artn.database.sh 2>&1
echo "ALTER ROLE ${artn_db_user} WITH ENCRYPTED PASSWORD '${artn_db_pass}';"                  >> /tmp/artn.database.sh 2>&1
echo "CREATE DATABASE ${artn_db_name};"                                                       >> /tmp/artn.database.sh 2>&1
echo "GRANT ALL PRIVILEGES ON DATABASE ${artn_db_name} TO ${artn_db_user};"                   >> /tmp/artn.database.sh 2>&1
echo "ALTER DATABASE ${artn_db_name} OWNER TO ${artn_db_user};"                               >> /tmp/artn.database.sh 2>&1
echo "EOF"                                                                                    >> /tmp/artn.database.sh 2>&1


# +
# execute
# -
write_blue "%% bash $0 --database=${artn_db_name} --hostname=${artn_db_host} --password=${artn_db_pass} --username=${artn_db_user} --dry-run=${dry_run}"
if [[ ${dry_run} -eq 1 ]]; then
  if [[ "${USER}" != "root" ]]; then
    write_red "WARNING: you need to be root to execute these commands!"
  fi
  if [[ ! -f /tmp/artn.database.sh ]]; then
    write_red "WARNING: /tmp/artn.database.sh does not exist!"
  fi
  write_yellow "Dry-Run> chmod a+x /tmp/artn.database.sh"
  write_yellow "Dry-Run> bash /tmp/artn.database.sh"
  write_yellow "Dry-Run> rm -f /tmp/artn.database.sh"

else
  if [[ "${USER}" != "root" ]]; then
    write_red "ERROR: you need to be root to execute these commands!"
    usage
    exit
  fi
  if [[ ! -f /tmp/artn.database.sh ]]; then
    write_red "ERROR: /tmp/artn.database.sh does not exist!"
    usage
    exit
  fi
  write_green "Executing> chmod a+x /tmp/artn.database.sh"
  chmod a+x /tmp/artn.database.sh
  write_green "Executing> bash /tmp/artn.database.sh"
  bash /tmp/artn.database.sh
  write_green "Executing> rm -f /tmp/artn.database.sh"
  rm -f /tmp/artn.database.sh
fi


# +
# exit
# -
exit 0
