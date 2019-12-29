RED = "\033[1;31m"
RESET = "\033[0;0m"
GREEN = "\033[1;32m"
BRIGHT_WHITE = "\033[1;97m"

def failure(input_text):
    print(RED + input_text + RESET)

def status(input_text):
    print(BRIGHT_WHITE + input_text+ RESET)

def success(input_text):
    print(GREEN + input_text + RESET)