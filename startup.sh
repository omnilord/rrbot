#!/bin/sh

use_docker_database=0
use_console=0
run_tests=0
while getopts "Dct" opt
do
    case $opt in
    (D) use_docker_database=1 ;;
    (c) use_console=1 ;;
    (t) echo "Test harness not yet established." && exit 1 ;;
    (*) printf "Illegal option '-%s'\n" "$opt" && exit 1 ;;
    esac
done

if [ $use_docker_database -eq 1 ]; then
  name='rrbot_db_1'
  echo "Checking docker for '$name' container..."

  # Check if docker is running
  if [ ! docker info >/dev/null 2>&1 ]; then
      echo "Docker does not seem to be running, run it first and retry"
      exit 1
  fi

  if [[ $(docker ps --filter "name=^$name$" --format '{{.Names}}') == $name ]]; then
    echo "Database is already running."
  else
    if [[ ! -d ./.data ]]; then
      mkdir ./.data
    fi

    echo "Spinning up docker container.  If this is the first time, it could take up to a minute to respond."

    docker-compose up -d

    sentinel=0
    while [ $sentinel -lt 60 ]; do
      print '.'
      if [[ $(mysqladmin ping --user=rrbot --password=rrbot --protocol=tcp --port=3306) == *"mysqld is alive"* ]]; then
        echo "MySQL detect alive."
        break
      fi
      sentinel=$((sentinel + 5))
      sleep 5
    done

    if [[ $sentinel -gt 29 ]]; then
      echo "MySQL docker container took too long to detect."
      exit 1
    fi

    alembic upgrade head
  fi

  echo "---===---"
fi

cd src

if [ $use_console -eq 1 ]; then
  py3 main.py -c
else
  py3 main.py
fi

if [ $use_docker_database -eq 1 ]; then
  docker-compose down
fi
