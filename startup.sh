#!/bin/sh

use_docker_database=0
use_console=0
run_tests=0
run_mysql_console=0

while getopts "Dcmt" opt; do
    case $opt in
    (D) use_docker_database=1 ;;
    (c) use_console=1 ;;
    (m) run_mysql_console=1 ;;
    (t) run_tests=1 ;;
    (*) printf "Illegal option '-%s'\n" "$opt" && exit 1 ;;
    esac
done


if [[ $run_tests -eq 1 ]]; then
  echo "Test harness not yet established."
  exit 1
fi


mysql_conf=$(python3 ./src/configuration.py database_url)
if [ -z $mysql_conf ]; then
  echo "Unable to assertain MySQL configuration."
  exit 1
fi

re='^[^:]+://([^:]+):([^@]+)@([^:]+):([0-9]+)/([A-Za-z][A-Za-z0-9_]+).*$'
[[ $mysql_conf =~ $re ]] \
  && username="${BASH_REMATCH[1]}" \
  && password="${BASH_REMATCH[2]}" \
  && host="${BASH_REMATCH[3]}" \
  && port="${BASH_REMATCH[4]}" \
  && dbname="${BASH_REMATCH[5]}"

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
      if [[ $(mysqladmin ping --user=$username --password=$password --protocol=tcp --port=$port) == *"mysqld is alive"* ]]; then
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

sentinel=0
until mysql -h $host -P $port -u$username -p$password -D $dbname -e ";"; do
  ((sentinel++))
  if [[ $sentinel -gt 10 ]]; then
    echo "No MySQL connection."
    exit 1
  fi
  sleep 1
  printf "."
done
echo "MySQL found running."

if [ $use_console -eq 1 ]; then
  python3 main.py -c
elif [ $run_mysql_console -eq 1 ]; then
  mysql -h $host -P $port -u$username -p$password -D $dbname
else
  python3 main.py
fi

if [ $use_docker_database -eq 1 ]; then
  docker-compose down
fi
