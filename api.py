from cache_config import cache  # Import cache directly
import requests
from datetime import datetime
from config import HEADERS, NFL_EVENTS_URL, ODDS_URL, SCOREBOARD_URL, SCORING_PLAYS_URL


@cache.memoize(timeout=900)  # Cache for 15 mins
def fetch_nfl_events():
    querystring = {"year": "2024"}
    response = requests.get(NFL_EVENTS_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch NFL events"}

# Other functions remain the same
def fetch_espn_bet_odds(game_id):
    querystring = {"id": game_id}
    response = requests.get(ODDS_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        odds_data = response.json()
        for item in odds_data.get('items', []):
            if item.get('provider', {}).get('id') == "58":  # ESPN BET Provider ID
                return item.get('details', 'N/A')
    return {"error": "Failed to fetch odds"}

def fetch_games_by_day():
    response = requests.get(SCOREBOARD_URL, headers=HEADERS)
    print("Response status:", response.status_code)
    print("Response headers:", response.headers)
    print("Response content:", response.text[:500])  # Log first 500 characters of response for inspection

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch games data.")
    return {"error": "Failed to fetch games"}


def get_scoring_plays(game_id):
    querystring = {"id": game_id}
    response = requests.get(SCORING_PLAYS_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json().get('scoringPlays', [])
    return {"error": "Failed to fetch scoring plays"}