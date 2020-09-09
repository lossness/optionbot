#!/bin/bash

echo "Launching insta profile.."

gnome-terminal -- google-chrome --remote-debugging-port=9223 --user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1" --disable-gpu --profile-directory="Profile 2"    --user-data-dir=/home/swing/projects/optionbot/insta_session www.instagram.com/flowalertslounge

echo "Insta window initalized!"
