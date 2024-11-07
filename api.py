#api.py
import pytz
from cache_config import cache  # Import cache directly
import requests, json
from datetime import datetime
from config import (HEADERS, NFL_EVENTS_URL, ODDS_URL, SCOREBOARD_URL, SCORING_PLAYS_URL,
                    SCOREBOARD_WEEK_URL, TEAMS_URL, RECORD_URL, DIVISION_URL, PLAYERS_URL)


@cache.memoize(timeout=1800)  # Cache for 30 minutes
def fetch_nfl_events():
    querystring = {"year": "2024"}
    try:
        response = requests.get(NFL_EVENTS_URL, headers=HEADERS, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NFL events: {e}")
        return None


@cache.memoize(timeout=1800)  # Cache for 30 minutes
def fetch_current_odds(week):
    week -= 3
    querystring = {"year":"2024","type":"2","week":week}
    response = requests.get(SCOREBOARD_WEEK_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch games"}


def fetch_odds(game_id):
    querystring = {"id": game_id}
    try:
        response = requests.get(ODDS_URL, headers=HEADERS, params=querystring)
        response.raise_for_status()
        odds_data = response.json()
        for item in odds_data.get('items', []):
            if item.get('provider', {}).get('id') == "58":  # ESPN BET Provider ID
                return item.get('details', 'N/A')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds: {e}")
        return None


def fetch_games_by_day():
    est = pytz.timezone('America/New_York')
    today = datetime.now(est).strftime('%Y%m%d')  # Format the date as 'YYYYMMDD' in EST
    querystring = {"day": today}
    response = requests.get(SCOREBOARD_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch games"}


def fetch_scoring_plays(game_id):
    querystring = {"id": game_id}
    try:
        response = requests.get(SCORING_PLAYS_URL, headers=HEADERS, params=querystring)
        response.raise_for_status()
        return response.json().get('scoringPlays', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching scoring plays: {e}")
        return None


def fetch_teams():
    try:
        response = requests.get(TEAMS_URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NFL teams: {e}")
        return None


def fetch_team_records(team_id):
    querystring = {"id": team_id, "year": "2024"}
    try:
        response = requests.get(RECORD_URL, headers=HEADERS, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team record: {e}")
        return None


def fetch_division(team_id):
    querystring = {"id": team_id, "year": "2024"}
    try:
        response = requests.get(DIVISION_URL, headers=HEADERS, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team division: {e}")
        return None


def fetch_players_by_team(team_id):
    querystring = {"id": team_id}
    try:
        response = requests.get(PLAYERS_URL, headers=HEADERS, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team division: {e}")
        return None


def fetch_bye_teams(week):
    week -= 3
    querystring = {"year": "2024", "type": "2", "week": week}
    response = requests.get(SCOREBOARD_WEEK_URL, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        if response.status_code == 200:
            data = response.json()

            # Check if "teamsOnBye" is present and not empty
            bye_teams = data.get("week", {}).get("teamsOnBye", [])

            if not bye_teams:  # No teams on bye
                return []  # Return an empty list or add a message if preferred

            # Extract name, logo, and color for each team on bye
            teams_on_bye = [
                {
                    "id": team["id"],
                    "name": team["displayName"],
                    "logo": team["logo"],
                }
                for team in bye_teams
            ]
            # Append team color from data/teams.json using team's id
            with open('data/teams.json', 'r') as f:
                teams = json.load(f)
            for team in teams_on_bye:
                team_match = next((t for t in teams if t['id'] == team['id']), None)
                if team_match:
                    team['color'] = team_match['color']
            return teams_on_bye
    return {"error": "Failed to fetch games"}