#!/bin/sh


# +
#
# Name:        artn.obsreqs.sh
# Description: ARTN Obsreq(s) Control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190415
# Execute:     % bash artn.obsreqs.sh --help
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
  write_blue   "ARTN Obsreq(s) Control"                                                                           2>&1
  write_blue   ""                                                                                                 2>&1
  write_green  "Use:"                                                                                             2>&1
  write_green  "  %% bash $0 --database=<str> --hostname=<str:int> --password=<str> --username=<str> [--dry-run]" 2>&1
  write_cyan   ""                                                                                                 2>&1
  write_yellow "Input(s):"                                                                                        2>&1
  write_yellow "  --database=<str>,      where <str> is the database name,               default=${def_db_name}"  2>&1
  write_yellow "  --hostname=<str:int>,  where <str> is the database hostname and port,  default=${def_db_host}"  2>&1
  write_yellow "  --password=<str>,      where <str> is the database password,           default=${def_db_pass}"  2>&1
  write_yellow "  --username=<str>,      where <str> is the database username,           default=${def_db_user}"  2>&1
  write_cyan   ""                                                                                                 2>&1
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
PSQL_CMD="PGPASSWORD=\"${artn_db_pass}\" psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name} "
if [[ -f /tmp/artn.obsreqs.sh ]]; then
  rm -f /tmp/artn.obsreqs.sh
fi


