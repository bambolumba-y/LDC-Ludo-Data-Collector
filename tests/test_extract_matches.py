from src.liquipedia.extract_matches import extract_matches_from_wikitext


def test_extract_matches_basic():
    wikitext = """
    {{Match|team1=Alpha|team2=Beta|score1=2|score2=1|bestof=3|date=2024-01-01|time=12:00}}
    {{Match2|team1=Gamma|team2=Delta|score1=0|score2=2|bestof=3}}
    """
    matches = extract_matches_from_wikitext(wikitext, "Test Event", "S")
    assert len(matches) == 2
    first = matches[0]
    assert first["team1"] == "Alpha"
    assert first["team2"] == "Beta"
    assert first["score1"] == 2
    assert first["score2"] == 1
    assert first["winner"] == "team1"


def test_best_of_and_winner_logic():
    wikitext = "{{Match|team1=Foo|team2=Bar|score1=1|score2=3|bestof=5}}"
    matches = extract_matches_from_wikitext(wikitext, "Test Event", "A")
    assert matches[0]["best_of"] == 5
    assert matches[0]["winner"] == "team2"
