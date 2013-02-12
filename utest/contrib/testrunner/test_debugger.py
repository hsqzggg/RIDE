from contextlib import contextmanager
import threading
import unittest
import time
from robotide.contrib.testrunner.TestRunnerAgent import RobotDebugger

class TestDebugger(unittest.TestCase):

    def setUp(self):
        self._debugger = RobotDebugger()

    def test_pausing_and_resuming(self):
        self.assertFalse(self._debugger.is_paused())
        self._debugger.pause()
        self.assertTrue(self._debugger.is_paused())
        self._debugger.resume()
        self.assertFalse(self._debugger.is_paused())

    def test_step_next(self):
        self._debugger.pause()
        started = threading.Event()
        first_keyword_done = threading.Event()
        second_keyword_done = threading.Event()
        third_keyword_done = threading.Event()
        wait_for_step_next_before_entering_debugger = threading.Event()

        def test_execution():
            started.set()
            with self.kw():
                first_keyword_done.set()
                wait_for_step_next_before_entering_debugger.wait()
                with self.kw():
                    second_keyword_done.set()
            with self.kw():
                third_keyword_done.set()

        def debugger_signals():
            self._verify_done(started)
            self.assertFalse(first_keyword_done.isSet())
            self._debugger.step_next()
            self._verify_done(first_keyword_done)
            self.assertFalse(second_keyword_done.isSet())
            self._debugger.step_next()
            wait_for_step_next_before_entering_debugger.set()
            self._verify_done(second_keyword_done)
            self.assertFalse(third_keyword_done.isSet())
            self._debugger.step_next()
            self._verify_done(third_keyword_done)

        t = threading.Thread(target=test_execution)
        t.setDaemon(True)
        t.start()
        debugger_signals()
        t.join()

    def _verify_done(self, event):
        self.assertTrue(event.wait(timeout=1.0) or event.isSet())

    @contextmanager
    def kw(self):
        self._debugger.start_keyword()
        yield
        self._debugger.end_keyword()

    def test_step_over(self):
        self._debugger.pause()
        started = threading.Event()
        first_keyword_done = threading.Event()
        second_keyword_done = threading.Event()
        last_keyword_done = threading.Event()

        def test_execution():
            started.set()
            with self.kw():
                first_keyword_done.set()
                with self.kw():
                    second_keyword_done.set()
                with self.kw():
                    pass
                with self.kw():
                    pass
            with self.kw():
                last_keyword_done.set()

        def debugger_signals():
            self._verify_done(started)
            self.assertFalse(first_keyword_done.isSet())
            self._debugger.step_over()
            self._verify_done(first_keyword_done)
            self._verify_done(second_keyword_done)
            self.assertFalse(last_keyword_done.isSet())
            self._debugger.step_over()
            self._verify_done(last_keyword_done)

        t = threading.Thread(target=test_execution)
        t.setDaemon(True)
        t.start()
        debugger_signals()
        t.join()


if __name__ == '__main__':
    unittest.main()