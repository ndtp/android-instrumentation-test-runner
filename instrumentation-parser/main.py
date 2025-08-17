import argparse
import os
import sys

from InstrumentationResultParser import InstrumentationResultParser
from XmlTestRunListener import XmlTestRunListener


class InstrumentationPretty:
    def __init__(self, outputpath):
        self.outputpath = outputpath

    def process_instrumentation_output(self):
        # create test listener and parser
        test_listener = XmlTestRunListener()
        parser = InstrumentationResultParser("Instrumentation results", test_listener)
        if self.outputpath:
            report_dir = self.outputpath
        else:
            report_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(report_dir, exist_ok=True)
        test_listener.set_report_dir(report_dir)
        lines = [line.rstrip('\n') for line in sys.stdin]
        parser.process_new_lines(lines)
        parser.done()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InstrumentationPretty")
    parser.add_argument("-o", "--output", help="output file path", required=False)
    args = parser.parse_args()
    output_file_path = args.output if args.output else ""
    try:
        InstrumentationPretty(output_file_path).process_instrumentation_output()
    except Exception as e:
        print(e)
