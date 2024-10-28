# utils.py
import json
from dash import dcc, html
import requests
import pytz
from datetime import datetime, timezone
from config import HEADERS, ODDS_URL, ODDS_FILE_PATH
from api import fetch_nfl_events, fetch_games_by_day


def save_last_fetched_odds(last_fetched_odds):
    """Save the last fetched odds to a JSON file."""
    with open(ODDS_FILE_PATH, 'w') as f:
        json.dump(last_fetched_odds, f)

def load_last_fetched_odds():
    """Load the last fetched odds from a JSON file."""
    try:
        with open(ODDS_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def fetch_espn_bet_odds(game_id, game_status, last_fetched_odds):
    """Fetch ESPN BET odds based on game status."""
    if game_status == 'Scheduled':
        # print(f"Fetching ESPN BET odds for scheduled game ID: {game_id}")
        querystring = {"id": game_id}
        response = requests.get(ODDS_URL, headers=HEADERS, params=querystring)
        odds_data = response.json()

        for item in odds_data.get('items', []):
            if item.get('provider', {}).get('id') == "58":  # ESPN BET Provider ID
                last_fetched_odds[game_id] = item.get('details', 'N/A')  # Store the fetched odds
                save_last_fetched_odds(last_fetched_odds)  # Save to file
                return item.get('details', 'N/A')
    elif game_id not in last_fetched_odds:
        # Odds not available in the dictionary, fetch odds regardless of the game status
        # print(f"Fetching ESPN BET odds for game ID: {game_id} as it is not in last fetched odds.")
        querystring = {"id": game_id}
        response = requests.get(ODDS_URL, headers=HEADERS, params=querystring)
        odds_data = response.json()

        for item in odds_data.get('items', []):
            if item.get('provider', {}).get('id') == "58":  # ESPN BET Provider ID
                last_fetched_odds[game_id] = item.get('details', 'N/A')  # Store the fetched odds
                save_last_fetched_odds()  # Save to file
                return item.get('details', 'N/A')
    else:
        # Return the last fetched odds if the game is in progress or final
        # print(f"Returning last fetched odds for game ID: {game_id}")
        return last_fetched_odds[game_id]  # Return last fetched odds if available

    return None  # Return None if no odds are found


def extract_game_info(event, last_fetched_odds):
    """Extract all relevant game information from an event."""
    eastern = pytz.timezone("America/New_York")
    event_start_utc = datetime.fromisoformat(event['date'][:-1]).replace(tzinfo=timezone.utc)
    event_start_est = event_start_utc.astimezone(eastern)
    event_start_est_str = event_start_est.strftime('%A, %b %-d @ %-I:%M%p')

    home_team = event['competitions'][0]['competitors'][0]['team']
    away_team = event['competitions'][0]['competitors'][1]['team']

    # Get the game status (e.g., Scheduled, In Progress, Final)
    game_status = event['status']['type']['description']

    # Fetch odds based on game status (fetch live odds if scheduled, retain last odds otherwise)
    game_id = event.get('id')
    odds = fetch_espn_bet_odds(game_id, game_status, last_fetched_odds)

    # Extract overall records from the statistics
    home_team_record = event['competitions'][0]['competitors'][0]['records'][0]['summary']
    away_team_record = event['competitions'][0]['competitors'][1]['records'][0]['summary']

    return {
        'Home Team': home_team['displayName'],
        'Away Team': away_team['displayName'],
        'Home Team ID': home_team['id'],
        'Away Team ID': away_team['id'],
        'Home Team Score': event['competitions'][0]['competitors'][0].get('score', 'N/A'),
        'Away Team Score': event['competitions'][0]['competitors'][1].get('score', 'N/A'),
        'Odds': odds,
        'Home Team Logo': home_team.get('logo'),
        'Away Team Logo': away_team.get('logo'),
        'Home Team Abbreviation': home_team.get('abbreviation'),
        'Away Team Abbreviation': away_team.get('abbreviation'),
        'Home Team Color': f"#{home_team.get('color', '000000')}",
        'Away Team Color': f"#{away_team.get('color', '000000')}",
        'Venue': event['competitions'][0]['venue']['fullName'],
        'Location': f"{event['competitions'][0]['venue']['address']['city']}",
        'Network': event['competitions'][0].get('broadcast', 'N/A'),  # Include the broadcast network
        'Game Status': game_status,
        'Start Date (EST)': event_start_est_str,
        'Quarter': event.get('status', {}).get('period', None),
        'Time Remaining': event.get('status', {}).get('displayClock', None),
        'Home Team Record': home_team_record,  # Added home team record
        'Away Team Record': away_team_record  # Added away team record
    }


def line_scores():
    # Retrieve the cached NFL events data
    events_data = fetch_nfl_events()

    # Initialize dictionary to store linescores by game_id
    linescores_dict = {}

    if not events_data:  # Check if events_data is None or empty
        return linescores_dict  # Return an empty dictionary if no data is available

    # Extract linescores information from each event
    for event in events_data.get("events", []):
        game_id = event.get("id")
        game_status = event.get("status", {}).get("type", {}).get("description", "").lower()
        season_type = event.get("season", {}).get("type")

        # Only include regular season games with a final status
        if season_type == 2 and game_status == "final":  # Regular season and completed games only
            linescores_dict[game_id] = {
                "home_line_scores": [],
                "away_line_scores": []
            }

            # Loop through teams to classify home and away team scores
            for competition in event.get("competitions", []):
                for competitor in competition.get("competitors", []):
                    team_linescores = [score.get("value") for score in competitor.get("linescores", [])]

                    if competitor.get("homeAway") == "home":
                        linescores_dict[game_id]["home_line_scores"] = team_linescores
                    elif competitor.get("homeAway") == "away":
                        linescores_dict[game_id]["away_line_scores"] = team_linescores

    return linescores_dict  # Always returns a dictionary, even if empty

def format_line_score(home_team, away_team, home_line_scores, away_line_scores):
    team_rows = []
    for team, scores in [(home_team, home_line_scores), (away_team, away_line_scores)]:
        team_logo = team["team"]["logo"]
        team_name = team["team"]["displayName"]
        total_score = sum(scores)

        team_row = html.Tr([
            html.Td(html.Img(src=team_logo, height="30px")),
            html.Td(team_name),
            *[html.Td(str(score), style={'textAlign': 'right'}) for score in scores],
            html.Td(str(total_score), style={'fontWeight': 'bold', 'textAlign': 'center'})
        ])
        team_rows.append(team_row)

    return html.Table([
        html.Thead(html.Tr([
            html.Th(""), html.Th(""),
            html.Th("Q1", style={'textAlign': 'right'}), html.Th("Q2", style={'textAlign': 'right'}),
            html.Th("Q3", style={'textAlign': 'right'}), html.Th("Q4", style={'textAlign': 'right'}),
            html.Th("Total", style={'textAlign': 'center'})
        ])),
        html.Tbody(team_rows)
    ], style={
        'width': '100%', 'borderCollapse': 'collapse', 'backgroundColor': 'rgba(255, 255, 255, 0.5)',
        'borderRadius': '8px', 'padding': '10px', 'marginBottom': '20px'
    })

def format_game_leaders(game_leaders):
    formatted_game_leaders = html.Div([
        html.H6("Game Leaders", style={'fontWeight': 'bold', 'paddingBottom': '10px'}),
        *[
            html.Div([
                html.Img(src=player['athlete']['headshot'], height="30px", style={'marginRight': '10px'}),
                html.Span(
                    f"{leader['displayName']} - {player['athlete']['displayName']} ({player['displayValue']})")
            ], style={'display': 'flex', 'alignItems': 'center', 'padding': '5px 0'})
            for leader in game_leaders for player in leader.get('leaders', [])
        ]
    ], style={
        'backgroundColor': 'rgba(255, 255, 255, 0.3)', 'borderRadius': '8px',
        'padding': '10px', 'boxShadow': '0px 2px 4px rgba(0, 0, 0, 0.1)'
    })

    if not formatted_game_leaders.children:
        formatted_game_leaders.children = [html.Div("No leaders data available", style={'color': 'gray'})]

    return formatted_game_leaders


def format_scoring_play(scoring_plays):
    """
    Takes a list of scoring plays and returns a styled Div with the title "Scoring Plays"
    and a formatted list of individual play elements.
    """
    # Format each play as a separate Div element
    formatted_plays = [
        html.Div([
            html.Img(src=play['team'].get('logo', ''), height="30px", style={'marginRight': '10px'}),
            html.Span(f"Q{play.get('period', {}).get('number', '')} {play.get('clock', {}).get('displayValue', '')} - {play.get('text', '')}"),
            html.Span(f"{play.get('awayScore', 'N/A')} - {play.get('homeScore', 'N/A')}",
                      style={'marginLeft': '10px', 'fontWeight': 'bold'})
        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '5px 0'})
        for play in scoring_plays
    ]

    # Wrap all plays in a Div with a title and background styling
    return html.Div([
        html.H6("Scoring Plays", style={'fontWeight': 'bold', 'paddingBottom': '10px'}),
        *formatted_plays  # Unpack the list of individual formatted plays
    ], style={
        'backgroundColor': 'rgba(255, 255, 255, 0.3)',  # Transparent background
        'borderRadius': '8px',
        'padding': '10px',
        'marginBottom': '20px',
        'boxShadow': '0px 2px 4px rgba(0, 0, 0, 0.1)'
    })