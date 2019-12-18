#!/bin/sh


# +
#
# Name:        artn.verify.upload.sh
# Description: Verifies File Upload
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash artn.verify.upload.sh --help
#
# -


# +
# default(s)
# -
def_orp_source="${PWD}"

dry_run=0
stand_alone=0
verbose=0


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
  write_blue   ""                                                                                              2>&1
  write_blue   "ARTN Verify Upload Control"                                                                    2>&1
  write_blue   ""                                                                                              2>&1
  write_green  "Use:"                                                                                          2>&1
  write_green  "  %% bash $0 --source=<str> [--dry-run] [--stand-alone]"                                       2>&1
  write_yellow ""                                                                                              2>&1
  write_yellow "Input(s):"                                                                                     2>&1
  write_yellow "  --source=<str>,   where <str> is source code directory,          default=${def_orp_source}"  2>&1
  write_yellow ""                                                                                              2>&1
  write_cyan   "Flag(s):"                                                                                      2>&1
  write_cyan   " --dry-run,         show (but do not execute) commands,            default=false"              2>&1
  write_cyan   " --stand-alone,     use standalone code,                           default=false"              2>&1
  write_cyan   " --verbose,         produce more verbose output,                   default=false"              2>&1
  write_cyan   ""                                                                                              2>&1
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
    --stand-alone|--STAND-ALONE)
      stand_alone=1
      shift
      ;;
    --verbose|--VERBOSE)
      verbose=1
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
write_blue "%% source ${orp_source}/etc/ARTN.sh ${orp_source}"
source ${orp_source}/etc/ARTN.sh ${orp_source}
write_blue "%% source ${orp_source}/etc/ORP.sh  ${orp_source}"
source ${orp_source}/etc/ORP.sh  ${orp_source}


# +
# execute (dry-run)
# -
write_blue "%% bash $0 --source=${orp_source} --dry-run=${dry_run} --stand-alone=${stand_alone} --verbose=${verbose}"
if [[ ${dry_run} -eq 1 ]]; then
  for _f in `ls ${orp_source}/instance/files/*.csv`; do
    if [[ ${stand_alone} -eq 1 ]]; then
      if [[ ${verbose} -eq 1 ]]; then
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json --verbose"
      else
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json"
      fi
    else
      if [[ ${verbose} -eq 1 ]]; then
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json --verbose"
      else
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json"
      fi
    fi
  done
  for _f in `ls ${orp_source}/instance/files/*.tsv`; do
    if [[ ${stand_alone} -eq 1 ]]; then
      if [[ ${verbose} -eq 1 ]]; then
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json --verbose"
      else
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json"
      fi
    else
      if [[ ${verbose} -eq 1 ]]; then
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json --verbose"
      else
        write_yellow "Dry-Run> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json"
      fi
    fi
  done

else
  for _f in `ls ${orp_source}/instance/files/*.csv`; do
    if [[ ${stand_alone} -eq 1 ]]; then
      if [[ ${verbose} -eq 1 ]]; then
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json --verbose"
        python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json --verbose
      else
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json"
        python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json
      fi
    else
      if [[ ${verbose} -eq 1 ]]; then
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json --verbose"
        python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json --verbose
      else
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json"
        python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json
      fi
    fi
  done
  for _f in `ls ${orp_source}/instance/files/*.tsv`; do
    if [[ ${stand_alone} -eq 1 ]]; then
      if [[ ${verbose} -eq 1 ]]; then
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json --verbose"
        python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json --verbose
      else
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json"
        python3 ${orp_source}/utils/check_upload_format_standalone.py --file=${_f} --json
      fi
    else
      if [[ ${verbose} -eq 1 ]]; then
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json --verbose"
        python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json --verbose
      else
        write_green "Executing> python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json"
        python3 ${orp_source}/utils/check_upload_format.py --file=${_f} --json
      fi
    fi
  done
fi


# +
# exit
# -
exit 0
