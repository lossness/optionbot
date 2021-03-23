#!/bin/bash

echo "Launching Elite Twitter profile.."

gnome-terminal -- google-chrome --remote-debugging-port=9224 --disable-gpu --profile-directory="Profile 3" --user-data-dir=/home/swing/projects/optionbot/etwitter_session https://tweetdeck.twitter.com

echo "Elite Twitter window initalized!"
