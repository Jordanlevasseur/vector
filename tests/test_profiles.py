import os
from pathlib import Path
import subprocess
import sys
import unittest

ENV={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}

class ProfileTests(unittest.TestCase):
    def test_filter_synchronizes_existing_threads(self):
        script='''
import threading,socket,json
from vector_core.security import activate
ready=threading.Event();go=threading.Event();observed=[]
def probe():
 ready.set();go.wait()
 for family in (socket.AF_INET,socket.AF_INET6,socket.AF_UNIX):
  try:socket.socket(family,socket.SOCK_STREAM)
  except PermissionError:observed.append(True)
  else:observed.append(False)
t=threading.Thread(target=probe);t.start();ready.wait();activate();go.set();t.join(timeout=3)
assert observed==[True,True,True],observed
print(json.dumps({'thread_synchronized':True}))
'''
        child=subprocess.run([sys.executable,'-c',script],env=ENV,capture_output=True,text=True,timeout=10)
        self.assertEqual(child.returncode,0,child.stderr)
    def test_remote_display_is_refused_before_connecting(self):
        script='''
import argparse,os
os.environ['DISPLAY']='example.invalid:0'
from vector_core.desktop import bootstrap
try:bootstrap(argparse.Namespace())
except RuntimeError as error:assert 'remote displays are refused before connection' in str(error)
else:raise AssertionError('Remote display accepted')
'''
        child=subprocess.run([sys.executable,'-c',script],env=ENV,capture_output=True,text=True,timeout=10)
        self.assertEqual(child.returncode,0,child.stderr)
    def test_only_explicit_pipe_descriptors_may_be_retained(self):
        script='''
import tempfile
from vector_core.security import activate,SecurityError
with tempfile.TemporaryFile() as file:
 try:activate(pipe_fds=(file.fileno(),))
 except SecurityError:pass
 else:raise AssertionError('Regular file retained as IPC pipe')
'''
        child=subprocess.run([sys.executable,'-c',script],env=ENV,capture_output=True,text=True,timeout=10)
        self.assertEqual(child.returncode,0,child.stderr)
