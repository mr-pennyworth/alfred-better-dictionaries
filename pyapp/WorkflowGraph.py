# -*- coding: utf-8 -*-

import json
import plistlib
import uuid


def mkuid():
  return f'{uuid.uuid4()}'.upper()

def plistRead(path):
  with open(path, 'rb') as f:
    return plistlib.load(f)


def plistWrite(obj, path):
  with open(path, 'wb') as f:
    return plistlib.dump(obj, f)


class WorkflowGraph:
  # value of 'modifiers' property of a connection when it has cmd
  CMD = 1048576

  def __init__(self, plist_path):
    self.plist_path = plist_path
    self.wf = plistRead(self.plist_path)

  def newJunction(self):
    junction_uuid = mkuid()
    junction = {
      'type': 'alfred.workflow.utility.junction',
      'uid': junction_uuid,
      'version': 1
    }
    self.wf['objects'].append(junction)
    self.wf['uidata'][junction_uuid] = {
      'noexport': 1,
      'xpos': 0,
      'ypos': 0,
    }
    self.wf['connections'][junction_uuid] = []
    return junction

  def newHotkey(self, note):
    hotkey_uuid = mkuid()
    hotkey = {
      'type': 'alfred.workflow.trigger.hotkey',
      'uid': hotkey_uuid,
      'version': 2,
      'config': {
        'action': 0,
        'argument': 0,
        'focusedappvariable': False,
        'focusedappvariablename': '',
        'hotkey': 0,
        'hotmod': 0,
        'hotstring': '',
        'leftcursor': False,
        'modsmode': 0,
        'relatedAppsMode': 0,
      },
    }
    self.wf['objects'].append(hotkey)
    self.wf['uidata'][hotkey_uuid] = {
      'note': note,
      'noexport': 1,
      'xpos': 0,
      'ypos': 0,
    }
    self.wf['connections'][hotkey_uuid] = []
    return hotkey

  def newFallbackSearch(self, note, title):
    fallback_search_uuid = mkuid()
    fallback_search = {
      'type': 'alfred.workflow.trigger.fallback',
      'uid': fallback_search_uuid,
      'version': 1,
      'config': {
        'text': title,
      },
    }
    self.wf['objects'].append(fallback_search)
    self.wf['uidata'][fallback_search_uuid] = {
      'note': note,
      'noexport': 1,
      'xpos': 0,
      'ypos': 0,
    }
    self.wf['connections'][fallback_search_uuid] = []
    return fallback_search

  def newBashScriptFilter(self, title, script, note):
    script_filter_uuid = mkuid()
    script_filter = {
      'type': 'alfred.workflow.input.scriptfilter',
      'uid': script_filter_uuid,
      'version': 3,
      'config': {
        'title': title,
        'script': script,
        'runningsubtext': 'loading...',
        'subtext': '',
        'alfredfiltersresults': False,
        'alfredfiltersresultsmatchmode': 1,
        'argumenttreatemptyqueryasnil': True,
        'argumenttrimmode': 0,
        'argumenttype': 0,
        'escaping': 102,
        'queuedelaycustom': 3,
        'queuedelayimmediatelyinitially': True,
        'queuedelaymode': 0,
        'queuemode': 2,
        'scriptargtype': 1,
        'scriptfile': '',
        'type': 0,
        'withspace': True,
      },
    }
    self.wf['objects'].append(script_filter)
    self.wf['uidata'][script_filter_uuid] = {
      'note': note,
      'noexport': 1,
      'xpos': 0,
      'ypos': 0,
    }
    self.wf['connections'][script_filter_uuid] = []
    return script_filter
    
  def getObjWithLabel(self, label):
    for uid, data in self.wf['uidata'].items():
      if data.get('note') == label:
        for obj in self.wf['objects']:
          if obj['uid'] == uid:
            return obj

  def addOutputToRouter(self, router, output):
    output_uuid = mkuid()
    router['config']['conditions'].append({
      'inputstring': '{var:dict_id}',
      'matchcasesensitive': False,
      'matchmode': 0,
      'matchstring': output,
      'outputlabel': output,
      'uid': output_uuid
    })
    return output_uuid

  def connect(self, src, dst, mod=0, src_out=None):
    connection = {
      'destinationuid': dst['uid'],
      'modifiers': mod,
      'modifiersubtext': '',
      'vitoclose': False,
    }
    if src_out is not None:
      connection['sourceoutputuid'] = src_out

    if src['uid'] not in self.wf['connections']:
      self.wf['connections'][src['uid']] = []

    self.wf['connections'][src['uid']].append(connection)
    
  def x(self, obj):
    return self.wf['uidata'][obj['uid']]['xpos']

  def y(self, obj):
    return self.wf['uidata'][obj['uid']]['ypos']

  def setX(self, obj, x):
    self.wf['uidata'][obj['uid']]['xpos'] = x

  def setY(self, obj, y):
    self.wf['uidata'][obj['uid']]['ypos'] = y

  def getOutputCount(self, router):
    return len(router['config']['conditions'])

  def save(self):
    plistWrite(self.wf, self.plist_path)
