Arizona Robotic Telescope Network Observation Request Portal
------------------------------------------------------------

Welcome to the **A**rizona **R**obotic **T**elescope **N**etwork **O**bservation **R**equest 
**P**ortal (*ARTN ORP*) which is a Flask front end to a database for astronomers, scientists and engineers to request
observations on the diversity of telescopes within the network. Users *must* be authorized and accredited 
to use the system.

## Pre-Requisites

* Linux (we use Ubuntu 18.04 LTS)
* Python 3.7 (it will not work with Python < 3.6)
* PostGreSQL 12.x (but will probably work with earlier versions)
* wkhtmltopdf (if you want to generate PDF night logs)

## Get The Software

* Obtain a copy of the software from [GitHub](https://github.com/pndaly/ARTN-ORP).

* Install dependencies:

    ```bash
    % pip3 install --upgrade pip
    % pip3 install -r requirements.txt
    ```

## Create and Populate The Database and Tables

NB: All utility bash-shell scripts in ${ORP_BIN} support the `--help` argument for further information 
and the `--dry-run` option to show executable commands without invoking them. You would be well-advised
to use them!

* Create the *artn* database

    To create a database called *artn* with username *artn* and password *my_secret* (using the 
    PostGreSQL server defaults of *localhost:5432*), execute:
    
    ```bash
    % bash ${ORP_BIN}/artn.database.sh --database=artn --password=my_secret --username=artn --dry-run
    % cat /tmp/artn.database.sh
    % bash ${ORP_BIN}/artn.database.sh --database=artn --password=my_secret --username=artn
    ```
      
* Create the *users* table

    If you choose to leave the `${ARTN_BIN}/artn.users.sh` script as-is, the accounts created are:
    
    | Username      | Password      | Is Admin? | Is Disabled? |
    |:-------------:|:-------------:|:---------:|:------------:|
    | artn          | secretsanta   | Yes       | No           |
    | Demo1         | FooBar1       | No        | No           |
    | Demo2         | FooBar2       | No        | No           |
    | Demo3         | FooBar3       | No        | No           |
    | Demo4         | FooBar4       | No        | No           |
    | Demo5         | FooBar5       | No        | No           |
    
    *NB: You are, however, advised to edit the `${ORP_BIN}/artn.users.sh` script and change these defaults!*
    
    To create a *users* table within the *artn* database created above (using credentials
    *artn:my_secret* on the PostGreSQL server of *localhost:5432*), execute:
    
    ```bash
    % bash ${ORP_BIN}/artn.users.sh --database=artn --password=my_secret --username=artn --dry-run
    % cat /tmp/artn.users.sh
    % bash ${ORP_BIN}/artn.users.sh --database=artn --password=my_secret --username=artn
    ```

    *Once you have regular, registered, users we suggest you *disable* all Demo[1-5] accounts!*

* Create the *obsreqs* table

    Assuming you created the users table as above, to create an *obsreqs* table within the *artn* database 
    created above (using credentials *artn:my_secret* on the PostGreSQL server of *localhost:5432*), execute:
    
    ```bash
    % bash ${ORP_BIN}/artn.obsreqs.sh --database=artn --password=my_secret --username=artn --dry-run
    % cat /tmp/artn.obsreqs.sh
    % bash ${ORP_BIN}/artn.obsreqs.sh --database=artn --password=my_secret --username=artn
    ```

* Database entity-relationship diagram 

    If you have `eralchemy` installed, an entity-relationship diagram can be generated:
    
    ```bash
    % eralchemy -i "postgresql+psycopg2://${ARTN_DB_USER}:${ARTN_DB_PASS}@${ARTN_DB_HOST}:${ARTN_DB_PORT}/${ARTN_DB_NAME}" -o ${ARTN_DB_NAME}.pdf
    ```

* Database utilities

    We provide the following, generic, utilities for database manipulation:
    
    ```bash
    % bash ${ORP_BIN}/psql.size.sh --help
    % bash ${ORP_BIN}/psql.backup.sh --help
    % bash ${ORP_BIN}/psql.restore.sh --help
    ```

    We dockerize the database, so a utility is also provided for that:
    
    ```bash
    % bash ${ORP_BIN}/artn.docker.sh --help
    ```

    If you decide to use Docker, remember to restart the container after a reboot via root's `crontab` (and, of 
    course, replace `<path_to_shell_script>` with your installation path in the following):
    
    ```
    @reboot bash <path_to_shell_script>/artn.docker.sh --command=start
    ```

