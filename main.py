#!/usr/local/bin/python3
import argparse
import tempfile
from flakyTestDetector import detect_flaky_tests

parser = argparse.ArgumentParser(description='Detects flaky tests')
parser.add_argument("--config-file", help="Provide the config file to use", required=True, type=argparse.FileType('r'))
args = parser.parse_args()
with tempfile.TemporaryDirectory() as temp_dir:
    detect_flaky_tests(temp_dir, args.config_file)