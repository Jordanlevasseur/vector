"""Real protected desktop Send/render/history path with default advanced flags off."""
import unittest
import test_desktop_stage1 as desktop_fixture
class RoutingDesktopTests(unittest.TestCase):
 run_gui=desktop_fixture.DesktopStage1Tests.run_gui
 def test_default_chat_checked_math_continuation_gaps_and_history(self):
  self.run_gui(r'''
assert not app.planning_enabled.get() and not app.semantic_enabled.get()
for question,expected in [('What is 568 times 564?','320352'),('568 multiplied by 564','320352'),('Calculate (13 + 7) * 2, then divide the result by 8.','5'),('What is 25% of 200?','50.00'),('Divide that by 2','25.00')]:
 app.question.insert(0,question);app.send_chat();wait();record=app.last_response['result'];assert record['checked']['findings'][-1]['values'][0]['value']==expected,record;assert 'Verified calculation:' in app.chat.get('1.0','end');assert record['outcome']['generation'] is None
app.shell.reset();app.question.insert(0,'Sum up the Declaration of Independence.');app.send_chat();wait();assert 'cannot provide a reliable complete document summary' in app.chat.get('1.0','end');assert 'interrupted' not in app.chat.get('1.0','end')
app.shell.reset();app.question.insert(0,'Why might a small fan vibrate intermittently?');app.send_chat();wait();assert 'not established a verified answer' in app.chat.get('1.0','end');assert app.last_response['result']['context'] is None
app.load_history();wait();assert '320352' in app.chat.get('1.0','end');assert not app.planning_enabled.get() and not app.semantic_enabled.get()
''')