# +
# create table
# -
echo "Creating /tmp/artn.obsreqs.sh"
echo "#!/bin/sh"                                                                                                                                                   >> /tmp/artn.obsreqs.sh 2>&1
echo ""                                                                                                                                                            >> /tmp/artn.obsreqs.sh 2>&1
echo "${PSQL_CMD} << END_TABLE"                                                                                                                                    >> /tmp/artn.obsreqs.sh 2>&1
echo "DROP TABLE IF EXISTS obsreqs;"                                                                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "CREATE TABLE obsreqs ("                                                                                                                                      >> /tmp/artn.obsreqs.sh 2>&1
echo "  id SERIAL PRIMARY KEY,"                                                                                                                                    >> /tmp/artn.obsreqs.sh 2>&1
echo "  username VARCHAR(64) NOT NULL,"                                                                                                                            >> /tmp/artn.obsreqs.sh 2>&1
echo "  pi VARCHAR(256) NOT NULL,"                                                                                                                                 >> /tmp/artn.obsreqs.sh 2>&1
echo "  created_iso TIMESTAMP NOT NULL DEFAULT CURRENT_DATE,"                                                                                                      >> /tmp/artn.obsreqs.sh 2>&1
echo "  created_mjd double precision NOT NULL,"                                                                                                                    >> /tmp/artn.obsreqs.sh 2>&1
echo "  group_id VARCHAR(128) NOT NULL,"                                                                                                                           >> /tmp/artn.obsreqs.sh 2>&1
echo "  observation_id VARCHAR(128) NOT NULL,"                                                                                                                     >> /tmp/artn.obsreqs.sh 2>&1
echo "  priority VARCHAR(16) NOT NULL DEFAULT 'Routine',"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "  priority_value double precision NOT NULL DEFAULT 0.0,"                                                                                                     >> /tmp/artn.obsreqs.sh 2>&1
echo "  object_name VARCHAR(64) NOT NULL,"                                                                                                                         >> /tmp/artn.obsreqs.sh 2>&1
echo "  ra_hms VARCHAR(16) NOT NULL,"                                                                                                                              >> /tmp/artn.obsreqs.sh 2>&1
echo "  ra_deg double precision NOT NULL,"                                                                                                                         >> /tmp/artn.obsreqs.sh 2>&1
echo "  dec_dms VARCHAR(16) NOT NULL,"                                                                                                                             >> /tmp/artn.obsreqs.sh 2>&1
echo "  dec_deg double precision NOT NULL,"                                                                                                                        >> /tmp/artn.obsreqs.sh 2>&1
echo "  begin_iso TIMESTAMP NOT NULL DEFAULT CURRENT_DATE,"                                                                                                        >> /tmp/artn.obsreqs.sh 2>&1
echo "  begin_mjd double precision NOT NULL,"                                                                                                                      >> /tmp/artn.obsreqs.sh 2>&1
echo "  end_iso TIMESTAMP NOT NULL DEFAULT CURRENT_DATE,"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "  end_mjd double precision NOT NULL,"                                                                                                                        >> /tmp/artn.obsreqs.sh 2>&1
echo "  airmass double precision NOT NULL DEFAULT 1.25,"                                                                                                           >> /tmp/artn.obsreqs.sh 2>&1
echo "  lunarphase VARCHAR(16) NOT NULL DEFAULT 'Dark',"                                                                                                           >> /tmp/artn.obsreqs.sh 2>&1
echo "  moonphase double precision NOT NULL DEFAULT 1.0,"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "  photometric BOOLEAN NOT NULL DEFAULT False,"                                                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "  guiding BOOLEAN NOT NULL DEFAULT False,"                                                                                                                   >> /tmp/artn.obsreqs.sh 2>&1
echo "  non_sidereal BOOLEAN NOT NULL DEFAULT False,"                                                                                                              >> /tmp/artn.obsreqs.sh 2>&1
echo "  filter_name VARCHAR(24) NOT NULL DEFAULT 'V',"                                                                                                             >> /tmp/artn.obsreqs.sh 2>&1
echo "  exp_time double precision NOT NULL DEFAULT 0.0,"                                                                                                           >> /tmp/artn.obsreqs.sh 2>&1
echo "  num_exp INTEGER NOT NULL DEFAULT 1,"                                                                                                                       >> /tmp/artn.obsreqs.sh 2>&1
echo "  binning VARCHAR(16) NOT NULL DEFAULT 'None',"                                                                                                              >> /tmp/artn.obsreqs.sh 2>&1
echo "  dither VARCHAR(16) NOT NULL DEFAULT 'None',"                                                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "  cadence VARCHAR(16) NOT NULL DEFAULT 'Once',"                                                                                                              >> /tmp/artn.obsreqs.sh 2>&1
echo "  telescope VARCHAR(16) NOT NULL DEFAULT 'Kuiper',"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "  instrument VARCHAR(16) NOT NULL DEFAULT 'Mont4k',"                                                                                                         >> /tmp/artn.obsreqs.sh 2>&1
echo "  rts2_doc JSONB NOT NULL DEFAULT '{}',"                                                                                                                     >> /tmp/artn.obsreqs.sh 2>&1
echo "  rts2_id INTEGER NOT NULL DEFAULT -1,"                                                                                                                      >> /tmp/artn.obsreqs.sh 2>&1
echo "  queued BOOLEAN NOT NULL DEFAULT False,"                                                                                                                    >> /tmp/artn.obsreqs.sh 2>&1
echo "  completed BOOLEAN NOT NULL DEFAULT False,"                                                                                                                 >> /tmp/artn.obsreqs.sh 2>&1
echo "  non_sidereal_json JSONB DEFAULT '{}',"                                                                                                                     >> /tmp/artn.obsreqs.sh 2>&1
echo "  user_id SERIAL REFERENCES users(id));"                                                                                                                     >> /tmp/artn.obsreqs.sh 2>&1
echo "END_TABLE"                                                                                                                                                   >> /tmp/artn.obsreqs.sh 2>&1
echo ""                                                                                                                                                            >> /tmp/artn.obsreqs.sh 2>&1
echo "${PSQL_CMD} << END_OBSREQ"                                                                                                                                   >> /tmp/artn.obsreqs.sh 2>&1
echo "INSERT INTO obsreqs (username, pi, created_iso, created_mjd, group_id, observation_id, priority, priority_value,"                                            >> /tmp/artn.obsreqs.sh 2>&1
echo "object_name, ra_hms, ra_deg, dec_dms, dec_deg, begin_iso, begin_mjd, end_iso, end_mjd, airmass, lunarphase, moonphase,"                                      >> /tmp/artn.obsreqs.sh 2>&1
echo "photometric, guiding, non_sidereal, filter_name, exp_time, num_exp, binning, dither, cadence, telescope, instrument,"                                        >> /tmp/artn.obsreqs.sh 2>&1
echo "rts2_doc, rts2_id, queued, completed, non_sidereal_json, user_id) VALUES"                                                                                    >> /tmp/artn.obsreqs.sh 2>&1

