#!/usr/local/bin/python3
import yaml
import tempfile
import subprocess
import os
import sys
import time
import xml.etree.ElementTree as ET
from distutils.dir_util import copy_tree
from bug_tracking import trello 

def readconfig(config_file):
    with open(config_file) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        return config

def clone(repo_url, dir_path):
    try:
        subprocess.check_output(["git", "clone", repo_url, dir_path])
        return True
    except subprocess.CalledProcessError as error:
        print("An error occured: \n{}".format(error.output))
        return False

def execute_test(test_command, cwd):
    try:
        subprocess.check_output(test_command, shell=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as error:
        print("An error occured: \n{}".format(error.output))
        return False

def commit_and_push(cwd):
    subprocess.check_output([ "git", "commit", "-am", "Ignoring flaky tests"], cwd=cwd)
    branch_name = "flaky-test-{}".format(str(time.time()))
    subprocess.check_output(["git", "checkout", "-b", branch_name], cwd=cwd)
    subprocess.check_output([ "git", "push", "origin", branch_name], cwd=cwd)

def find_files(classname, working_dir):
    output = subprocess.check_output(["git", "ls-files"], cwd=working_dir).decode(sys.stdout.encoding).strip()
    files = output.split('\n')
    filepaths = list(map(lambda relative_path: os.path.join(working_dir, relative_path), files))
    filtered = list(filter(lambda filepath: classname in filepath, filepaths))
    return filtered

def create_inside_package_function(package_name):
    def inside_package_filter(filepath):
        with open(filepath) as f:
            first_line = f.readline()
            return "package {};".format(package_name) in first_line
    return inside_package_filter
    
def ignore_annotation_string(test_function_string):
    test_function_indentation = len(test_function_string) - len(test_function_string.lstrip())
    string = "@Ignore\n"
    for i in range(test_function_indentation):
        string = " " + string
    return string

def ignore_test(fully_qualified_test_name, working_dir):
    (package_name, class_name, test_name) = fully_qualified_test_name.rsplit('.', 2)
    files = find_files(class_name, working_dir)
    inside_package_lambda = create_inside_package_function(package_name)
    
    test_class_files = list(filter(inside_package_lambda, files))
    assert len(test_class_files) == 1, "Expecting only 1 test-class for class-name: %r" % class_name
    test_class_file = test_class_files[0]    
    with open(test_class_file) as f:
        lines = f.readlines()
    for index in range(len(lines)):
        if "public void {}()".format(test_name) in lines[index]:
            test_function_line_number = index
            break
    assert test_function_line_number != -1, "Test name not present in the file"
    lines.insert(test_function_line_number, ignore_annotation_string(lines[test_function_line_number]))
    with open(test_class_file, "w") as f:
        f.writelines(lines)

def detect_flaky_tests(temp_dir):
    config = readconfig("config.yaml")
    repo_url = config["repository"]
    test_command = config["command"]
    test_report = config["testreport"]
    trello_config = config["trello"]
    number_of_invocations = int(config["numberOfInvocations"])
    clone_dir_path = temp_dir + "/cloned"
    test_report_backup = temp_dir + "/backup"
    clone_success = clone(repo_url, clone_dir_path)
    if clone_success:
        os.mkdir(test_report_backup)
        for i in range(number_of_invocations):
            execute_test(test_command, clone_dir_path)
            toDirectory = test_report_backup + "/" + str(i)
            os.mkdir(toDirectory)
            fromDirectory = clone_dir_path + "/" + test_report
            copy_tree(fromDirectory, toDirectory)

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
        tests_are_flaky = False
        for test in test_results:
            if len(test_results[test]) != number_of_invocations and len(test_results[test]) != 0:
                tests_are_flaky = True
                print("{} is flaky".format(test))
                t = trello.Trello(trello_config)
                t.make_trello_task(test, test_results[test])
                ignore_test(test, clone_dir_path)
        if tests_are_flaky:
            commit_and_push(clone_dir_path)

with tempfile.TemporaryDirectory() as temp_dir:
    detect_flaky_tests(temp_dir)