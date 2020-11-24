# -*- coding: utf-8 -*-

import os
import sys

def infer_workflow_dir():
  candidate = sys.path[0]
  while not os.path.split(candidate)[1].startswith('user.workflow.'):
    candidate = os.path.split(candidate)[0]
  return candidate


def get_workflow_dir():
  prefs_dir = os.environ.get('alfred_preferences')
  if prefs_dir is None:
    return infer_workflow_dir()

  workflow_uid = os.environ.get('alfred_workflow_uid')
  if workflow_uid is None:
    return infer_workflow_dir()

  return f'{prefs_dir}/workflows/{workflow_uid}'