# +
# create record(s)
# -
echo "Creating observation record for Demo1"
_begin_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(0)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_begin_isot=$(echo ${_begin_time} | cut -d' ' -f1)
_begin_iso=${_begin_isot//T/ }
_begin_mjd=$(echo ${_begin_time} | cut -d' ' -f2)
_end_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(30)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_end_isot=$(echo ${_end_time} | cut -d' ' -f1)
_end_iso=${_end_isot//T/ }
_end_mjd=$(echo ${_end_time} | cut -d' ' -f2)
_gid=$(echo -e "import hashlib;print(hashlib.sha256('${_begin_isot}'.encode('utf-8')).hexdigest())" | python3)
_oid=$(echo -e "import hashlib;print(hashlib.sha256('${_end_isot}'.encode('utf-8')).hexdigest())" | python3)
_ra_hms="01:02:03.04"
_ra_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_ra_hms} hours').degree))" | python3)
_dec_dms="-12:13:14.15"
_dec_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_dec_dms} degrees').degree))" | python3)
echo "('Demo1', 'Demo1', '${_begin_iso}', ${_begin_mjd},"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_gid}', '${_oid}', 'Routine', ${_begin_mjd},"                                                                                                             >> /tmp/artn.obsreqs.sh 2>&1
echo "'Demo1 Object', '${_ra_hms}', ${_ra_deg}, '${_dec_dms}', ${_dec_deg},"                                                                                       >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_begin_iso}', ${_begin_mjd}, '${_end_iso}', ${_end_mjd}, 1.5, 'Dark', 2.5,"                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "False, False, False, 'U', 30.0, 5,"                                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'3x3', 'None', 'Once', 'Kuiper', 'Mont4k', '{}', -1, False, False, '{}', 1),"                                                                                >> /tmp/artn.obsreqs.sh 2>&1

echo "Creating observation record for Demo2"
_begin_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(1)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_begin_isot=$(echo ${_begin_time} | cut -d' ' -f1)
_begin_iso=${_begin_isot//T/ }
_begin_mjd=$(echo ${_begin_time} | cut -d' ' -f2)
_end_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(31)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_end_isot=$(echo ${_end_time} | cut -d' ' -f1)
_end_iso=${_end_isot//T/ }
_end_mjd=$(echo ${_end_time} | cut -d' ' -f2)
_gid=$(echo -e "import hashlib;print(hashlib.sha256('${_begin_isot}'.encode('utf-8')).hexdigest())" | python3)
_oid=$(echo -e "import hashlib;print(hashlib.sha256('${_end_isot}'.encode('utf-8')).hexdigest())" | python3)
_ra_hms="05:06:07.08"
_ra_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_ra_hms} hours').degree))" | python3)
_dec_dms="-30:30:30.30"
_dec_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_dec_dms} degrees').degree))" | python3)
echo "('Demo2', 'Demo2', '${_begin_iso}', ${_begin_mjd},"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_gid}', '${_oid}', 'Routine', ${_begin_mjd},"                                                                                                             >> /tmp/artn.obsreqs.sh 2>&1
echo "'Demo2 Object', '${_ra_hms}', ${_ra_deg}, '${_dec_dms}', ${_dec_deg},"                                                                                       >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_begin_iso}', ${_begin_mjd}, '${_end_iso}', ${_end_mjd}, 1.5, 'Dark', 2.5,"                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "False, False, False, 'B', 35.0, 4,"                                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'3x3', 'None', 'Once', 'Kuiper', 'Mont4k', '{}', -1, False, False, '{}', 1),"                                                                                >> /tmp/artn.obsreqs.sh 2>&1

