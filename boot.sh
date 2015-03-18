#!/bin/sh
BASE_SCREEN_NAME=velib-irc-bot
SCREEN_NAME=$BASE_SCREEN_NAME

echo "Launching $SCREEN_NAME.."

screen -wipe
screen_nb=`screen -ls | grep $SCREEN_NAME | wc -l`
if [ $screen_nb -gt 0 ]
then
    echo "Killing existing $SCREEN_NAME"
    screen -X -S $SCREEN_NAME quit
    sleep 5
fi

screen -dmS $SCREEN_NAME ./bin/velib-irc-bot

echo 'Done.'