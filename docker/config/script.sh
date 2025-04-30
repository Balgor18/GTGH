#!/bin/bash

set -x

pip install --upgrade pip
pip install -r /requirements.txt

if [ $DEBUG -eq 1 ]
then
   /usr/bin/tail -f /dev/null
fi
python3 github_exporter.py