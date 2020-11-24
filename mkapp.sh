#!/usr/bin/env bash

cd pyapp
pip install -r requirements.txt
python BetterDict.setup.py py2app --dist-dir=../ $@
cd ..
