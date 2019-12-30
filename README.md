# FlakyTestDetector
This is a tool that invokes test suite multiple times and detects tests that fail intermittently. Further it creates a Trello card for the flaky tests and creates a Pull Request by marking them '@Ignore'

## Usage:
Clone this repository and execute the file `main.py`. 

```
./main.py --config-file config.yaml
```

config.yaml schema:
```yaml
repository: git@github.com:Dhanavarsha/FlakyTests.git
command:    mvn -f java/pom.xml clean test
testreport: java/target/surefire-reports/
numberOfInvocations: 3

trello:
  api_key: <<trello_api_key>>
  access_token: <<trello_access_token>>
  board_name: Bugs
  board_list: Things To Do

github:
  username: <<github-username>>
  password: <<github-password>>
```


![Screen Recording](https://github.com/Dhanavarsha/FlakyTestDetector/raw/master/images/screen_record.gif)
