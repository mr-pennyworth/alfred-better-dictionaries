# -*- coding: utf-8 -*-

import time

from multiprocess import Process, Queue
from subprocess import Popen, PIPE

import alfred


WORKFLOW_DIR = alfred.get_workflow_dir()
CD_PATH = f'{WORKFLOW_DIR}/cocoaDialog.app/Contents/MacOS/cocoaDialog'


class ProgressBar:
  
  def __init__(self, title='Progress', message='', percent=0.01):
    cmd = [
      CD_PATH, 'progressbar',
      '--title', title,
      '--text', message,
      '--percent', str(percent)
    ]
    self.proc = Popen(cmd, stdin=PIPE, encoding='utf-8')
    self.message = message
    self.start_time = time.time()
          
  def update(self, percent, message):
    elapsed_seconds = time.time() - self.start_time
    estimated_total_seconds = elapsed_seconds * 100 / percent
    estimated_remaining_seconds = estimated_total_seconds - elapsed_seconds
    rs = int(estimated_remaining_seconds) % 60
    rm = int(estimated_remaining_seconds) // 60
    eta_n_message = f'[ETA {rm:02d}:{rs:02d}] {message}'
    self.proc.stdin.write(f'{int(percent)} {eta_n_message}\n')
    self.proc.stdin.flush()
      
  def finish(self):
    self.proc.kill()


class IndefiniteProgressBar:

  def __init__(self, title='Progress', message=''):
    cmd = [
      CD_PATH, 'progressbar',
      '--title', title,
      '--text', message,
      '--indeterminate'
    ]
    self.proc = Popen(cmd, stdin=PIPE, encoding='utf-8')
    self.message = message
    self.start_time = time.time()
          
  def update(self, message):
    elapsed_seconds = time.time() - self.start_time
    es = int(elapsed_seconds) % 60
    em = int(elapsed_seconds) // 60
    time_n_message = f'[Elapsed {em:02d}:{es:02d}] {message}'
    self.proc.stdin.write(f'0 {time_n_message}\n')
    self.proc.stdin.flush()
      
  def finish(self):
    self.proc.kill()
  

class NoOpAcc:
  def add(self, items): pass
  def finish(self): pass

def run_parallely_with_progress_bar(
    items,
    func,
    msgfunc,
    accumulator=NoOpAcc(),
    title=''):
  PROC_COUNT = 5

  total = len(items)

  task_queue = Queue()
  done_queue = Queue()

  def pb_updater(inq, results_q):
    pb = ProgressBar(title)
    for i in range(total):
      msg, result = results_q.get()
      accumulator.add(result)
      pb.update(percent=((i+1)*100)/total, message=msg)
    pb.finish()
    accumulator.finish()

    # tell the workers to stop
    for i in range(PROC_COUNT):
      inq.put('STOP')

  def worker(inq, outq):
    for item in iter(inq.get, 'STOP'):
      result = func(item)
      outq.put((msgfunc(item), result))

  for i in range(PROC_COUNT):
    Process(target=worker, args=(task_queue, done_queue)).start()

  updater = Process(target=pb_updater, args=(task_queue, done_queue))
  updater.start()
  for item in items:
    task_queue.put(item)


def _run_parallely_with_progress_bar(items, func, msgfunc, title):
  pb = ProgressBar(title)
  total = len(items)

  for i, item in enumerate(items):
    pb.update(percent=((i+1)*100)/total, message=msgfunc(item))
    func(item)

  pb.finish()
