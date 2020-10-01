#!/bin/bash

echo "Initializing Optionbot..."

cd /usr/local/bin/

./launch_discord_chrome.sh
sleep 8
./launch_insta_chrome.sh
sleep 5
pidof chrome >/dev/null && echo "Chrome is running" || echo "Chrome NOT running"

cd /home/swing/projects/
. env/bin/activate
cd /home/swing/projects/optionbot/
gnome-terminal -- python3 run.py
