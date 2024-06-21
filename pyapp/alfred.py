# -*- coding: utf-8 -*-

import os


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
