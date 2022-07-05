import argparse

import requests
import unittest
from xml.dom.minidom import parseString


class Main:
    def __init__(self):
        self.user_name_cache = {}
        self.game_name_cache = {}

    def get_url(self, user_id):
        if user_id.isnumeric():
            return f"https://steamcommunity.com/profiles/{user_id}/games/?tab=all&xml=1"
        return f"https://steamcommunity.com/id/{user_id}/games?tab=all&xml=1"

    def send_xml_request(self, url):
        return requests.get(url).content.decode()

    def parse_xml(self, xml):
        xml_dict = {"games": {}}
        dom_tree = parseString(xml)
        games_list_tag = dom_tree.documentElement
        xml_dict["steamID64"] = self.get_element_text(games_list_tag, "steamID64")
        xml_dict["steamID"] = self.get_element_text(games_list_tag, "steamID")
        games = games_list_tag.getElementsByTagName("games")[0].getElementsByTagName("game")
        for game in games:
            # print("*****Game*****")
            # self.print_element_text(game, "name")
            # self.print_element_text(game, "hoursOnRecord")
            xml_dict["games"][self.get_element_text(game, "appID")] = {
                "name": self.get_element_text(game, "name"),
                "hoursOnRecord": self.get_element_text(game, "hoursOnRecord")
            }
        self.cache_user_name(xml_dict)
        self.cache_game_names(xml_dict["games"])
        return xml_dict

    def print_element_text(self, parent_element, tag):
        print(f"{tag}: {self.get_element_text(parent_element, tag)}")

    @staticmethod
    def get_element_text(parent_element, tag_name):
        element = parent_element.getElementsByTagName(tag_name)
        if len(element) > 0:
            return element[0].childNodes[0].data
        return ""

    @staticmethod
    def compare_games(users):
        games = {}
        for user in users:
            user_id = user["steamID64"]
            for game in user["games"]:
                if game in games:
                    games[game].append(user_id)
                else:
                    games[game] = [user_id]
        return games

    @staticmethod
    def sort_compare_dict(compare_dict):
        return dict(sorted(compare_dict.items(), key=lambda x: len(x[1]), reverse=True))

    @staticmethod
    def remove_games_with_only_one_owner(compare_dict):
        return {key: value for key, value in compare_dict.items() if len(value) > 1}

    def cache_user_name(self, user):
        self.user_name_cache[user["steamID64"]] = user["steamID"]

    def cache_game_names(self, games):
        for game in games.keys():
            if game not in self.game_name_cache:
                self.game_name_cache[game] = games[game]["name"]

    def get_user_name(self, user_id):
        return self.user_name_cache[user_id]

    def get_game_name(self, app_id):
        return self.game_name_cache[app_id]

    def format_compare_dict(self, compare_dict):
        prepped_dict = self.sort_compare_dict(self.remove_games_with_only_one_owner(compare_dict))
        output = ""
        for game, users in prepped_dict.items():
            output += f"{self.get_game_name(game)}: {[self.get_user_name(user) for user in users]}\n"
        return output[:-1]


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cut = Main()

    def test_parse_xml(self):
        expected = {"steamID64": "76561198025674497",
                    "steamID": "EpicWolverine",
                    "games": {
                        "976730": {"name": "Halo: The Master Chief Collection", "hoursOnRecord": "388"},
                        "296910": {"name": "8BitBoy", "hoursOnRecord": ""}
                    }}
        with open("test_games.xml", 'r') as xml_file:
            self.assertEqual(expected, self.cut.parse_xml(''.join(xml_file.readlines())))

    def test_get_url(self):
        self.assertEqual("https://steamcommunity.com/id/EpicWolverine/games?tab=all&xml=1",
                         self.cut.get_url("EpicWolverine"))
        self.assertEqual("https://steamcommunity.com/profiles/76561198083108093/games/?tab=all&xml=1",
                         self.cut.get_url("76561198083108093"))

    def test_send_xml_request(self):
        response = self.cut.send_xml_request(self.cut.get_url("76561198083108093"))
        expected = r"""<\?xml version="1.0" encoding="UTF-8" standalone="yes"\?><gamesList>
	<steamID64>76561198083108093</steamID64>
	<steamID><!\[CDATA\[EpicNovaSatori]]></steamID>
	<games>
		<game>
			<appID>440</appID>
			<name><!\[CDATA\[Team Fortress 2]]></name>
			<logo><!\[CDATA\[https://cdn.\w*.steamstatic.com/steam/apps/440/capsule_184x69.jpg]]></logo>
			<storeLink><!\[CDATA\[https://steamcommunity.com/app/440]]></storeLink>
			<hoursOnRecord>1.1</hoursOnRecord>
			<statsLink><!\[CDATA\[https://steamcommunity.com/profiles/76561198083108093/stats/TF2]]></statsLink>
			<globalStatsLink><!\[CDATA\[https://steamcommunity.com/stats/TF2/achievements/]]></globalStatsLink>
		</game>
	</games>
</gamesList>
""".replace("\n", "\r\n")
        self.assertRegex(response, expected)

    def test_compare_lists(self):
        user1 = {"steamID64": "76561198025674497",
                 "games": {"976730": {"name": "Halo: The Master Chief Collection", "hoursOnRecord": "388"},
                           "296910": {"name": "8BitBoy", "hoursOnRecord": ""}}
                 }
        user2 = {"steamID64": "76561198083108093",
                 "games": {"976730": {"name": "Halo: The Master Chief Collection", "hoursOnRecord": "3"},
                           "440": {"name": "Team Fortress 2", "hoursOnRecord": "1.1"}}
                 }
        user3 = {"steamID64": "1234",
                 "games": {"976730": {"name": "Halo: The Master Chief Collection", "hoursOnRecord": "3"},
                           "440": {"name": "Team Fortress 2", "hoursOnRecord": "1.1"}}
                 }
        expected = {"976730": ["76561198025674497", "76561198083108093", "1234"],
                    "296910": ["76561198025674497"],
                    "440": ["76561198083108093", "1234"]}
        self.assertEqual(expected, self.cut.compare_games([user1, user2, user3]))

    def test_sort_dict_by_value_length(self):
        compare_dict = {"441": ["76561198083108093", "1234"],
                        "976730": ["76561198025674497", "76561198083108093", "1234"],
                        "296910": ["76561198025674497"],
                        "440": ["76561198083108093", "1234"]}
        expected = {"976730": ["76561198025674497", "76561198083108093", "1234"],
                    "440": ["76561198083108093", "1234"],
                    "441": ["76561198083108093", "1234"],
                    "296910": ["76561198025674497"]}
        self.assertEqual(expected, self.cut.sort_compare_dict(compare_dict))

    def test_remove_from_dict_values_of_length_1(self):
        compare_dict = {"441": ["76561198083108093", "1234"],
                        "976730": ["76561198025674497", "76561198083108093", "1234"],
                        "296910": ["76561198025674497"],
                        "440": ["76561198083108093", "1234"]}
        expected = {"441": ["76561198083108093", "1234"],
                    "976730": ["76561198025674497", "76561198083108093", "1234"],
                    "440": ["76561198083108093", "1234"]}
        self.assertEqual(expected, self.cut.remove_games_with_only_one_owner(compare_dict))

    def test_cache_game_names(self):
        user1 = {"steamID64": "76561198025674497",
                 "games": {"976730": {"name": "Halo: The Master Chief Collection", "hoursOnRecord": "388"},
                           "296910": {"name": "8BitBoy", "hoursOnRecord": ""}}
                 }
        user2 = {"steamID64": "76561198083108093",
                 "games": {"976730": {"name": "Halo: The Master Chief Collection", "hoursOnRecord": "3"},
                           "440": {"name": "Team Fortress 2", "hoursOnRecord": "1.1"}}
                 }
        expected = {"976730": "Halo: The Master Chief Collection",
                    "296910": "8BitBoy",
                    "440": "Team Fortress 2"}
        self.cut.cache_game_names(user1["games"])
        self.cut.cache_game_names(user2["games"])
        self.assertEqual(expected, self.cut.game_name_cache)

    def test_cache_user_name(self):
        user1 = {"steamID64": "76561198025674497",
                 "steamID": "EpicWolverine"}
        user2 = {"steamID64": "76561198083108093",
                 "steamID": "EpicNovaSatori"}
        expected = {"76561198025674497": "EpicWolverine",
                    "76561198083108093": "EpicNovaSatori"}
        self.cut.cache_user_name(user1)
        self.cut.cache_user_name(user2)
        self.assertEqual(expected, self.cut.user_name_cache)

    def test_format_compare_dict(self):
        self.cut.user_name_cache = {"76561198025674497": "EpicWolverine", "76561198083108093": "EpicNovaSatori"}
        self.cut.game_name_cache = {"976730": "Halo: The Master Chief Collection", "296910": "8BitBoy", "440": "Team Fortress 2"}
        compare_dict = {"976730": ["76561198025674497", "76561198083108093"],
                        "296910": ["76561198025674497"],
                        "440": ["76561198083108093"]}
        expected = "Halo: The Master Chief Collection: ['EpicWolverine', 'EpicNovaSatori']"
        self.assertEqual(expected, self.cut.format_compare_dict(compare_dict))


if __name__ == '__main__':
    main = Main()
    parser = argparse.ArgumentParser(description="Compare Steam libraries")
    parser.add_argument("user_ids", metavar='user_id', nargs='+',
                        help="list of Steam User IDs")
    args = parser.parse_args()

    users = []
    for user_id in args.user_ids:
        users.append(main.parse_xml(main.send_xml_request(main.get_url(user_id))))
    print(main.format_compare_dict(main.compare_games(users)))
