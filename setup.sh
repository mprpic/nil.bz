#!/bin/sh

for app in pip virtualenv; do
    if [ "$(which ${app} >/dev/null 2>&1; echo $?)" == "1" ]; then
        echo "${app} not found, please install it!"
        exit 1
    fi
done

virtualenv venv
venv/bin/pip install -r requirements.txt
