import requests
from config import HEADERS, NFL_EVENTS_URL, ODDS_URL, SCOREBOARD_URL, SCORING_PLAYS_URL
from datetime import datetime

def fetch_nfl_events():
    querystring = {"year": "2024"}
    response = requests.get(NFL_EVENTS_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch NFL events"}

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
    today = datetime.now().strftime('%Y%m%d')
    querystring = {"day": today}
    response = requests.get(SCOREBOARD_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch games"}

def get_scoring_plays(game_id):
    querystring = {"id": game_id}
    response = requests.get(SCORING_PLAYS_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json().get('scoringPlays', [])
    return {"error": "Failed to fetch scoring plays"}