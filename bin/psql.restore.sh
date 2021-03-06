#!/bin/sh


# +
#
# Name:        psql.restore.sh
# Description: restore a PostGresQL database
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20181205
# Execute:     % bash psql.restore.sh --help
#
# -


# +
# set defaults: edit as you see fit
# -
today=$(date "+%Y%m%d")
default_authorization="artn:********"
default_database="artn"
default_directory="${PWD}"
default_filename="psql.${default_database}.${today}.sql"
default_filename_compressed="psql.${default_database}.${today}.db"
default_server="localhost"
default_port=5432

dry_run=0
compressed=0


# +
# env(s)
# -
export PATH=/usr/lib/postgresql/10/bin:${PATH}
export PATH=/usr/lib/postgresql/11/bin:${PATH}


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
  write_blue   ""                                                                                                                                     2>&1
  write_blue   "Restore a PostGreSQL database"                                                                                                        2>&1
  write_blue   ""                                                                                                                                     2>&1
  write_green  "Use:"                                                                                                                                 2>&1
  write_green  " %% bash $0 --authorization=<str> --database=<str> --directory=<path> --filename=<str> --server=<address> [--compressed] [--dry-run]" 2>&1
  write_yellow ""                                                                                                                                     2>&1
  write_yellow "Input(s):"                                                                                                                            2>&1
  write_yellow "  --authorization=<str>, where <str> is of the form 'username:password',  default=${default_authorization}"                           2>&1
  write_yellow "  --database=<str>,      where <str> is a database name,                  default=${default_database}"                                2>&1
  write_yellow "  --directory=<path>,    where <path> is a directory name,                default=${default_directory}"                               2>&1
  write_yellow "  --filename=<str>,      where <str> is a database backup file name,      default=${default_filename}"                                2>&1
  write_yellow "  --port=<int>,          where <int> is a port number,                    default=${default_port}"                                    2>&1
  write_yellow "  --server=<address>,    where <address> is a hostname or IP-address,     default=${default_server}"                                  2>&1
  write_yellow ""                                                                                                                                     2>&1
  write_cyan   "Flag(s):"                                                                                                                             2>&1
  write_cyan   "  --compressed,          use compressed backup format,                    default=false"                                              2>&1
  write_cyan   "  --dry-run,             show (but do not execute) commands,              default=false"                                              2>&1
  write_cyan   ""                                                                                                                                     2>&1
  echo         "Output(s):"                                                                                                                           2>&1
  echo         "  --compressed=0: database restored from ${default_directory}/${default_filename}"                                                    2>&1
  echo         "  --compressed=1: database restored from ${default_directory}/${default_filename_compressed}"                                         2>&1
  echo         ""                                                                                                                                     2>&1
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --authorization*|--AUTHORIZATION*)
      rs_authorization=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --compressed|--COMPRESSED)
      compressed=1
      shift
      ;;
    --database*|--DATABASE*)
      rs_database=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --directory*|--DIRECTORY*)
      rs_directory=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --filename*|--FILENAME*)
      rs_filename=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    --port*|--PORT*)
      rs_port=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --server*|--SERVER*)
      rs_server=$(echo $1 | cut -d'=' -f2)
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
[[ -z ${rs_authorization} ]] && rs_authorization=${default_authorization}
[[ -z ${rs_database} ]] && rs_database=${default_database}
[[ -z ${rs_directory} ]] && rs_directory=${default_directory}
[[ ! -d ${rs_directory} ]] && rs_directory=${PWD}
[[ -z ${rs_port} ]] && rs_port=${default_port}
[[ -z ${rs_server} ]] && rs_server=${default_server}

if [[ -z ${rs_filename} ]]; then
  if [[ ${compressed} -eq 1 ]]; then
    rs_filename="psql.${rs_database}.${today}.db"
  else
    rs_filename="psql.${rs_database}.${today}.sql"
  fi
