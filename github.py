import requests
import pretty_print
from requests.auth import HTTPBasicAuth

class Github:

    BASE_URL = "https://api.github.com"

    def __init__(self, github_config):
        self.github_config = github_config

    def create_pull_request(self, repository, title, body, branch_name, base_branch):
        url = Github.BASE_URL + "/repos/{}/{}/pulls".format('Dhanavarsha', 'FlakyTests')
        payload = { 'title': title,
                    'body': body,
                    'head': branch_name,
                    'base': base_branch}
        response = requests.post(url,
                                json = payload,
                                auth = HTTPBasicAuth(self.github_config["username"], self.github_config["password"]))
        assert response.status_code == 201, "Pull Request failed for branch : {}".format(branch_name)
        pretty_print.success("Created a PR at url: {}".format(response.json()["html_url"]))