#!/bin/bash

pip install --user python-telegram-bot --upgrade
printf "Enter API token for bot: "
read token
printf "Enter allowed user for bot: "
read user
sed -ie "s/BASHTOKENFORTELEGRAM/$token/g" ssb.py
sed -ie "s/ALLOWEDUSER/$user/g" ssb.py
