import datetime
import os
import socket
import tempfile
import xml.etree.ElementTree as ET
from enum import Enum

from TestResult import TestResult
from TestRunResult import TestRunResult


class TestFailure(Enum):
    ERROR = "ERROR"
    FAILURE = "FAILURE"


class XmlTestRunListener:
    TEST_RESULT_FILE_SUFFIX = ".xml"
    TEST_RESULT_FILE_PREFIX = "test_result_"
    TESTSUITE = "testsuite"
    TESTCASE = "testcase"
    ERROR = "error"
    FAILURE = "failure"
    SKIPPED = "skipped"
    ATTR_NAME = "name"
    ATTR_TIME = "time"
    ATTR_ERRORS = "errors"
    ATTR_FAILURES = "failures"
    ATTR_SKIPPED = "skipped"
    ATTR_TESTS = "tests"
    PROPERTIES = "properties"
    ATTR_CLASSNAME = "classname"
    TIMESTAMP = "timestamp"
    HOSTNAME = "hostname"

    def __init__(self):
        self.mHostName = socket.gethostname()
        self.mReportDir = tempfile.gettempdir()
        self.mReportPath = ""
        self.mRunResult = TestRunResult()

    def set_report_dir(self, path):
        self.mReportDir = path

    def set_host_name(self, host_name):
        self.mHostName = host_name

    def get_run_result(self):
        return self.mRunResult

    def test_run_started(self, run_name, num_tests):
        self.mRunResult = TestRunResult(run_name)

    def test_started(self, test):
        self.mRunResult.report_test_started(test)

    def test_failed(self, status, test, trace):
        if status == TestFailure.ERROR:
            self.mRunResult.report_test_failure(test, TestResult.TestStatus.ERROR, trace)
        else:
            self.mRunResult.report_test_failure(test, TestResult.TestStatus.FAILURE, trace)

    def test_ended(self, test, test_metrics):
        self.mRunResult.report_test_ended(test, test_metrics)

    def test_skipped(self, test, test_metrics):
        self.mRunResult.report_test_skipped(test, test_metrics)

    def test_run_failed(self, error_message):
        self.mRunResult.set_run_failure_error(error_message)

    def test_run_stopped(self, arg0):
        pass

    def test_run_ended(self, elapsed_time, run_metrics):
        self.mRunResult.set_run_complete(True)
        self.generate_document(self.mReportDir, elapsed_time)

    def generate_document(self, report_dir, elapsed_time):
        timestamp = self.get_timestamp()
        report_file = self.get_result_file(report_dir)
        self.mReportPath = report_file
        suite_elem = ET.Element(self.TESTSUITE)
        name = self.get_test_suite_name()
        if name:
            suite_elem.set(self.ATTR_NAME, name)
        suite_elem.set(self.ATTR_TESTS, str(self.mRunResult.get_num_tests()))
        suite_elem.set(self.ATTR_FAILURES, str(self.mRunResult.get_num_failed_tests()))
        suite_elem.set(self.ATTR_ERRORS, str(self.mRunResult.get_num_error_tests()))
        suite_elem.set(self.ATTR_SKIPPED, str(self.mRunResult.get_num_skipped_tests()))
        suite_elem.set(self.ATTR_TIME, str(float(elapsed_time) / 1000.0))
        suite_elem.set(self.TIMESTAMP, timestamp)
        suite_elem.set(self.HOSTNAME, self.mHostName)

        properties_elem = ET.SubElement(suite_elem, self.PROPERTIES)
        self.set_properties_attributes(properties_elem)

        test_results = self.mRunResult.get_test_results()
        for test_id, test_result in test_results.items():
            self.print_test_case(suite_elem, test_id, test_result)

        tree = ET.ElementTree(suite_elem)
        tree.write(report_file, encoding="utf-8", xml_declaration=True)

    def get_absolute_report_path(self):
        return self.mReportPath

    def get_timestamp(self):
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    def get_result_file(self, report_dir):
        fd, path = tempfile.mkstemp(
            prefix=self.TEST_RESULT_FILE_PREFIX,
            suffix=self.TEST_RESULT_FILE_SUFFIX,
            dir=report_dir
        )
        os.close(fd)
        return path

    def get_test_suite_name(self):
        return self.mRunResult.get_name()

    def set_properties_attributes(self, properties_elem):
        pass

    def get_test_name(self, test_id):
        return test_id.get_test_name()

    def print_test_case(self, suite_elem, test_id, test_result):
        case_elem = ET.SubElement(suite_elem, self.TESTCASE)
        case_elem.set(self.ATTR_NAME, self.get_test_name(test_id))
        case_elem.set(self.ATTR_CLASSNAME, test_id.get_class_name())
        elapsed_time_ms = test_result.get_end_time() - test_result.get_start_time()
        case_elem.set(self.ATTR_TIME, str(float(elapsed_time_ms) / 1000.0))

        if test_result.get_status() != TestResult.TestStatus.PASSED:
            if test_result.get_status() == TestResult.TestStatus.FAILURE:
                result_tag = self.FAILURE
            elif test_result.get_status() == TestResult.TestStatus.SKIPPED:
                result_tag = self.SKIPPED
            else:
                result_tag = self.ERROR
            result_elem = ET.SubElement(case_elem, result_tag)
            stack_trace = test_result.get_stack_trace() or ""
            result_elem.text = self.sanitize(stack_trace)

    def sanitize(self, text):
        return text.replace("\0", "<\\0>")
