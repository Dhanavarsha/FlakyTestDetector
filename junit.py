import xml.etree.ElementTree as ET
import os

def extract_test_results(number_of_invocations, test_report_backup):
    test_results = {}
    for i in range(number_of_invocations):
        test_report_dir = test_report_backup + "/" + str(i)
        for filename in  os.listdir(test_report_dir):
            if filename.endswith(".xml"):
                tree = ET.parse(test_report_dir + "/" + filename)
                testsuite = tree.getroot()
                for testCase in testsuite.findall('testcase'):
                    testcase_name = testCase.get('name')
                    testcase_class = testCase.get('classname')
                    full_test_name_key = testcase_class + "." + testcase_name
                    if full_test_name_key not in test_results:
                        test_results[full_test_name_key] = []
                    for child in testCase:
                        if child.tag == "failure":
                            failure_reason = child.get('message')
                            if failure_reason is None:
                                failure_reason = child.text
                            test_results[full_test_name_key].append(failure_reason)
    return test_results
