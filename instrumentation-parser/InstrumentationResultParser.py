import re
from collections import defaultdict
from TestIdentifier import TestIdentifier
from XmlTestRunListener import TestFailure

class StatusKeys:
    TEST = "test"
    CLASS = "class"
    STACK = "stack"
    NUMTESTS = "numtests"
    ERROR = "Error"
    SHORTMSG = "shortMsg"

KNOWN_KEYS = {
    StatusKeys.TEST,
    StatusKeys.CLASS,
    StatusKeys.STACK,
    StatusKeys.NUMTESTS,
    StatusKeys.ERROR,
    StatusKeys.SHORTMSG,
    "stream",
    "id",
    "current"
}

class StatusCodes:
    FAILURE = -2
    START = 1
    ERROR = -1
    OK = 0
    IN_PROGRESS = 2
    SKIPPED = -3

class Prefixes:
    STATUS = "INSTRUMENTATION_STATUS: "
    STATUS_CODE = "INSTRUMENTATION_STATUS_CODE: "
    STATUS_FAILED = "INSTRUMENTATION_FAILED: "
    CODE = "INSTRUMENTATION_CODE: "
    RESULT = "INSTRUMENTATION_RESULT: "
    TIME_REPORT = "Time: "

class InstrumentationResultParser:
    NO_TEST_RESULTS_MSG = "No test results"
    INCOMPLETE_TEST_ERR_MSG_PREFIX = "Test failed to run to completion"
    INCOMPLETE_TEST_ERR_MSG_POSTFIX = "Check device logcat for details"
    INCOMPLETE_RUN_ERR_MSG_PREFIX = "Test run failed to complete"

    class TestResult:
        def __init__(self):
            self.code = None
            self.test_name = None
            self.test_class = None
            self.stack_trace = None
            self.num_tests = None

        def is_complete(self):
            return self.code is not None and self.test_name is not None and self.test_class is not None

        def __str__(self):
            output = []
            if self.test_class:
                output.append(self.test_class)
            if self.test_name:
                output.append(f"#{self.test_name}")
            return "".join(output) if output else "unknown result"

    def __init__(self, run_name, listeners):
        self.mTestRunName = run_name
        self.mTestListeners = listeners if isinstance(listeners, list) else [listeners]
        self.mCurrentTestResult = None
        self.mLastTestResult = None
        self.mCurrentKey = None
        self.mCurrentValue = None
        self.mTestStartReported = False
        self.mTestRunFinished = False
        self.mTestRunFailReported = False
        self.mTestTime = 0
        self.mIsCancelled = False
        self.mNumTestsRun = 0
        self.mNumTestsExpected = 0
        self.mInInstrumentationResultKey = False
        self.mInstrumentationResultBundle = {}
        self.mTestMetrics = {}
        self.LOG_TAG = "InstrumentationResultParser"

    def process_new_lines(self, lines):
        for line in lines:
            self.parse(line)

    def parse(self, line):
        if line.startswith(Prefixes.STATUS_CODE):
            self.submit_current_key_value()
            self.mInInstrumentationResultKey = False
            self.parse_status_code(line)
        elif line.startswith(Prefixes.STATUS):
            self.submit_current_key_value()
            self.mInInstrumentationResultKey = False
            self.parse_key(line, len(Prefixes.STATUS))
        elif line.startswith(Prefixes.RESULT):
            self.submit_current_key_value()
            self.mInInstrumentationResultKey = True
            self.parse_key(line, len(Prefixes.RESULT))
        elif line.startswith(Prefixes.STATUS_FAILED) or line.startswith(Prefixes.CODE):
            self.submit_current_key_value()
            self.mInInstrumentationResultKey = False
            self.mTestRunFinished = True
        elif line.startswith(Prefixes.TIME_REPORT):
            self.parse_time(line)
        else:
            if self.mCurrentValue is not None:
                self.mCurrentValue += "\r\n" + line
            elif line.strip():
                pass  # Unrecognized line

    def submit_current_key_value(self):
        if self.mCurrentKey is not None and self.mCurrentValue is not None:
            status_value = self.mCurrentValue
            if self.mInInstrumentationResultKey:
                if self.mCurrentKey not in KNOWN_KEYS:
                    self.mInstrumentationResultBundle[self.mCurrentKey] = status_value
                elif self.mCurrentKey == StatusKeys.SHORTMSG:
                    self.handle_test_run_failed(f"Instrumentation run failed due to '{status_value}'")
            else:
                test_info = self.get_current_test_info()
                if self.mCurrentKey == StatusKeys.CLASS:
                    test_info.test_class = status_value.strip()
                elif self.mCurrentKey == StatusKeys.TEST:
                    test_info.test_name = status_value.strip()
                elif self.mCurrentKey == StatusKeys.NUMTESTS:
                    try:
                        test_info.num_tests = int(status_value)
                    except ValueError:
                        pass
                elif self.mCurrentKey == StatusKeys.ERROR:
                    self.handle_test_run_failed(status_value)
                elif self.mCurrentKey == StatusKeys.STACK:
                    test_info.stack_trace = status_value
                elif self.mCurrentKey not in KNOWN_KEYS:
                    self.mTestMetrics[self.mCurrentKey] = status_value
            self.mCurrentKey = None
            self.mCurrentValue = None

    def get_and_reset_test_metrics(self):
        ret_val = self.mTestMetrics
        self.mTestMetrics = {}
        return ret_val

    def get_current_test_info(self):
        if self.mCurrentTestResult is None:
            self.mCurrentTestResult = InstrumentationResultParser.TestResult()
        return self.mCurrentTestResult

    def clear_current_test_info(self):
        self.mLastTestResult = self.mCurrentTestResult
        self.mCurrentTestResult = None

    def parse_key(self, line, key_start_pos):
        end_key_pos = line.find('=', key_start_pos)
        if end_key_pos != -1:
            self.mCurrentKey = line[key_start_pos:end_key_pos].strip()
            self.parse_value(line, end_key_pos + 1)

    def parse_value(self, line, value_start_pos):
        self.mCurrentValue = line[value_start_pos:]

    def parse_status_code(self, line):
        value = line[len(Prefixes.STATUS_CODE):].strip()
        test_info = self.get_current_test_info()
        test_info.code = StatusCodes.ERROR
        try:
            test_info.code = int(value)
        except ValueError:
            test_info.code = StatusCodes.ERROR
        if test_info.code != StatusCodes.IN_PROGRESS:
            self.report_result(test_info)
            self.clear_current_test_info()

    def is_cancelled(self):
        return self.mIsCancelled

    def cancel(self):
        self.mIsCancelled = True

    def report_result(self, test_info):
        if not test_info.is_complete():
            return
        self.report_test_run_started(test_info)
        test_id = TestIdentifier(test_info.test_class, test_info.test_name)
        metrics = None
        if test_info.code == StatusCodes.START:
            for listener in self.mTestListeners:
                listener.test_started(test_id)
        elif test_info.code == StatusCodes.FAILURE:
            metrics = self.get_and_reset_test_metrics()
            for listener in self.mTestListeners:
                listener.test_failed(TestFailure.FAILURE, test_id, self.get_trace(test_info))
                listener.test_ended(test_id, metrics)
            self.mNumTestsRun += 1
        elif test_info.code == StatusCodes.ERROR:
            metrics = self.get_and_reset_test_metrics()
            for listener in self.mTestListeners:
                listener.test_failed(TestFailure.ERROR, test_id, self.get_trace(test_info))
                listener.test_ended(test_id, metrics)
            self.mNumTestsRun += 1
        elif test_info.code == StatusCodes.OK:
            metrics = self.get_and_reset_test_metrics()
            for listener in self.mTestListeners:
                listener.test_ended(test_id, metrics)
            self.mNumTestsRun += 1
        elif test_info.code == StatusCodes.SKIPPED:
            metrics = self.get_and_reset_test_metrics()
            for listener in self.mTestListeners:
                listener.test_skipped(test_id, metrics)
            self.mNumTestsRun += 1
        else:
            metrics = self.get_and_reset_test_metrics()
            for listener in self.mTestListeners:
                listener.test_ended(test_id, metrics)
            self.mNumTestsRun += 1

    def report_test_run_started(self, test_info):
        if not self.mTestStartReported and test_info.num_tests is not None:
            for listener in self.mTestListeners:
                listener.test_run_started(self.mTestRunName, test_info.num_tests)
            self.mNumTestsExpected = test_info.num_tests
            self.mTestStartReported = True

    def get_trace(self, test_info):
        return test_info.stack_trace if test_info.stack_trace else "Unknown failure"

    def parse_time(self, line):
        match = re.search(rf"{Prefixes.TIME_REPORT}\s*([\d\.]+)", line)
        if match:
            try:
                time_seconds = float(match.group(1))
                self.mTestTime = int(time_seconds * 1000)
            except ValueError:
                pass

    def handle_test_run_failed(self, error_msg):
        error_msg = error_msg or "Unknown error"
        if self.mLastTestResult and self.mLastTestResult.is_complete() and self.mLastTestResult.code == StatusCodes.START:
            test_id = TestIdentifier(self.mLastTestResult.test_class, self.mLastTestResult.test_name)
            for listener in self.mTestListeners:
                listener.test_failed(TestFailure.ERROR, test_id,
                                     f"{self.INCOMPLETE_TEST_ERR_MSG_PREFIX}. Reason: '{error_msg}'. {self.INCOMPLETE_TEST_ERR_MSG_POSTFIX}")
                listener.test_ended(test_id, self.get_and_reset_test_metrics())
        for listener in self.mTestListeners:
            if not self.mTestStartReported:
                listener.test_run_started(self.mTestRunName, 0)
            listener.test_run_failed(error_msg)
            listener.test_run_ended(self.mTestTime, self.mInstrumentationResultBundle)
        self.mTestStartReported = True
        self.mTestRunFailReported = True

    def done(self):
        if not self.mTestRunFailReported:
            self.handle_output_done()

    def handle_output_done(self):
        if not self.mTestStartReported and not self.mTestRunFinished:
            self.handle_test_run_failed(self.NO_TEST_RESULTS_MSG)
        elif self.mNumTestsExpected > self.mNumTestsRun:
            message = f"{self.INCOMPLETE_RUN_ERR_MSG_PREFIX}. Expected {self.mNumTestsExpected} tests, received {self.mNumTestsRun}"
            self.handle_test_run_failed(message)
        else:
            for listener in self.mTestListeners:
                if not self.mTestStartReported:
                    listener.test_run_started(self.mTestRunName, 0)
                listener.test_run_ended(self.mTestTime, self.mInstrumentationResultBundle)
