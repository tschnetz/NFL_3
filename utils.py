# utils.py
import json
import re
from dash import html
import pandas as pd
import pytz
from collections import defaultdict
import dash_bootstrap_components as dbc
from datetime import datetime, timezone
from config import ODDS_FILE_PATH
from api import fetch_nfl_events, fetch_odds, fetch_division, fetch_team_records, fetch_teams, fetch_players_by_team, \
    fetch_current_odds


# Helper functions
def hex_to_rgba(hex_color, alpha=0.2):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def parse_and_capitalize(name):
    # Split camelCase and capitalize each word
    words = re.sub('([a-z])([A-Z])', r'\1 \2', name).split()
    return ' '.join(word.capitalize() for word in words)


# Odds functions
def save_last_fetched_odds(last_fetched_odds):
    with open(ODDS_FILE_PATH, 'w') as f:
        json.dump(last_fetched_odds, f, indent=2)


def load_last_fetched_odds():
    """Load the last fetched odds from a JSON file."""
    try:
        with open(ODDS_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# API calls and formatting functions
def get_game_odds(game_id, game_status, last_fetched_odds):
    if game_id not in last_fetched_odds:
        # Odds not available in the dictionary, fetch odds regardless of the game status
        odds_data = fetch_odds(game_id)
        last_fetched_odds[game_id] = odds_data  # Store the fetched odds
        save_last_fetched_odds(last_fetched_odds)  # Save to file
        return odds_data
    else:
        # Return the last fetched odds if the game is in progress or final
        return last_fetched_odds[game_id]  # Return last fetched odds if available
    return None  # Return None if no odds are found


def get_unique_divisions(teams_df):
    division_dict = {}

    for _, team in teams_df.iterrows():
        division_data = fetch_division(team["id"])

        division_id = division_data["id"]
        division_name = division_data["name"]
        division_teams = division_data["teams"]

        if division_id not in division_dict:
            division_dict[division_id] = {"division_name": division_name, "teams": []}

        for div_team in division_teams:
            if div_team not in division_dict[division_id]["teams"]:
                division_dict[division_id]["teams"].append(div_team)

    division_records = []
    for division_id, data in division_dict.items():
        for team in data["teams"]:
            division_records.append({
                "division_id": division_id,
                "division_name": data["division_name"],  # Use the specific division name for each entry
                "team_id": team["id"],
            })

    # Save to data/divisions.json
    with open("data/divisions.json", "w") as f:
        json.dump(division_records, f, indent=2)

    return pd.DataFrame(division_records)


def get_records(teams_df):
    # Initialize list to store records for each team
    team_records = []

    for _, team in teams_df.iterrows():
        # Fetch records for the specific team
        records_data = fetch_team_records(team['id'])

        # Ensure records_data is a dictionary and contains the expected "items" key
        if isinstance(records_data, dict) and "items" in records_data:
            for record in records_data["items"]:  # Assuming "items" is a list of individual records
                # Confirm record is a dictionary and has the "name" key
                if isinstance(record, dict) and "name" in record:
                    if record["name"] == "overall":
                        # Extract stats within "overall"
                        wins = next((stat["value"] for stat in record.get("stats", []) if stat.get("name") == "wins"),
                                    0)
                        losses = next(
                            (stat["value"] for stat in record.get("stats", []) if stat.get("name") == "losses"), 0)
                        ties = next((stat["value"] for stat in record.get("stats", []) if stat.get("name") == "ties"),
                                    0)

                    elif record["name"] == "vs. Div.":
                        # Extract stats within "vs. Div."
                        division_wins = next(
                            (stat["value"] for stat in record.get("stats", []) if stat.get("name") == "divisionWins"),
                            0)
                        division_losses = next(
                            (stat["value"] for stat in record.get("stats", []) if stat.get("name") == "divisionLosses"),
                            0)
                        division_ties = next(
                            (stat["value"] for stat in record.get("stats", []) if stat.get("name") == "divisionTies"),
                            0)

            # Append processed data
            team_records.append({
                "id": team["id"],
                "display_name": team["display_name"],
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "division_wins": division_wins,
                "division_losses": division_losses,
                "division_ties": division_ties,
                "color": team["color"],
                "logo": team["logo"],
            })

    # Convert to DataFrame
    # Save to data/records.json
    with open("data/records.json", "w") as f:
        json.dump(team_records, f, indent=2)
    return pd.DataFrame(team_records)


def get_teams():
    teams_data = fetch_teams()
    team_data = [
        {
            "id": team.get("id", None),
            "display_name": team.get("displayName", None),
            "color": team.get("color", None),
            "logo": team.get("logos", [{}])[0].get("href", None)
        }
        for team in teams_data.get("teams", [])
    ]
    # Save to data/teams.json
    with open("data/teams.json", "w") as f:
        json.dump(team_data, f, indent=2)
    return pd.DataFrame(team_data)


def get_game_info(event, last_fetched_odds):
    """Extract all relevant game information from an event."""
    eastern = pytz.timezone("America/New_York")
    event_start_utc = datetime.fromisoformat(event['date'][:-1]).replace(tzinfo=timezone.utc)
    event_start_est = event_start_utc.astimezone(eastern)
    event_start_est_str = event_start_est.strftime('%A, %b %-d @ %-I:%M%p')

    home_team = event['competitions'][0]['competitors'][0]['team']
    away_team = event['competitions'][0]['competitors'][1]['team']

    # Get the game status (e.g., Scheduled, In Progress, Final)
    game_status = event['status']['type']['description']

    # if game_status = 'final', extract headlines.description from competitions
    if game_status.lower() == 'final':
        headlines = event['competitions'][0].get('headlines', [])  # Get headlines, or an empty list if not found
        game_headline = headlines[0].get('shortLinkText') if headlines else None  # Get description if headlines exist
    else:
        game_headline = None


    # Fetch odds based on game status (fetch live odds if scheduled, retain last odds otherwise)
    game_id = event.get('id')
    odds = get_game_odds(game_id, game_status, last_fetched_odds)
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
        'Away Team Record': away_team_record,  # Added away team record
        'Game Headline': game_headline  # Added game headline'
    }


