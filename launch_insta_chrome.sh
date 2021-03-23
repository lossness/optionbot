#!/bin/bash

echo "Launching insta profile.."

gnome-terminal -- google-chrome --remote-debugging-port=9223 --user-agent="Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.81 Mobile Safari/537.36" --disable-gpu --profile-directory="Profile 2"    --user-data-dir=/home/swing/projects/optionbot/insta_session www.instagram.com/flowalertslounge

echo "Insta window initalized!"
