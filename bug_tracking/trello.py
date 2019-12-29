import requests
import pretty_print

class Trello:

    BASE_URL = "https://api.trello.com/1/"

    def __init__(self, trello_config):
        self.trello_config = trello_config

    def make_trello_task(self, testcase_name, failures):
        pretty_print.status("Creating a trello task for the flaky test {}".format(testcase_name))
        list_id = self._get_list_id()
        standard_desc = "The flaky-test-detector observed the following failures:\n"
        for failure in failures:
            standard_desc += "```\n" + failure + "\n```\n"
        querystring = { "idList":list_id,
                        "keepFromSource":"all",
                        "name":testcase_name + " is flaky",
                        "desc":standard_desc}
        self._call_trello("POST", "/cards", params=querystring)

    def _get_list_id(self):
        board_id = self._get_board_id()
        path = "boards/{}/lists".format(board_id)
        querystring = {"cards":"none",
                       "card_fields":"all",
                       "filter":"open",
                       "fields":"all",
                       }
        board_lists = self._call_trello("GET", path, params=querystring)
        for board_list in board_lists:
            if board_list["name"] == self.trello_config["board_list"]:
                    return board_list["id"]

    def _get_board_id(self):
        querystring = { "filter":"all",
                        "fields":"all",
                        "lists":"none",
                        "memberships":"none",
                        "organization":"false",
                        "organization_fields":"name,displayName",
                    }
        boards =  self._call_trello("GET", "members/me/boards", params=querystring)
        board_id = None
        for board in boards:
            if board["name"] == self.trello_config["board_name"]:
                    return board["id"]

    def _call_trello(self, method_name, path, params={}):
        url = Trello.BASE_URL + path
        params.update({ "key":self.trello_config["api_key"],
                      "token":self.trello_config["access_token"],
                     })
        return requests.request(method_name, url, params=params).json()