fi

rs_username=$(echo ${rs_authorization} | cut -d':' -f1)
rs_password=$(echo ${rs_authorization} | cut -d':' -f2)


# +
# check input(s)
# -
if ! ping -c 1 -w 5 ${rs_server} &>/dev/null; then 
  write_red "<ERROR> server (${rs_server}) is down ... exiting"
  exit 0 
fi

if [[ -z "${rs_filename}" ]]; then
  write_red "<ERROR> invalid filename (${rs_filename}) ... exiting"
  exit 0 
fi

if [[ ! -f "${rs_directory}/${rs_filename}" ]]; then
  write_red "<ERROR> filename (${rs_directory}/${rs_filename}) does not exist ... exiting"
  exit 0 
fi

if [[ -z "${rs_password}" ]]; then
  write_red "<ERROR> invalid password (${rs_password}) ... exiting"
  exit 0 
fi

if [[ -z "${rs_username}" ]]; then
  write_red "<ERROR> invalid username (${rs_username}) ... exiting"
  exit 0 
fi


# +
# execute (dry-run)
# -
write_blue "%% bash $0 --authorization=${rs_username}:${rs_password} --database=${rs_database} --directory=${rs_directory} --filename=${rs_filename} --port=${rs_port} --server=${rs_server} --compressed=${compressed} --dry-run=${dry_run}"
if [[ ${dry_run} -eq 1 ]]; then
  if [[ ${compressed} -eq 1 ]]; then
    write_yellow "Dry-Run>> PGPASSWORD=${rs_password} pg_restore -h ${rs_server} -p ${rs_port} -U ${rs_username} -d ${rs_database} ${rs_directory}/${rs_filename} 2>&1 >> /dev/null"
  else
    write_yellow "Dry-Run>> PGPASSWORD=${rs_password} PGOPTIONS='--client-min-messages=warning' psql -X -q -1 -v ON_ERROR_STOP=1 --pset pager=off -h ${rs_server} -p ${rs_port} -U ${rs_username} -d ${rs_database} < ${rs_directory}/${rs_filename} 2>&1 >> /dev/null"
  fi
  write_yellow "Database backup restored from ${rs_directpry}/${rs_filename}"


# +
# execute (for-real)
# -
else
  if [[ ${compressed} -eq 1 ]]; then
    write_yellow "Dry-Run>> PGPASSWORD=${rs_password} pg_restore -h ${rs_server} -p ${rs_port} -U ${rs_username} -d ${rs_database} ${rs_directpry}/${rs_filename} 2>&1 >> /dev/null"
    PGPASSWORD=${rs_password} pg_restore -h ${rs_server} -p ${rs_port} -U ${rs_username} -d ${rs_database} ${rs_directpry}/${rs_filename} 2>&1 >> /dev/null
  else
  write_yellow "Executing>> PGPASSWORD=${rs_password} PGOPTIONS='--client-min-messages=warning' psql -X -q -1 -v ON_ERROR_STOP=1 --pset pager=off -h ${rs_server} -p ${rs_port} -U ${rs_username} -d ${rs_database} < ${rs_directory}/${rs_filename} 2>&1 >> /dev/null"
  PGPASSWORD=${rs_password} PGOPTIONS='--client-min-messages=warning' psql -X -q -1 -v ON_ERROR_STOP=1 --pset pager=off -h ${rs_server} -p ${rs_port} -U ${rs_username} -d ${rs_database} < ${rs_directory}/${rs_filename} 2>&1 >> /dev/null
  fi
  if [[ $? == 0 ]]; then
    write_yellow "Database backup restored from ${rs_directory}/${rs_filename}"
  else
    write_red "<ERROR> invalid access to database (${rs_directory}/${rs_database}) on server (${rs_server}:${rs_port}) using authorization (${rs_username}:${rs_password}) ... exiting"
  fi
fi


# +
# exit
# -
exit 0
