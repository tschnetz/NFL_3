from cache_config import cache  # Import cache directly
import requests
from datetime import datetime
from config import (HEADERS, NFL_EVENTS_URL, ODDS_URL, SCOREBOARD_URL,
                    SCORING_PLAYS_URL, TEAMS_URL, RECORD_URL, DIVISION_URL)


@cache.memoize(timeout=1800)  # Cache for 30 minutes
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


@cache.memoize(timeout=1800)  # Cache for 30 minutes
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
    today = datetime.now().strftime('%Y%m%d')
    querystring = {"day": today}
    response = requests.get(SCOREBOARD_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch games"}


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


def fetch_teams():
    try:
        print(f"Requesting URL: {TEAMS_URL}")
        response = requests.get(TEAMS_URL, headers=HEADERS)
        print(f"Response status code: {response.status_code}")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NFL teams: {e}")
        return None


def fetch_team_records(team_id):
    querystring = {"id": team_id, "year": "2024"}
    try:
        print(f"Requesting URL: {RECORD_URL}")
        response = requests.get(RECORD_URL, headers=HEADERS, params=querystring)
        print(f"Response status code: {response.status_code}")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team record: {e}")
        return None


def fetch_division(team_id):
    querystring = {"id": team_id, "year": "2024"}
    try:
        print(f"Requesting URL: {DIVISION_URL}")
        response = requests.get(DIVISION_URL, headers=HEADERS, params=querystring)
        print(f"Response status code: {response.status_code}")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team division: {e}")
        return None
