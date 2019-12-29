#!/usr/local/bin/python3
import argparse
import yaml
import tempfile
import subprocess
import os
import time
import xml.etree.ElementTree as ET
from distutils.dir_util import copy_tree
from bug_tracking import trello 
from ignore_tests import java
from config import Config
import pretty_print

def execute_command(command, cwd=None, failure_message=None):
    shell = isinstance(command, str)
    try:
        subprocess.check_call(command, cwd=cwd, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as error:
        if failure_message:
            pretty_print.failure(failure_message)
        else:
            pretty_print.failure('Command "{}" failed'.format(command))
        return False

def clone(repo_url, dir_path):
    pretty_print.status("Cloning: {} at path: {}".format(repo_url, dir_path))
    return execute_command(["git", "clone", repo_url, dir_path])

def execute_test(test_command, cwd):
    pretty_print.status("Executing test command: {}".format(test_command))
    return execute_command(test_command, cwd=cwd, failure_message="Tests failed")

def commit_and_push(cwd):
    branch_name = "flaky-test-{}".format(str(time.time()))
    pretty_print.status("Pushing changes to branch: {}".format(branch_name))
    execute_command([ "git", "commit", "-am", "Ignoring flaky tests"], cwd=cwd)
    execute_command(["git", "checkout", "-b", branch_name], cwd=cwd)
    execute_command([ "git", "push", "origin", branch_name], cwd=cwd)

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

def detect_flaky_tests(temp_dir, config_file):
    config = Config(config_file)
    number_of_invocations = int(config.numberOfInvocations)
    clone_dir_path = temp_dir + "/cloned"
    test_report_backup = temp_dir + "/backup"
    clone_success = clone(config.repository, clone_dir_path)
    if clone_success:
        os.mkdir(test_report_backup)
        for i in range(number_of_invocations):
            execute_test(config.command, cwd=clone_dir_path)
            toDirectory = test_report_backup + "/" + str(i)
            os.mkdir(toDirectory)
            fromDirectory = clone_dir_path + "/" + config.testreport
            copy_tree(fromDirectory, toDirectory)
        test_results = extract_test_results(number_of_invocations, test_report_backup)
        tests_are_flaky = False
        for test in test_results:
            if len(test_results[test]) != number_of_invocations and len(test_results[test]) != 0:
                tests_are_flaky = True
                pretty_print.success("{} is flaky".format(test))
                t = trello.Trello(config.trello)
                t.make_trello_task(test, test_results[test])
                java.ignore_test(test, clone_dir_path)
        if tests_are_flaky:
            commit_and_push(clone_dir_path)

parser = argparse.ArgumentParser(description='Detects flaky tests')
parser.add_argument("--config-file", help="Provide the config file to use", required=True, type=argparse.FileType('r'))
args = parser.parse_args()
with tempfile.TemporaryDirectory() as temp_dir:
    detect_flaky_tests(temp_dir, args.config_file)