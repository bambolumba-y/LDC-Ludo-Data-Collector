from src.liquipedia.mediawiki import iter_category_members


class DummyClient:
    def __init__(self):
        self.calls = 0

    def get_json(self, params):
        self.calls += 1
        if self.calls == 1:
            return {
                "query": {"categorymembers": [{"title": "Event 1", "pageid": 1}]},
                "continue": {"cmcontinue": "page|2"},
            }
        return {
            "query": {"categorymembers": [{"title": "Event 2", "pageid": 2}]},
        }


def test_iter_category_members_pagination():
    client = DummyClient()
    members = list(iter_category_members(client, "S-Tier_Tournaments", cmlimit=1))
    assert len(members) == 2
    assert members[0]["title"] == "Event 1"
    assert members[1]["title"] == "Event 2"