# Game Details creation functions
def create_line_scores():
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
                "away_line_scores": [],
                "home_line_scores": []
            }

            # Loop through teams to classify home and away team scores
            for competition in event.get("competitions", []):
                for competitor in competition.get("competitors", []):
                    team_linescores = [score.get("value") for score in competitor.get("linescores", [])]

                    if competitor.get("homeAway") == "away":
                        linescores_dict[game_id]["away_line_scores"] = team_linescores
                    elif competitor.get("homeAway") == "home":
                        linescores_dict[game_id]["home_line_scores"] = team_linescores

    return linescores_dict, events_data  # Always returns a dictionary, even if empty


def create_standings():
    # Toggle standing_df to rebuild records json files
    # teams_df = pd.read_json("data/teams.json")
    # standings_df = get_records(teams_df)
    standings_df = pd.read_json("data/records.json")
    divisions_df = pd.read_json("data/divisions.json")


    # Merge and clean up columns
    standings_df = standings_df.merge(divisions_df, how='left', left_on='id', right_on='team_id')
    standings_df.drop(columns=['team_id'], inplace=True)

    # Calculate win percentages and sort
    standings_df["overall_win%"] = standings_df["wins"] / (
                standings_df["wins"] + standings_df["losses"] + standings_df["ties"])
    standings_df["division_win%"] = standings_df["division_wins"] / (
                standings_df["division_wins"] + standings_df["division_losses"] + standings_df["division_ties"])
    standings_df = standings_df.sort_values(by=["division_name", "overall_win%", "division_win%"],
                                            ascending=[True, False, False])


    return standings_df


