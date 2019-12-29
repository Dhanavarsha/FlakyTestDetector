import subprocess
import sys
import os

def ignore_test(fully_qualified_test_name, working_dir):
    (package_name, class_name, test_name) = fully_qualified_test_name.rsplit('.', 2)
    files = _find_files(class_name, working_dir)
    inside_package_lambda = _create_inside_package_function(package_name)
    
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
    lines.insert(test_function_line_number, _ignore_annotation_string(lines[test_function_line_number]))
    with open(test_class_file, "w") as f:
        f.writelines(lines)

def _find_files(classname, working_dir):
    output = subprocess.check_output(["git", "ls-files"], cwd=working_dir).decode(sys.stdout.encoding).strip()
    files = output.split('\n')
    filepaths = list(map(lambda relative_path: os.path.join(working_dir, relative_path), files))
    filtered = list(filter(lambda filepath: classname in filepath, filepaths))
    return filtered

def _create_inside_package_function(package_name):
    def inside_package_filter(filepath):
        with open(filepath) as f:
            first_line = f.readline()
            return "package {};".format(package_name) in first_line
    return inside_package_filter
    
def _ignore_annotation_string(test_function_string):
    test_function_indentation = len(test_function_string) - len(test_function_string.lstrip())
    string = "@Ignore\n"
    for i in range(test_function_indentation):
        string = " " + string
    return string