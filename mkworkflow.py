# -*- coding: utf-8 -*-

import os
import platform
import plistlib
import shutil
import subprocess

from contextlib import contextmanager


BUILD_DIR = 'wfbuild'
WF_FILES = [
  'AlfredExtraPane.app',
  'alfred-dict-server',
  'cocoaDialog.app',
  'dict-entry.css',
  'icon.png',
  'info.plist',
  'jq',
  'pyapp',
  'python',
  'README.md',
  'sayipa.sh',
  'search.sh',
  'setup.sh',
]


def copy(filenames, dest_folder):
  if os.path.exists(dest_folder):
    shutil.rmtree(dest_folder)
  os.makedirs(dest_folder)

  for filename in filenames:
    if os.path.isdir(filename):
      shutil.copytree(filename, f'{dest_folder}/{filename}')
    else:
      shutil.copy(filename, f'{dest_folder}/{filename}')


def plistRead(path):
  with open(path, 'rb') as f:
    return plistlib.load(f)


def plistWrite(obj, path):
  with open(path, 'wb') as f:
    return plistlib.dump(obj, f)


@contextmanager
def cwd(dir):
  old_wd = os.path.abspath(os.curdir)
  os.chdir(dir)
  yield
  os.chdir(old_wd)

  
def make_export_ready(plist_path):
  wf = plistRead(plist_path)

  # remove noexport vars
  wf['variablesdontexport'] = []

  # remove noexport objects
  noexport_uids = [
    uid
    for uid, data
    in wf['uidata'].items()
    if 'noexport' in data
  ]

  # direct forward references
  for noexport_uid in noexport_uids:
    del wf['connections'][noexport_uid]
    del wf['uidata'][noexport_uid]

  # actual objects
  new_objs = []
  for obj in wf['objects']:
    if obj['uid'] not in noexport_uids:
      new_objs.append(obj)
  wf['objects'] = new_objs

  # backward references
  new_connections = {}
  for src_uid, conn_infos in wf['connections'].items():
    new_conn_infos = []
    for conn_info in conn_infos:
      if not conn_info['destinationuid'] in noexport_uids:
        new_conn_infos.append(conn_info)
    new_connections[src_uid] = new_conn_infos
  wf['connections'] = new_connections

  #remove noexport router outputs
  for uid, data in wf['uidata'].items():
    if data.get('note') == 'router':
      for obj in wf['objects']:
        if obj['uid'] == uid:
          router = obj
          router['config']['conditions'] = router['config']['conditions'][:1]

  # add readme
  with open('README.md') as f:
    wf['readme'] = f.read()

  plistWrite(wf, plist_path)
  return wf['name']


if __name__ == '__main__':
  subprocess.call(['./mkapps.sh'])
  copy(WF_FILES, BUILD_DIR)
  wf_name = make_export_ready(f'{BUILD_DIR}/info.plist')
  wf_filename = f'{wf_name}.{platform.machine()}.alfredworkflow'
  with cwd(BUILD_DIR):
    subprocess.call(['zip', '-r', f'../{wf_filename}'] + WF_FILES)
