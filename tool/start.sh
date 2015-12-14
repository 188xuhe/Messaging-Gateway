#!/bin/sh



killall -9 "python"

cd ~/test_server/src/src
source ../webapp/venv/bin/activate
python main.py
sleep 99999999
