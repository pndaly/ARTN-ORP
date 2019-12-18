#!/bin/sh


# +
#
# Name:        artn.cli.upload.sh
# Description: upload a file to ORP from command line
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190915
# Execute:     % bash artn.cli.upload.sh --help
#
# -


# +
# set defaults: edit as you see fit
# -
def_auth="${HOME}/.scopenet"
def_file="${HOME}/non_sidereal.tsv"

dry_run=0
verbose=0


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
  write_blue   ""                                                                               2>&1
  write_blue   "Upload file to ORP from command line"                                           2>&1
  write_blue   ""                                                                               2>&1
  write_green  "Use:"                                                                           2>&1
  write_green  " %% bash $0 --auth=<path> --file=<path> [--dry-run] [--verbose]"                2>&1
  write_yellow ""                                                                               2>&1
  write_yellow "Input(s):"                                                                      2>&1
  write_yellow "  --auth=<path>,  where <path> is the authorization file,  default=${def_auth}" 2>&1
  write_yellow "  --file=<path>,  where <path> is the upload file,         default=${def_file}" 2>&1
  write_yellow ""                                                                               2>&1
  write_cyan   "Flag(s):"                                                                       2>&1
  write_cyan   "  --dry-run,      show commands,                           default=false"       2>&1
  write_cyan   "  --verbose,      show more output,                        default=false"       2>&1
  write_cyan   ""                                                                               2>&1
}


# +
# get command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --auth*|--AUTH*)
      rs_auth=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --file*|--FILE*)
      rs_file=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
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
# check and/or reset input(s)
# -
if [[ -z ${rs_auth} ]]; then
  rs_auth=${def_auth}
fi
rs_auth="${rs_auth/#\~/$HOME}"
if [[ ! -f "${rs_auth}" ]]; then
  write_red "<ERROR> invalid file (${rs_auth}) ... exiting"
  exit 0 
fi

if [[ -z ${rs_file} ]]; then
  rs_file=${def_file}
fi
rs_file="${rs_file/#\~/$HOME}"
if [[ ! -f "${rs_file}" ]]; then
  write_red "<ERROR> invalid file (${rs_file}) ... exiting"
  exit 0 
fi

_user=$(cat ${rs_auth} | cut -d' ' -f4)


# +
# execute (dry-run)
# -
write_blue "%% bash $0 --auth=${rs_auth} --file=${rs_file} --dry-run=${dry_run} --verbose=${verbose} [_user=${_user}]"
if [[ ${dry_run} -eq 1 ]]; then
  write_yellow "Dry-Run>> rm -f ~/.scopenet.cookie >> /dev/null 2>&1"
  if [[ ${verbose} -eq 1 ]]; then
    write_yellow "Dry-Run>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} -v https://scopenet.as.arizona.edu/orp/login"
    write_yellow "Dry-Run>> curl -L -i -b ~/.scopenet.cookie -v -X POST -F file='@${rs_file}' https://scopenet.as.arizona.edu/orp/cli_upload/${_user}"
    write_yellow "Dry-Run>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} -v https://scopenet.as.arizona.edu/orp/logout"
  else
    write_yellow "Dry-Run>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} https://scopenet.as.arizona.edu/orp/login"
    write_yellow "Dry-Run>> curl -L -i -b ~/.scopenet.cookie -X POST -F file='@${rs_file}' https://scopenet.as.arizona.edu/orp/cli_upload/${_user}"
    write_yellow "Dry-Run>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} https://scopenet.as.arizona.edu/orp/logout"
  fi

# +
# execute (for-real)
# -
else
  write_green "Executing>> rm -f ~/.scopenet.cookie >> /dev/null 2>&1"
  rm -f ~/.scopenet.cookie >> /dev/null 2>&1
  if [[ ${verbose} -eq 1 ]]; then
    write_green "Executing>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} -v https://scopenet.as.arizona.edu/orp/login"
    curl -i -c ~/.scopenet.cookie -n ${rs_auth} -v https://scopenet.as.arizona.edu/orp/login
    write_green "Executing>> curl -L -i -b ~/.scopenet.cookie -v -X POST -F file='@${rs_file}' https://scopenet.as.arizona.edu/orp/cli_upload/${_user}"
    curl -L -i -b ~/.scopenet.cookie -v -X POST -F file="@${rs_file}" https://scopenet.as.arizona.edu/orp/cli_upload/${_user}
    write_green "Executing>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} -v https://scopenet.as.arizona.edu/orp/logout"
    curl -i -c ~/.scopenet.cookie -n ${rs_auth} -v https://scopenet.as.arizona.edu/orp/logout
  else
    write_green "Executing>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} https://scopenet.as.arizona.edu/orp/login"
    curl -i -c ~/.scopenet.cookie -n ${rs_auth} https://scopenet.as.arizona.edu/orp/login
    write_green "Executing>> curl -L -i -b ~/.scopenet.cookie -X POST -F file='@${rs_file}' https://scopenet.as.arizona.edu/orp/cli_upload/${_user}"
    curl -L -i -b ~/.scopenet.cookie -X POST -F file="@${rs_file}" https://scopenet.as.arizona.edu/orp/cli_upload/${_user}
    write_green "Executing>> curl -i -c ~/.scopenet.cookie -n ${rs_auth} https://scopenet.as.arizona.edu/orp/logout"
    curl -i -c ~/.scopenet.cookie -n ${rs_auth} https://scopenet.as.arizona.edu/orp/logout
  fi

fi


# +
# exit
# -
exit 0
