from TestResult import TestResult


class TestRunResult:
    def __init__(self, run_name="not started"):
        self._test_run_name = run_name
        self._test_results = {}
        self._run_metrics = {}
        self._is_run_complete = False
        self._elapsed_time = 0
        self._num_failed_tests = 0
        self._num_error_tests = 0
        self._num_passed_tests = 0
        self._num_incomplete_tests = 0
        self._num_skipped_tests = 0
        self._run_failure_error = None

    def get_name(self):
        return self._test_run_name

    def get_test_results(self):
        return self._test_results

    def add_metrics(self, run_metrics, aggregate_metrics):
        for key, value in run_metrics.items():
            if aggregate_metrics and key in self._run_metrics:
                self._run_metrics[key] = self._combine_values(self._run_metrics[key], value)
            else:
                self._run_metrics[key] = value

    @staticmethod
    def _combine_values(existing_value, new_value):
        try:
            return str(int(existing_value) + int(new_value))
        except (ValueError, TypeError):
            pass
        try:
            return str(float(existing_value) + float(new_value))
        except (ValueError, TypeError):
            pass
        return new_value

    def get_run_metrics(self):
        return self._run_metrics

    def get_completed_tests(self):
        return {tid for tid, result in self._test_results.items()
                if result.get_status() != TestResult.TestStatus.INCOMPLETE}

    def is_run_failure(self):
        return self._run_failure_error is not None

    def is_run_complete(self):
        return self._is_run_complete

    def set_run_complete(self, run_complete):
        self._is_run_complete = run_complete

    def add_elapsed_time(self, elapsed_time):
        self._elapsed_time += elapsed_time

    def set_run_failure_error(self, error_message):
        self._run_failure_error = error_message

    def get_num_passed_tests(self):
        return self._num_passed_tests

    def get_num_tests(self):
        return len(self._test_results)

    def get_num_complete_tests(self):
        return self.get_num_tests() - self.get_num_incomplete_tests()

    def get_num_failed_tests(self):
        return self._num_failed_tests

    def get_num_error_tests(self):
        return self._num_error_tests

    def get_num_incomplete_tests(self):
        return self._num_incomplete_tests

    def get_num_skipped_tests(self):
        return self._num_skipped_tests

    def has_failed_tests(self):
        return self.get_num_error_tests() > 0 or self.get_num_failed_tests() > 0

    def get_elapsed_time(self):
        return self._elapsed_time

    def get_run_failure_message(self):
        return self._run_failure_error

    def report_test_started(self, test):
        result = self._test_results.get(test)
        if result:
            status = result.get_status()
            if status == TestResult.TestStatus.ERROR:
                self._num_error_tests -= 1
            elif status == TestResult.TestStatus.FAILURE:
                self._num_failed_tests -= 1
            elif status == TestResult.TestStatus.PASSED:
                self._num_passed_tests -= 1
            elif status == TestResult.TestStatus.SKIPPED:
                self._num_skipped_tests -= 1
        else:
            self._num_incomplete_tests += 1
        self._test_results[test] = TestResult()

    def report_test_failure(self, test, status, trace):
        result = self._test_results.get(test)
        if not result:
            result = TestResult()
            self._test_results[test] = result
        elif result.get_status() == TestResult.TestStatus.PASSED:
            self._num_passed_tests -= 1
        result.set_stack_trace(trace)
        if status == TestResult.TestStatus.ERROR:
            self._num_error_tests += 1
            result.set_status(TestResult.TestStatus.ERROR)
        elif status == TestResult.TestStatus.FAILURE:
            self._num_failed_tests += 1
            result.set_status(TestResult.TestStatus.FAILURE)

    def report_test_ended(self, test, test_metrics):
        result = self._test_results.get(test)
        if not result:
            result = TestResult()
            self._test_results[test] = result
        else:
            self._num_incomplete_tests -= 1
        result.set_end_time()
        result.set_metrics(test_metrics)
        if result.get_status() == TestResult.TestStatus.INCOMPLETE:
            result.set_status(TestResult.TestStatus.PASSED)
            self._num_passed_tests += 1
            return True
        return False

    def report_test_skipped(self, test, test_metrics):
        result = self._test_results.get(test)
        if not result:
            result = TestResult()
            self._test_results[test] = result
        else:
            self._num_incomplete_tests -= 1
        result.set_end_time()
        result.set_metrics(test_metrics)
        if result.get_status() == TestResult.TestStatus.INCOMPLETE:
            result.set_status(TestResult.TestStatus.SKIPPED)
            self._num_skipped_tests += 1

    def get_suite_result(self):
        for result in self._test_results.values():
            status = result.get_status()
            if status != TestResult.TestStatus.PASSED and status != TestResult.TestStatus.SKIPPED:
                return "failing"
        return "passing"