def create_roster_table(team_id):
    # Load team data
    with open('data/teams.json') as f:
        teams_data = json.load(f)

    # Fetch the selected team data
    team_data = next((team for team in teams_data if team["id"] == str(team_id)), None)
    if not team_data:
        return html.Div("Team not found")

    # Set team logo, name, and color
    team_logo = team_data['logo']
    team_name = team_data['display_name']
    team_color = team_data.get("color", "#003f5c")  # Default color if none is provided
    background_color_rgba = hex_to_rgba(team_color, alpha=1.0)

    # Team header (logo and name)
    subheading = dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Img(src=team_logo, height="80px", style={"marginRight": "10px"}),
                html.H2(team_name, style={
                    "display": "inline-block",
                    "verticalAlign": "middle",
                    "marginBottom": "0",
                    "color": "white",  # Text color
                    "fontWeight": "bold",
                    "fontSize": "2.0rem"
                }),
            ], style={
                "backgroundColor": "transparent",
            })
        ])
    ], style={
        "backgroundColor": background_color_rgba,
        "borderRadius": "5px",
        "padding": "5px",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.2)",
        "border": f"2px solid {team_color}",
    })

    # Player data from API
    player_data = fetch_players_by_team(team_id)
    table_rows = []

    # Iterate over each group
    for group in player_data.get("athletes", []):
        group_name = parse_and_capitalize(group.get("position", "Unknown Group"))

       # Group header row
        table_rows.append(html.Tr([
            html.Th(group_name, colSpan=9, className="roster-group-header",
                    style={'textAlign': 'center',
                           "marginBottom": "0",
                    "color": "white",  # Text color
                    "backgroundColor": background_color_rgba,
                    "fontWeight": "bold",
                    "fontSize": "1.5rem"})
        ]))

        # Group players by position within each main group (e.g., Running Back under Offense)
        players_by_position = defaultdict(list)
        for player in group.get("items", []):
            position = player["position"]["displayName"]
            players_by_position[position].append(player)

        # Iterate over positions within each group
        for position, position_players in players_by_position.items():
            # Position subheading
            table_rows.append(html.Tr([
                html.Th(position, colSpan=9, className="roster-position-header")
            ]))

            # Add smaller repeated headers for clarity
            table_rows.append(html.Tr([
                html.Th("", style={"fontSize": "14px", "fontWeight": "normal", "color": "white"}),
                html.Th("Jersey", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"}),
                html.Th("Name", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"}),
                html.Th("Position", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"}),
                html.Th("Height", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"}),
                html.Th("Weight", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"}),
                html.Th("Age", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"}),
                html.Th("College", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"}),
                html.Th("Status", style={"fontSize": "14px", "fontWeight": "normal", "color": "#white"})
            ]))

            # Player rows for each position
            for player in position_players:
                player_row = html.Tr([
                    html.Td(html.Img(src=player.get('headshot', {}).get('href', ''), height="50px",
                                     className="player-photo")),
                    html.Td(player.get("jersey", "N/A")),
                    html.Td(player.get("displayName", "Unknown Name")),
                    html.Td(player["position"].get("displayName", "Unknown Position")),
                    html.Td(player.get("displayHeight", "N/A")),
                    html.Td(player.get("displayWeight", "N/A")),
                    html.Td(player.get("age", "N/A")),
                    html.Td(player.get("college", {}).get("shortName", "N/A")),
                    html.Td(player.get("status", {}).get("type", "N/A")),
                ])
                table_rows.append(player_row)

        # Construct the final layout
    return html.Div([
        subheading,
        html.Table([
            html.Tbody(table_rows)
        ], className="roster-table")
    ])


# Game Details formatting functions
def format_line_score(home_team, away_team, home_line_scores, away_line_scores):
    # Determine the maximum number of quarters to display
    max_quarters = max(len(home_line_scores), len(away_line_scores))

    # Generate the header dynamically based on the number of quarters
    quarter_headers = []
    for i in range(max_quarters):
        if i < 4:  # Standard quarters Q1 to Q4
            quarter_headers.append(html.Th(f"Q{i + 1}", style={'textAlign': 'center', 'textDecoration': 'underline'}))
        else:  # Any quarters beyond Q4 will be labeled as "OT"
            quarter_headers.append(html.Th("OT", style={'textAlign': 'center', 'textDecoration': 'underline'}))

    header_row = html.Tr([
        html.Th("", style={'textDecoration': 'underline'}),  # Empty cell with underline
        html.Th("", style={'textDecoration': 'underline'}),  # Empty cell with underline
        *quarter_headers,
        html.Th("Total", style={'textAlign': 'center', 'textDecoration': 'underline'})
    ])

    team_rows = []
    for team, scores in [(away_team, away_line_scores), (home_team, home_line_scores)]:
        team_logo = team["team"]["logo"]
        team_name = team["team"]["displayName"]
        total_score = sum(scores)

        # Generate the score cells dynamically based on the number of quarters
        score_cells = [html.Td(str(score), style={'textAlign': 'center'}) for score in scores]

        # Add empty cells if the team has fewer quarters than max_quarters (e.g., missing overtime scores)
        score_cells.extend([html.Td("", style={'textAlign': 'center'})] * (max_quarters - len(scores)))

        # Assemble the row for each team
        team_row = html.Tr([
            html.Td(html.Img(src=team_logo, height="50px", style={'marginLeft': '10px'})),
            html.Td(team_name, style={'fontWeight': 'bold', 'font-size': '14'}),
            *score_cells,
            html.Td(str(total_score), style={'fontWeight': 'bold', 'textAlign': 'center'})
        ])
        team_rows.append(team_row)

    # Return the completed table with dynamic headers and rows
    return html.Table([
        html.Thead(header_row),
        html.Tbody(team_rows)
    ], className="section-container", style={
        'width': '50%',  # Specific width for the boxscore section
        'marginLeft': 'auto',  # Center-align the narrower boxscore
        'marginRight': 'auto'
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
    ], className="section-container")  # Applying the CSS class here

    if not formatted_game_leaders.children:
        formatted_game_leaders.children = [html.Div("No leaders data available", style={'color': 'gray'})]

    return formatted_game_leaders


def format_scoring_play(scoring_plays):
    formatted_plays = []
    for play in scoring_plays:
        is_home = play.get("isHome", False)  # Assuming 'isHome' determines home/away status
        # if period = "Q5" change to period = "OT"
        if play.get('period', {}).get('number', '') == 5:
            quarter = "OT"
        else:
            quarter = f"Q{play.get('period', {}).get('number', '')}"

        formatted_plays.append(
            html.Div(
                [
                    # Logo container
                    html.Div(
                        html.Img(src=play['team'].get('logo', ''), height="30px"),
                        className="play-logo-container", style={'order': 1 if is_home else 0}
                    ),

                    # Text container (quarter, time, description)
                    html.Div(
                        f"{quarter} {play.get('clock', {}).get('displayValue', '')} - {play.get('text', '')}",
                        className="play-text", style={'textAlign': 'right' if is_home else 'left', 'flex': '1'}
                    ),

                    # Score container
                    html.Div(
                        f"{play.get('awayScore', 'N/A')} - {play.get('homeScore', 'N/A')}",
                        className="play-score",
                        style={'textAlign': 'right' if is_home else 'left', 'fontWeight': 'bold', 'order': 0 if is_home else 1}
                    ),
                ],
                className=f"scoring-play {'home-play' if is_home else 'away-play'}",
                style={'display': 'flex', 'flexDirection': 'row-reverse' if is_home else 'row', 'alignItems': 'center', 'padding': '5px 0'}
            )
        )

    return html.Div([
        html.H6("Scoring Plays", style={'fontWeight': 'bold', 'paddingBottom': '10px'}),
        *formatted_plays
    ], className="section-container")


# Bye Teams function
def create_bye_teams(week):
    data = fetch_current_odds(week)

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


def update_standings():
    teams_df = pd.read_json("data/teams.json")
    get_records(teams_df)
    return
