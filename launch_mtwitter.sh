#!/bin/bash

echo "Launching Mike Twitter profile.."

gnome-terminal -- google-chrome --remote-debugging-port=9225 --disable-gpu --profile-directory="Profile 4" --user-data-dir=/home/swing/projects/optionbot/mtwitter_session https://tweetdeck.twitter.com

echo "Mike Twitter window initalized!"
