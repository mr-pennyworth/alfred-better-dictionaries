#!/usr/bin/env bash

cd pyapp
pip3 install -r requirements.txt
python3 BetterDict.setup.py py2app --dist-dir=../ $@
cd ..
