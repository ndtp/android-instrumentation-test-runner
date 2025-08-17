import time
from enum import Enum


class TestResult:
    class TestStatus(Enum):
        ERROR = "ERROR"
        FAILURE = "FAILURE"
        PASSED = "PASSED"
        INCOMPLETE = "INCOMPLETE"
        SKIPPED = "SKIPPED"

    def __init__(self):
        self._status = TestResult.TestStatus.INCOMPLETE
        self._stack_trace = None
        self._metrics = None
        self._start_time = int(time.time() * 1000)
        self._end_time = 0

    def get_status(self):
        return self._status

    def get_stack_trace(self):
        return self._stack_trace

    def get_metrics(self):
        return self._metrics

    def set_metrics(self, metrics):
        self._metrics = metrics

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def set_status(self, status):
        self._status = status
        return self

    def set_stack_trace(self, trace):
        self._stack_trace = trace

    def set_end_time(self, current_time_millis=None):
        if current_time_millis is None:
            current_time_millis = int(time.time() * 1000)
        self._end_time = current_time_millis

    def __eq__(self, other):
        if not isinstance(other, TestResult):
            return False
        return (self._metrics == other._metrics and
                self._stack_trace == other._stack_trace and
                self._status == other._status)

    def __hash__(self):
        return hash((str(self._metrics), self._stack_trace, self._status))
