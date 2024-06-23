# -*- coding: utf-8 -*-

import os
from dataclasses import asdict, dataclass, field
from typing import Optional, Dict


def infer_workflow_dir():
    candidate = os.getcwd()
    while not os.path.split(candidate)[1].startswith("user.workflow."):
        if candidate == "/":
            return None
        candidate = os.path.split(candidate)[0]
    return candidate


def get_workflow_dir():
    prefs_dir = os.environ.get("alfred_preferences")
    if prefs_dir is None:
        return infer_workflow_dir()

    workflow_uid = os.environ.get("alfred_workflow_uid")
    if workflow_uid is None:
        return infer_workflow_dir()

    return f"{prefs_dir}/workflows/{workflow_uid}"


def default_workflow_data_dir(workflow_id):
    return os.path.expanduser(
        f"~/Library/Application Support/Alfred/Workflow Data/{workflow_id}"
    )


@dataclass
class Mod:
    subtitle: Optional[str] = None
    arg: Optional[str] = None
    valid: Optional[bool] = None
    icon: Optional[Dict[str, str]] = field(default_factory=dict)


@dataclass
class Text:
    copy: Optional[str] = None
    largetype: Optional[str] = None


@dataclass
class Icon:
    type: Optional[str] = None
    path: Optional[str] = None


@dataclass
class Item:
    """https://www.alfredapp.com/help/workflows/inputs/script-filter/json/"""

    title: str
    uid: Optional[str] = None
    subtitle: Optional[str] = None
    arg: Optional[str] = None
    autocomplete: Optional[str] = None
    valid: Optional[bool] = None
    match: Optional[str] = None
    icon: Optional[Icon] = None
    mods: Optional[Dict[str, Mod]] = None
    text: Optional[Text] = None
    quicklookurl: Optional[str] = None

    def as_dict(self):
        def exclude_unset_fields(d):
            return {k: v for (k, v) in d if v is not None}

        return asdict(self, dict_factory=exclude_unset_fields)