## Configure For Local Site

You should now *copy* `${ORP_BIN}/ORP.template.sh`, `${ORP_ETC}/ARTN.template.sh` and `${ORP_ETC}/ORP.template.sh` 
and edit the copies to suit your site and change:

   - local installation directory
   - database server and credentials
   - mail server and credentials
   - rts2 server (if using RTS2, otherwise ignore this setting)

```bash
% cp ${ORP_BIN}/ORP.template.sh ${ORP_BIN}/ORP.sh
% vi ${ORP_BIN}/ORP.sh
% cp ${ORP_ETC}/ARTN.template.sh ${ORP_ETC}/ARTN.sh
% vi ${ORP_ETC}/ARTN.sh
% cp ${ORP_ETC}/ORP.template.sh ${ORP_ETC}/ORP.sh
% vi ${ORP_ETC}/ORP.sh
```

## Quick Start Guide

If you carried out the above, and assuming the codebase is in /home/artn/ARTN-ORP, you can start the application:

* Local development server

    ```bash
    % cd /home/artn/ARTN-ORP
    % source etc/ARTN.sh
    % source etc/ORP.sh `pwd` localhost 5000
    % bash ${ORP_BIN}/ORP.sh --type=dev --source=/home/artn/ARTN-ORP --command=start --dry-run
    % bash ${ORP_BIN}/ORP.sh --type=dev --source=/home/artn/ARTN-ORP --command=start
    ```
    
    then point a browser to the local [ORP development server](http://localhost:5000/orp).
    
* Local production server

    ```bash
    % cd /home/artn/ARTN-ORP
    % source etc/ARTN.sh
    % source etc/ORP.sh `pwd` `hostname -i` 7500
    % bash ${ORP_BIN}/ORP.sh --type=prod --source=/home/artn/ARTN-ORP --command=start --dry-run
    % bash ${ORP_BIN}/ORP.sh --type=prod --source=/home/artn/ARTN-ORP --command=start
    ```
    
    then point a browser to the local [ORP production server](http://localhost:7500/orp).
    
* WSGI

    If you wish to run a WSGI-based server, we provide:

    * `${ARTN_HOME}/orp.wsgi` file which should work as-is
    * `${ARTN_HOME}/orp.conf` which should be edited: 
        `% sed 's/__myhost__/127\.0\.0\.1/g' >> /etc/apache2/sites-available/orp.conf` (or whatever IP address you have)
    * Enable the site via *Apache2* in the usual way

## IERS Updates

Sometime during 2019 astropy/astroplan broke due to the IERS ephemeris server at USNO going offline. To fix this,
we provide a cron job that updates the ephemeris from another source. The file `${ARTN_CRON}/iers.update.sh` contains
the crontab entry to show how to do this or the file can be run directly. We find that once per week is sufficient.

## RTS2 Users Only

You should *copy* `${ORP_SRC}/telescopes/rts2_config.template.json` and edit the copy to suit your site:

```bash
% cp ${ORP_SRC}/telescopes/rts2_config.template.json ${ORP_SRC}/telelscopes/rts2_config.json
% vi ${ORP_SRC}/telescopes/rts2_config.json
```

The `rts2_config.json` file contains the JSON snippet { "rts2url": "http://localhost:8889" }
for which we have to create an SSH tunnel. To do this, execute (*eg* on the Kuiper telescope):

```bash
% xterm -e ssh -X -L 8889:localhost:8889 -p 42022 rts2obs@kuiper.as.arizona.edu &
```

------------------------------------------------------------

Last Updated: 2020207
