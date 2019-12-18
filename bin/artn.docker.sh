#!/bin/sh


# +
#
# Name:        artn.docker.sh
# Description: ARTN Docker Control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20191202
# Execute:     % bash artn.docker.sh --help
#
# -


# +
# default(s)
# -
def_command="status"

dry_run=0


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
  write_blue   ""                                                                                                                                 2>&1
  write_blue   "ARTN Docker Control"                                                                                                              2>&1
  write_blue   ""                                                                                                                                 2>&1
  write_green  "Use:"                                                                                                                             2>&1
  write_green  "  %% bash $0 --command=<str> [--dry-run]"                                                                                         2>&1
  write_yellow ""                                                                                                                                 2>&1
  write_yellow "Input(s):"                                                                                                                        2>&1
  write_yellow "  --command=<str>,   -c=<str>  command where <str> is { build | connect | run | start | status | stop },  default=${def_command}" 2>&1
  write_yellow ""                                                                                                                                 2>&1
  write_cyan   "Flag(s):"                                                                                                                         2>&1
  write_cyan   "  --dry-run,         -d        show (but do not execute) command(s),                                      default=false"          2>&1
  write_cyan   ""                                                                                                                                 2>&1
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --command*|--COMMAND*)
      docker_command=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run|--DRY-RUN)
      dry_run=1
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
case $(echo ${docker_command} | tr '[A-Z]' '[a-z]') in
  build*|connect*|run*|start*|status*|stop*)
    ;;
  *)
    usage
    exit 0
    ;;
esac


# +
# variable(s)
# -
_container=$(docker container ps -a | grep -i postgres | cut -d' ' -f1)
_is_running=$(docker ps | grep ${_container})


# +
# execute (dry-run)
# -
write_blue "%% bash $0 --command=${docker_command} --dry-run=${dry_run}"
case $(echo ${docker_command} | tr '[A-Z]' '[a-z]') in

  # build a new image from Dockerfile
  build*)
    if [[ ${dry_run} -eq 1 ]]; then
      write_yellow "Dry-Run>> docker build contained-postgres -f /home/artn-eng/git-clones/postgres/11/alpine/Dockerfile"
    else
      write_green "Executing>> docker build contained-postgres -f /home/artn-eng/git-clones/postgres/11/alpine/Dockerfile"
      docker build contained-postgres -f /home/artn-eng/git-clones/postgres/11/alpine/Dockerfile
    fi
    ;;

  # connect to a running container
  connect*)
    if [[ ${dry_run} -eq 1 ]]; then
      write_yellow "Dry-Run>> docker exec -it ${_container} /bin/bash"
    else
      if [[ "${_is_running}" != "" ]]; then
        write_green "Executing>> docker exec -it ${_container} /bin/bash"
        docker exec -it ${_container} /bin/bash
      else
        write_red "ERROR>> no valid container found"
      fi
    fi
    ;;

  # create container from image and run it
  run*)
    if [[ ${dry_run} -eq 1 ]]; then
      if [[ "${_is_running}" != "" ]]; then
        write_yellow "Dry-Run>> docker stop ${_container}"
      fi
      write_yellow "Dry-Run>> docker run -d --network host -v /home/artn-eng/docker-volumes/orp/:/db -p 5432:5432 contained-postgres"
    else
      if [[ "${_is_running}" != "" ]]; then
        write_green "Executing>> docker stop ${_container}"
        docker stop ${_container}
      fi
      write_green "Executing>> docker run -d --network host -v /home/artn-eng/docker-volumes/orp/:/db -p 5432:5432 contained-postgres"
      docker run -d --network host -v /home/artn-eng/docker-volumes/orp/:/db -p 5432:5432 contained-postgres
    fi
    ;;

  # start a (previously) stopped container
  start*)
    if [[ ${dry_run} -eq 1 ]]; then
      if [[ "${_is_running}" != "" ]]; then
        write_yellow "Dry-Run>> docker stop ${_container}"
      fi
      write_yellow "Dry-Run>> docker start ${_container}"
    else
      if [[ "${_is_running}" != "" ]]; then
        write_green "Executing>> docker stop ${_container}"
        docker stop ${_container}
      fi
      write_green "Executing>> docker start ${_container}"
      docker start ${_container}
    fi
    ;;

  # show if container is running
  status*)
    if [[ ${dry_run} -eq 1 ]]; then
      write_yellow "Dry-Run>> docker container ps -a | grep -i postgres"
    else
      if [[ "${_is_running}" != "" ]]; then
        write_green "Executing>> docker container ps -a | grep -i postgres"
        docker container ps -a | grep -i postgres
      else
        write_red "ERROR>> no valid container found"
      fi
    fi
    ;;

  # stop a running container
  stop*)
    if [[ ${dry_run} -eq 1 ]]; then
      write_yellow "Dry-Run>> docker stop ${_container}"
    else
      if [[ "${_is_running}" != "" ]]; then
        write_green "Executing>> docker stop ${_container}"
        docker stop ${_container}
      else
        write_red "ERROR>> no valid container found"
      fi
    fi
    ;;
esac


# +
# exit
# -
exit 0