echo "Creating observation record for Demo3"
_begin_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(2)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_begin_isot=$(echo ${_begin_time} | cut -d' ' -f1)
_begin_iso=${_begin_isot//T/ }
_begin_mjd=$(echo ${_begin_time} | cut -d' ' -f2)
_end_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(32)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_end_isot=$(echo ${_end_time} | cut -d' ' -f1)
_end_iso=${_end_isot//T/ }
_end_mjd=$(echo ${_end_time} | cut -d' ' -f2)
_gid=$(echo -e "import hashlib;print(hashlib.sha256('${_begin_isot}'.encode('utf-8')).hexdigest())" | python3)
_oid=$(echo -e "import hashlib;print(hashlib.sha256('${_end_isot}'.encode('utf-8')).hexdigest())" | python3)
_ra_hms="01:02:03.04"
_ra_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_ra_hms} hours').degree))" | python3)
_dec_dms="-12:13:14.15"
_dec_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_dec_dms} degrees').degree))" | python3)
echo "('Demo3', 'Demo3', '${_begin_iso}', ${_begin_mjd},"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_gid}', '${_oid}', 'Routine', ${_begin_mjd},"                                                                                                             >> /tmp/artn.obsreqs.sh 2>&1
echo "'Demo3 Object', '${_ra_hms}', ${_ra_deg}, '${_dec_dms}', ${_dec_deg},"                                                                                       >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_begin_iso}', ${_begin_mjd}, '${_end_iso}', ${_end_mjd}, 1.5, 'Dark', 2.5,"                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "False, False, False, 'V', 40.0, 3,"                                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'3x3', 'None', 'Once', 'Kuiper', 'Mont4k', '{}', -1, False, False, '{}', 1),"                                                                                >> /tmp/artn.obsreqs.sh 2>&1

echo "Creating observation record for Demo4"
_begin_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(3)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_begin_isot=$(echo ${_begin_time} | cut -d' ' -f1)
_begin_iso=${_begin_isot//T/ }
_begin_mjd=$(echo ${_begin_time} | cut -d' ' -f2)
_end_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(33)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_end_isot=$(echo ${_end_time} | cut -d' ' -f1)
_end_iso=${_end_isot//T/ }
_end_mjd=$(echo ${_end_time} | cut -d' ' -f2)
_gid=$(echo -e "import hashlib;print(hashlib.sha256('${_begin_isot}'.encode('utf-8')).hexdigest())" | python3)
_oid=$(echo -e "import hashlib;print(hashlib.sha256('${_end_isot}'.encode('utf-8')).hexdigest())" | python3)
_ra_hms="01:02:03.04"
_ra_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_ra_hms} hours').degree))" | python3)
_dec_dms="-12:13:14.15"
_dec_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_dec_dms} degrees').degree))" | python3)
echo "('Demo4', 'Demo4', '${_begin_iso}', ${_begin_mjd},"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_gid}', '${_oid}', 'Routine', ${_begin_mjd},"                                                                                                             >> /tmp/artn.obsreqs.sh 2>&1
echo "'Demo4 Object', '${_ra_hms}', ${_ra_deg}, '${_dec_dms}', ${_dec_deg},"                                                                                       >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_begin_iso}', ${_begin_mjd}, '${_end_iso}', ${_end_mjd}, 1.5, 'Dark', 2.5,"                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "False, False, False, 'R', 45.0, 2,"                                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'3x3', 'None', 'Once', 'Kuiper', 'Mont4k', '{}', -1, False, False, '{}', 1),"                                                                                >> /tmp/artn.obsreqs.sh 2>&1

