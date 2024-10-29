from cache_config import cache  # Import cache directly
import requests
from datetime import datetime
from config import HEADERS, NFL_EVENTS_URL, ODDS_URL, SCOREBOARD_URL, SCORING_PLAYS_URL


def fetch_nfl_events():
    querystring = {"year": "2024"}
    try:
        print(f"Requesting URL: {NFL_EVENTS_URL}")
        response = requests.get(NFL_EVENTS_URL, headers=HEADERS, params=querystring)
        print(f"Response status code: {response.status_code}")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NFL events: {e}")
        return None

def fetch_espn_bet_odds(game_id):
    querystring = {"id": game_id}
    try:
        print(f"Requesting URL: {ODDS_URL}")
        response = requests.get(ODDS_URL, headers=HEADERS, params=querystring)
        print(f"Response status code: {response.status_code}")
        response.raise_for_status()
        odds_data = response.json()
        for item in odds_data.get('items', []):
            if item.get('provider', {}).get('id') == "58":  # ESPN BET Provider ID
                return item.get('details', 'N/A')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds: {e}")
        return None

def fetch_games_by_day():
    try:
        response = requests.get(SCOREBOARD_URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes

        data = response.json()
        print(f"Full API response: {data}")  # Print the entire JSON response

        if 'error' in data:
            print(f"API Error: {data['error']}")
            # You can potentially extract more error details from the response here
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching games: {e}")
        return None

def get_scoring_plays(game_id):
    querystring = {"id": game_id}
    try:
        print(f"Requesting URL: {SCORING_PLAYS_URL}")
        response = requests.get(SCORING_PLAYS_URL, headers=HEADERS, params=querystring)
        print(f"Response status code: {response.status_code}")
        response.raise_for_status()
        return response.json().get('scoringPlays', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching scoring plays: {e}")
        return None