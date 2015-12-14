#!/bin/sh

SCREEN_NAME=sb_server

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

screen -R $SCREEN_NAME $DIR/start.sh