#!/bin/sh


# +
#
# Name:        artn.users.sh
# Description: ARTN User(s) Control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190415
# Execute:     % bash artn.users.sh --help
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
# account(s) - edit as required
# -
_admin=artn:secretsanta
_demo1=Demo1:FooBar1
_demo2=Demo2:FooBar2
_demo3=Demo3:FooBar3
_demo4=Demo4:FooBar4
_demo5=Demo5:FooBar5


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
  write_blue   "ARTN User(s) Control"                                                                             2>&1
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
PSQL_CMD="PGPASSWORD=\"${artn_db_pass}\" psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name}"
if [[ -f /tmp/artn.users.sh ]]; then
  rm -f /tmp/artn.users.sh
fi


# +
# create table
# -
echo "Creating /tmp/artn.users.sh"
echo "#!/bin/sh"                                                                                                                                  >> /tmp/artn.users.sh 2>&1
echo ""                                                                                                                                           >> /tmp/artn.users.sh 2>&1
echo "${PSQL_CMD} << END_TABLE"                                                                                                                   >> /tmp/artn.users.sh 2>&1
echo "DROP TABLE IF EXISTS obsreqs;"                                                                                                              >> /tmp/artn.users.sh 2>&1
echo "DROP TABLE IF EXISTS users;"                                                                                                                >> /tmp/artn.users.sh 2>&1
echo "CREATE TABLE users ("                                                                                                                       >> /tmp/artn.users.sh 2>&1
echo "  id SERIAL PRIMARY KEY,"                                                                                                                   >> /tmp/artn.users.sh 2>&1
echo "  firstname VARCHAR(64) NOT NULL,"                                                                                                          >> /tmp/artn.users.sh 2>&1
echo "  lastname VARCHAR(64) NOT NULL,"                                                                                                           >> /tmp/artn.users.sh 2>&1
echo "  username VARCHAR(64) NOT NULL UNIQUE,"                                                                                                    >> /tmp/artn.users.sh 2>&1
echo "  hashword VARCHAR(128) NOT NULL,"                                                                                                          >> /tmp/artn.users.sh 2>&1
echo "  passphrase VARCHAR(128) NOT NULL,"                                                                                                        >> /tmp/artn.users.sh 2>&1
echo "  email VARCHAR(128) NOT NULL UNIQUE,"                                                                                                      >> /tmp/artn.users.sh 2>&1
echo "  affiliation VARCHAR(256) NOT NULL,"                                                                                                       >> /tmp/artn.users.sh 2>&1
echo "  created_iso TIMESTAMP NOT NULL DEFAULT CURRENT_DATE,"                                                                                     >> /tmp/artn.users.sh 2>&1
echo "  created_mjd double precision NOT NULL,"                                                                                                   >> /tmp/artn.users.sh 2>&1
echo "  avatar VARCHAR(128),"                                                                                                                     >> /tmp/artn.users.sh 2>&1
echo "  about_me VARCHAR(256),"                                                                                                                   >> /tmp/artn.users.sh 2>&1
echo "  last_seen_iso TIMESTAMP NOT NULL DEFAULT CURRENT_DATE,"                                                                                   >> /tmp/artn.users.sh 2>&1
echo "  last_seen_mjd double precision NOT NULL,"                                                                                                 >> /tmp/artn.users.sh 2>&1
echo "  is_admin BOOLEAN NOT NULL DEFAULT FALSE,"                                                                                                 >> /tmp/artn.users.sh 2>&1
echo "  is_disabled BOOLEAN NOT NULL DEFAULT FALSE);"                                                                                             >> /tmp/artn.users.sh 2>&1
echo "END_TABLE"                                                                                                                                  >> /tmp/artn.users.sh 2>&1
echo ""                                                                                                                                           >> /tmp/artn.users.sh 2>&1

