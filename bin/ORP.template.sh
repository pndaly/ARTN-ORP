#!/bin/sh


# +
#
# Name:        ORP.sh
# Description: ORP control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash ORP.sh --help
#
# -


# +
# default(s) - edit as required
# -
def_orp_command="status"
def_orp_source="${ORP_HOME}"
def_orp_type="dev"

def_dev_host="localhost"
def_dev_port=5000
def_prd_host="localhost"
def_prd_port=7500

dry_run=0


# +
# variable(s)
# -
orp_command="${def_orp_command}"
orp_source="${def_orp_source}"
orp_type="${def_orp_type}"

orp_port=${def_dev_port}
orp_host="${def_dev_host}"


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
  write_blue   ""                                                                                              2>&1
  write_blue   "ORP Control"                                                                                   2>&1
  write_blue   ""                                                                                              2>&1
  write_green  "Use:"                                                                                          2>&1
  write_green  "  %% bash $0 --command=<str> --source=<str> --type=<str> [--dry-run]"                          2>&1
  write_yellow ""                                                                                              2>&1
  write_yellow "Input(s):"                                                                                     2>&1
  write_yellow "  --command=<str>,  where <str> is { 'start', 'status', 'stop' },  default=${def_orp_command}" 2>&1
  write_yellow "  --source=<str>,   where <str> is source code directory,          default=${def_orp_source}"  2>&1
  write_yellow ""                                                                                              2>&1
  write_cyan   "Flag(s):"                                                                                      2>&1
  write_cyan   " --dry-run,         show (but do not execute) commands,            default=false"              2>&1
  write_cyan   ""                                                                                              2>&1
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --command*|--COMMAND*)
      orp_command=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    --source*|--SOURCE*)
      orp_source=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --type*|--TYPE*)
      orp_type=$(echo $1 | cut -d'=' -f2)
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
case $(echo ${orp_command} | tr '[A-Z]' '[a-z]') in
  start*|status*|stop*)
    ;;
  *)
    orp_command=${def_orp_command}
    ;;
esac


if [[ ! -d ${orp_source} ]]; then
  write_red "<ERROR> directory (${orp_source}) is unknown ... exiting"
  exit 0 
fi


case $(echo ${orp_type} | tr '[A-Z]' '[a-z]') in
  prod*)
    orp_type="production"
    orp_host=$(getent hosts ${def_prd_host} | cut -d' ' -f1)
    orp_port=${def_prd_port}
    ;;
  *)
    orp_type="development"
    orp_host="${def_dev_host}"
    orp_port=${def_dev_port}
    ;;
esac


if ! ping -c 1 -w 5 ${orp_host} &>/dev/null; then 
  write_red "<ERROR> server (${orp_host}) is down ... exiting"
  exit 0 
fi


# +
# env(s)
# -
if [[ -z "${PYTHONPATH}" ]]; then
  export PYTHONPATH=`pwd`
fi
write_blue "%% source ${orp_source}/etc/ARTN.sh ${orp_source}"
source ${orp_source}/etc/ARTN.sh ${orp_source}
write_blue "%% source ${orp_source}/etc/ORP.sh  ${orp_source} ${orp_host} ${orp_port}"
source ${orp_source}/etc/ORP.sh  ${orp_source} ${orp_host} ${orp_port}


# +
# execute (dry-run)
# -
write_blue "%% bash $0 --command=${orp_command} --dry-run=${dry_run} --source=${orp_source} --type=${orp_type}"
case $(echo ${orp_command} | tr '[A-Z]' '[a-z]') in
  start*)
    if [[ ${dry_run} -eq 1 ]]; then
      if [[ "${orp_type}" == "development" ]]; then
        write_yellow "Dry-Run> FLASK_DEBUG=True  FLASK_ENV=Development FLASK_APP=${orp_source}/source/orp.py flask run"
      elif [[ "${orp_type}" == "production" ]]; then
        write_yellow "Dry-Run> FLASK_DEBUG=False FLASK_ENV=Production  FLASK_APP=${orp_source}/source/orp.py flask run -h ${orp_host} -p ${orp_port}"
      fi
    else
      if [[ "${orp_type}" == "development" ]]; then
        write_green "Executing> FLASK_DEBUG=True  FLASK_ENV=Development FLASK_APP=${orp_source}/source/orp.py flask run"
        FLASK_DEBUG=True  FLASK_ENV=Development FLASK_APP=${orp_source}/source/orp.py flask run
      elif [[ "${orp_type}" == "production" ]]; then
        write_green "Executing> FLASK_DEBUG=False FLASK_ENV=Production  FLASK_APP=${orp_source}/source/orp.py flask run -h ${orp_host} -p ${orp_port}"
        FLASK_DEBUG=False FLASK_ENV=Production  FLASK_APP=${orp_source}/source/orp.py flask run -h ${orp_host} -p ${orp_port}
      fi
    fi
    ;;

  stop*)
    _pid=$(ps -ef | pgrep -f 'python' | pgrep  -f flask)
    if [[ ! -z "${_pid}" ]]; then
      if [[ ${dry_run} -eq 1 ]]; then
        write_yellow "Dry-Run> kill -9 ${_pid}"
      else
        write_green "Executing> kill -9 ${_pid}"
        kill -9 ${_pid}
      fi
    fi
    ;;

  status*)
      if [[ ${dry_run} -eq 1 ]]; then
        write_yellow "Dry-Run> ps -ef | grep -i python | grep -i flask"
      else
        write_green "Executing> ps -ef | grep -i python | grep -i flask"
        ps -ef | grep -i python | grep -i flask
      fi
    ;;
esac


# +
# exit
# -
exit 0
