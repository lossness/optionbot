#!/bin/bash

echo "Launching discord profile.."

gnome-terminal -- google-chrome --remote-debugging-port=9222 --disable-gpu --profile-directory="Profile 1" www.discord.com/channels/290278814217535489/699253100174770176

echo "Discord window initalized!"