# +
# create user(s)
# -
echo "${PSQL_CMD} << END_USER"                                                                                                                    >> /tmp/artn.users.sh 2>&1
echo "INSERT INTO users (firstname, lastname, username, hashword, passphrase, email, affiliation, created_iso, created_mjd,"                      >> /tmp/artn.users.sh 2>&1
echo "avatar, about_me, last_seen_iso, last_seen_mjd, is_admin, is_disabled) VALUES"                                                              >> /tmp/artn.users.sh 2>&1
echo "Adding admin ${_admin}"
_user=$(echo ${_admin} | cut -d':' -f1)
_pass=$(echo ${_admin} | cut -d':' -f2)
_epass=$(echo -e "from werkzeug.security import generate_password_hash;print(generate_password_hash('${_pass}'))" | python3)
_epass=${_epass//$/\\\$}
echo "('ARTN', 'Operator', '${_user}', '${_epass}', 'Artn Lorem Ipsum', 'artn@dev.null', 'None', '1970-01-01 00:00:00.000000', 40587.0,"          >> /tmp/artn.users.sh 2>&1
echo "'https://www.gravatar.com/avatar/5f25240e1dcb880a3aa408ceb24250e8', 'ARTN account', '1970-01-01 00:00:00.000000', 40587.0, TRUE, FALSE),"   >> /tmp/artn.users.sh 2>&1

echo "Adding user ${_demo1}"
_user=$(echo ${_demo1} | cut -d':' -f1)
_pass=$(echo ${_demo1} | cut -d':' -f2)
_epass=$(echo -e "from werkzeug.security import generate_password_hash;print(generate_password_hash('${_pass}'))" | python3)
_epass=${_epass//$/\\\$}
echo "('Demo1', 'Account', '${_user}', '${_epass}', 'Demo1 Lorem Ipsum', 'demo1@dev.null', 'None', '1970-01-01 00:00:00.000000', 40587.0,"        >> /tmp/artn.users.sh 2>&1
echo "'https://www.gravatar.com/avatar/d82afc65bd5cd6066ca4ab9ccfd68fd5', 'Demo1 account', '1970-01-01 00:00:00.000000', 40587.0, FALSE, FALSE)," >> /tmp/artn.users.sh 2>&1

echo "Adding user ${_demo2}"
_user=$(echo ${_demo2} | cut -d':' -f1)
_pass=$(echo ${_demo2} | cut -d':' -f2)
_epass=$(echo -e "from werkzeug.security import generate_password_hash;print(generate_password_hash('${_pass}'))" | python3)
_epass=${_epass//$/\\\$}
echo "('Demo2', 'Account', '${_user}', 'p${_epass}', 'Demo2 Lorem Ipsum', 'demo2@dev.null', 'None', '1970-01-01 00:00:00.000000', 40587.0,"       >> /tmp/artn.users.sh 2>&1
echo "'https://www.gravatar.com/avatar/6f9f213ce542b6376e16b5849bce2620', 'Demo2 account', '1970-01-01 00:00:00.000000', 40587.0, FALSE, FALSE)," >> /tmp/artn.users.sh 2>&1

echo "Adding user ${_demo3}"
_user=$(echo ${_demo3} | cut -d':' -f1)
_pass=$(echo ${_demo3} | cut -d':' -f2)
_epass=$(echo -e "from werkzeug.security import generate_password_hash;print(generate_password_hash('${_pass}'))" | python3)
_epass=${_epass//$/\\\$}
echo "('Demo3', 'Account', '${_user}', 'p${_epass}', 'Demo3 Lorem Ipsum', 'demo3@dev.null', 'None', '1970-01-01 00:00:00.000000', 40587.0,"       >> /tmp/artn.users.sh 2>&1
echo "'https://www.gravatar.com/avatar/c645d64298ae882d6cfc4e6b07ba0762', 'Demo3 account', '1970-01-01 00:00:00.000000', 40587.0, FALSE, FALSE)," >> /tmp/artn.users.sh 2>&1

echo "Adding user ${_demo4}"
_user=$(echo ${_demo4} | cut -d':' -f1)
_pass=$(echo ${_demo4} | cut -d':' -f2)
_epass=$(echo -e "from werkzeug.security import generate_password_hash;print(generate_password_hash('${_pass}'))" | python3)
_epass=${_epass//$/\\\$}
echo "('Demo4', 'Account', '${_user}', 'p${_epass}', 'Demo4 Lorem Ipsum', 'demo4@dev.null', 'None', '1970-01-01 00:00:00.000000', 40587.0,"       >> /tmp/artn.users.sh 2>&1
echo "'https://www.gravatar.com/avatar/68b258d2252992220a09354d78a46657', 'Demo4 account', '1970-01-01 00:00:00.000000', 40587.0, FALSE, FALSE)," >> /tmp/artn.users.sh 2>&1

echo "Adding user ${_demo5}"
_user=$(echo ${_demo5} | cut -d':' -f1)
_pass=$(echo ${_demo5} | cut -d':' -f2)
_epass=$(echo -e "from werkzeug.security import generate_password_hash;print(generate_password_hash('${_pass}'))" | python3)
_epass=${_epass//$/\\\$}
echo "('Demo5', 'Account', '${_user}', 'p${_epass}', 'Demo5 Lorem Ipsum', 'demo5@dev.null', 'None', '1970-01-01 00:00:00.000000', 40587.0,"       >> /tmp/artn.users.sh 2>&1
echo "'https://www.gravatar.com/avatar/f71718639739510c892109eb19b161fe', 'Demo5 account', '1970-01-01 00:00:00.000000', 40587.0, FALSE, FALSE);" >> /tmp/artn.users.sh 2>&1
echo "END_USER"                                                                                                                                   >> /tmp/artn.users.sh 2>&1


# +
# execute
# -
write_blue "%% bash $0 --database=${artn_db_name} --hostname=${artn_db_host} --password=${artn_db_pass} --username=${artn_db_user} --dry-run=${dry_run}"
if [[ ${dry_run} -eq 1 ]]; then
  if [[ "${USER}" != "root" ]]; then
    write_red "WARNING: you need to be root to execute these commands!"
  fi
  if [[ ! -f /tmp/artn.users.sh ]]; then
    write_red "WARNING: /tmp/artn.users.sh does not exist!"
  fi
  write_yellow "Dry-Run> chmod a+x /tmp/artn.users.sh"
  write_yellow "Dry-Run> bash /tmp/artn.users.sh"
  write_yellow "Dry-Run> rm -f /tmp/artn.users.sh"
  write_yellow "Dry-Run> PGPASSWORD='${artn_db_pass}' psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name} -c 'SELECT * FROM users;'"

else
  if [[ "${USER}" != "root" ]]; then
    write_red "ERROR: you need to be root to execute these commands!"
    usage
    exit
  fi
  if [[ ! -f /tmp/artn.users.sh ]]; then
    write_red "ERROR: /tmp/artn.users.sh does not exist!"
    usage
    exit
  fi
  write_green "Executing> chmod a+x /tmp/artn.users.sh"
  chmod a+x /tmp/artn.users.sh
  write_green "Executing> bash /tmp/artn.users.sh"
  bash /tmp/artn.users.sh
  write_green "Executing> rm -f /tmp/artn.users.sh"
  rm -f /tmp/artn.users.sh
  write_green "Executing> PGPASSWORD='${artn_db_pass}' psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name} -c 'SELECT * FROM users;'"
  PGPASSWORD="${artn_db_pass}" psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name} -c "SELECT * FROM users;"
fi


# +
# exit
# -
exit 0
