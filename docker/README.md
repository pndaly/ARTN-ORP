
# +
# install postgres clients - must match version in Dockerfile!
# -
```bash
apt update

apt install postgresql-client-common postgresql-client-12 
```


# +
# build the image
# -
```bash
bash artn.docker.sh --command=build --file=Dockerfile.artn --tag=artn/postgres-12:postgis3-q3c2 --verbose --dry-run

bash artn.docker.sh --name=artn --tag=artn/postgres-12:postgis3-q3c2 --verbose --dry-run
```


# +
# build the container
# -
```bash
bash artn.docker.sh --command=create --name=artn --tag=artn/postgres-12:postgis3-q3c2 --verbose --dry-run

bash artn.docker.sh --name=artn --tag=artn/postgres-12:postgis3-q3c2 --verbose --dry-run
```


# +
# connect to container
# -
```bash
bash artn.docker.sh --name=artn --command=connect
```


# +
# test
# -
```bash
PGPASSWORD=******** psql -h localhost -p 5432 -d artn -U artn -c "SELECT COUNT(*) FROM obsreqs;"
```