echo "Creating observation record for Demo5"
_begin_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(4)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_begin_isot=$(echo ${_begin_time} | cut -d' ' -f1)
_begin_iso=${_begin_isot//T/ }
_begin_mjd=$(echo ${_begin_time} | cut -d' ' -f2)
_end_time=$(echo -e "from astropy.time import Time;from datetime import datetime, timedelta;_t=(datetime.now()+timedelta(34)).isoformat();print(_t, float(Time(_t).mjd))" | python3)
_end_isot=$(echo ${_end_time} | cut -d' ' -f1)
_end_iso=${_end_isot//T/ }
_end_mjd=$(echo ${_end_time} | cut -d' ' -f2)
_gid=$(echo -e "import hashlib;print(hashlib.sha256('${_begin_isot}'.encode('utf-8')).hexdigest())" | python3)
_oid=$(echo -e "import hashlib;print(hashlib.sha256('${_end_isot}'.encode('utf-8')).hexdigest())" | python3)
_ra_hms="01:02:03.04"
_ra_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_ra_hms} hours').degree))" | python3)
_dec_dms="-12:13:14.15"
_dec_deg=$(echo -e "from astropy.coordinates import Angle;print(float(Angle('${_dec_dms} degrees').degree))" | python3)
echo "('Demo5', 'Demo5', '${_begin_iso}', ${_begin_mjd},"                                                                                                          >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_gid}', '${_oid}', 'Routine', ${_begin_mjd},"                                                                                                             >> /tmp/artn.obsreqs.sh 2>&1
echo "'Demo5 Object', '${_ra_hms}', ${_ra_deg}, '${_dec_dms}', ${_dec_deg},"                                                                                       >> /tmp/artn.obsreqs.sh 2>&1
echo "'${_begin_iso}', ${_begin_mjd}, '${_end_iso}', ${_end_mjd}, 1.5, 'Dark', 2.5,"                                                                               >> /tmp/artn.obsreqs.sh 2>&1
echo "False, False, True, 'I', 30.0, 1,"                                                                                                                           >> /tmp/artn.obsreqs.sh 2>&1
echo "'3x3', 'None', 'Once', 'Kuiper', 'Mont4k',"                                                                                                                  >> /tmp/artn.obsreqs.sh 2>&1
echo "'{\"Object_Rate\": \"0.05\", \"RA_BiasRate\": \"0.06\", \"Dec_BiasRate\": \"0.07\", \"PositionAngle\": \"90.0\", \"UTC_At_Position\": \"${_begin_isot}\"}'," >> /tmp/artn.obsreqs.sh 2>&1
echo "-1, False, False, '{}', 1);"                                                                                                                                 >> /tmp/artn.obsreqs.sh 2>&1
echo "END_OBSREQ"                                                                                                                                                  >> /tmp/artn.obsreqs.sh 2>&1


# +
# execute
# -
write_blue "%% bash $0 --database=${artn_db_name} --hostname=${artn_db_host} --password=${artn_db_pass} --username=${artn_db_user} --dry-run=${dry_run}"
if [[ ${dry_run} -eq 1 ]]; then
  if [[ "${USER}" != "root" ]]; then
    write_red "WARNING: you need to be root to execute these commands!"
  fi
  if [[ ! -f /tmp/artn.obsreqs.sh ]]; then
    write_red "WARNING: /tmp/artn.obsreqs.sh does not exist!"
  fi
  write_yellow "Dry-Run> chmod a+x /tmp/artn.obsreqs.sh"
  write_yellow "Dry-Run> bash /tmp/artn.obsreqs.sh"
  write_yellow "Dry-Run> rm -f /tmp/artn.obsreqs.sh"
  write_yellow "Dry-Run> PGPASSWORD='${artn_db_pass}' psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name} -c 'SELECT * FROM obsreqs;'"

else
  if [[ "${USER}" != "root" ]]; then
    write_red "ERROR: you need to be root to execute these commands!"
    usage
    exit
  fi
  if [[ ! -f /tmp/artn.obsreqs.sh ]]; then
    write_red "ERROR: /tmp/artn.obsreqs.sh does not exist!"
    usage
    exit
  fi
  write_green "Executing> chmod a+x /tmp/artn.obsreqs.sh"
  chmod a+x /tmp/artn.obsreqs.sh
  write_green "Executing> bash /tmp/artn.obsreqs.sh"
  bash /tmp/artn.obsreqs.sh
  write_green "Executing> rm -f /tmp/artn.obsreqs.sh"
  rm -f /tmp/artn.obsreqs.sh
  write_green "Executing> PGPASSWORD='${artn_db_pass}' psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name} -c 'SELECT * FROM obsreqs;'"
  PGPASSWORD="${artn_db_pass}" psql --echo-all -h ${_host} -p ${_port} -U ${artn_db_user} -d ${artn_db_name} -c "SELECT * FROM obsreqs;"
fi


# +
# exit
# -
exit 0
