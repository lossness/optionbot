#!/bin/bash

echo "Launching FlowAlerts main page"

gnome-terminal -- google-chrome --remote-debugging-port=9225 --user-agent="Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.81 Mobile Safari/537.36" --disable-gpu --profile-directory="Profile 4" --user-data-dir=/home/swing/projects/optionbot/mtwitter_session https://instagram.com/flowalerts

echo "The main FlowAlerts page window has been initalized!"
