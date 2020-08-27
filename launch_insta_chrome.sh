#!/bin/bash

echo "Launching insta profile.."

gnome-terminal -- google-chrome --remote-debugging-port=9223 --disable-gpu --profile-directory="Profile 2" www.instagram.com/marginkings

echo "Insta window initalized!"
