#!/bin/bash
function ctrl_c() {
    kill -9 $(ps | grep python | cut -f 1 -d ' ')
    exit
}

python manage.py livereload --settings=mprjlabeler.settings_dev &
LIVERELOAD_PID=$!
python manage.py runserver 0.0.0.0:8080 --settings=mprjlabeler.settings_dev &
MANAGE_PID=$!

trap ctrl_c INT

sleep 2 
echo Livereload $LIVERELOAD_PID
echo Runserver $MANAGE_PID

while true
do
    sleep 10
done
