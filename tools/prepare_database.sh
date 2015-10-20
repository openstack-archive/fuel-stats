#!/bin/sh

echo "Preparing pgpass file ${FUELSTAT_DB_ROOTPGPASS}"
echo "*:*:*:${FUELSTAT_DB_ROOT}:${FUELSTAT_DB_ROOTPW}" > ${FUELSTAT_DB_ROOTPGPASS}
chmod 600 ${FUELSTAT_DB_ROOTPGPASS}

export PGPASSFILE=${FUELSTAT_DB_ROOTPGPASS}

echo "Trying to find out if role ${FUELSTAT_DB_USER} exists"
root_roles=$(psql -h 127.0.0.1 -U ${FUELSTAT_DB_ROOT} -t -c "SELECT 'HERE' from pg_roles where rolname='${FUELSTAT_DB_USER}'")
if [[ ${root_roles} == *HERE ]];then
  echo "Role ${FUELSTAT_DB_USER} exists. Setting password ${FUELSTAT_DB_PW}"
  psql -h 127.0.0.1 -U ${FUELSTAT_DB_ROOT} -c "ALTER ROLE ${FUELSTAT_DB_USER} WITH SUPERUSER LOGIN PASSWORD '${FUELSTAT_DB_PW}'"
else
  echo "Creating role ${FUELSTAT_DB_USER} with password ${FUELSTAT_DB_PASSWD}"
  psql -h 127.0.0.1 -U ${FUELSTAT_DB_ROOT} -c "CREATE ROLE ${FUELSTAT_DB_USER} WITH SUPERUSER LOGIN PASSWORD '${FUELSTAT_DB_PW}'"
fi

echo "Dropping database ${FUELSTAT_DB} if exists"
psql -h 127.0.0.1 -U ${FUELSTAT_DB_ROOT} -c "DROP DATABASE IF EXISTS ${FUELSTAT_DB}"
echo "Creating database ${FUELSTAT_DB}"
psql -h 127.0.0.1 -U ${FUELSTAT_DB_ROOT} -c "CREATE DATABASE ${FUELSTAT_DB} OWNER ${FUELSTAT_DB_USER}"
