#!/bin/sh


# +
#
# Name:        iers.update.sh
# Description: IERS File Update
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20200207
# Execute:     % bash iers.update.sh --help
# Cron Entry:  0 8 * * 0 (cd $ARTN_HOME; bash $ARTN_CRON/iers.update.sh)
# -


# +
# default(s)
# -
def_orp_source="${PWD}"
dry_run=0


# +
# variable(s)
# -
orp_source="${def_orp_source}"


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
  write_blue   ""                                                                                   2>&1
  write_blue   "IERS File Update"                                                                   2>&1
  write_blue   ""                                                                                   2>&1
  write_green  "Use:"                                                                               2>&1
  write_green  "  %% bash $0 --source=<str> [--dry-run]"                                            2>&1
  write_yellow ""                                                                                   2>&1
  write_yellow "Input(s):"                                                                          2>&1
  write_yellow "  --source=<path>,  where <path> is source code path,    default=${def_orp_source}" 2>&1
  write_yellow ""                                                                                   2>&1
  write_cyan   "Flag(s):"                                                                           2>&1
  write_cyan   " --dry-run,         show (but do not execute) commands,  default=false"             2>&1
  write_cyan   ""                                                                                   2>&1
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    --source*|--SOURCE*)
      orp_source=$(echo $1 | cut -d'=' -f2)
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
if [[ ! -d ${orp_source} ]]; then
  write_red "<ERROR> directory (${orp_source}) is unknown ... exiting"
  exit 0 
fi


# +
# env(s)
# -
if [[ -z "${PYTHONPATH}" ]]; then
  export PYTHONPATH=`pwd`
fi


# +
# execute (dry-run)
# -
write_blue "%% bash $0 --source=${orp_source} --dry-run=${dry_run}"
if [[ ${dry_run} -eq 1 ]]; then
  write_yellow "Dry-Run>> source ${orp_source}/etc/ARTN.sh ${orp_source}"
  write_yellow "Dry-Run>> source ${orp_source}/etc/ORP.sh  ${orp_source}"
  write_yellow 'Dry-Run>> echo -e "from src import *; get_iers()" | python3'


# +
# execute (for-real)
# -
else
  write_green "Executing>> source ${orp_source}/etc/ARTN.sh ${orp_source}"
  source ${orp_source}/etc/ARTN.sh ${orp_source}
  write_green "Executing>> source ${orp_source}/etc/ORP.sh  ${orp_source}"
  source ${orp_source}/etc/ORP.sh  ${orp_source}
  write_green 'Executing>> echo -e "from src import *; get_iers()" | python3'
  echo -e "from src import *; get_iers()" | python3
fi


# +
# exit
# -
exit 0
