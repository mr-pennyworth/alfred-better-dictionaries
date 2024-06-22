# -*- coding: utf-8 -*-

import plistlib


def read(plist_path: str):
    with open(plist_path, "rb") as f:
        return plistlib.load(f)


def dump(obj, path: str):
    with open(path, "wb") as f:
        return plistlib.dump(obj, f)
