#!/usr/bin/env bash

pip3 install -r pyapp/requirements.txt
pyinstaller pyapp/BetterDict.py --onefile --noconfirm --distpath ./
