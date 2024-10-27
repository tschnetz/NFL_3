# callbacks.py
import dash
import json
from dash.dependencies import Input, Output, State, MATCH
from dash import html
import dash_bootstrap_components as dbc
from datetime import datetime, timezone
import requests
from utils import load_last_fetched_odds, extract_game_info

last_fetched_odds = load_last_fetched_odds()

def register_callbacks(app):
    @app.callback(
        Output('week-selector', 'options'),
        Output('week-options-store', 'data'),
        Output('week-selector', 'value'),
        Output('nfl-events-data', 'data'),
        [Input('week-options-store', 'data')],
    )
    def update_week_options(week_options_fetched):
        response = requests.get("http://0.0.0.0:8001/nfl-events")  # Updated port to 8001
        data = response.json() if response.status_code == 200 else {}
        leagues_data = data.get('leagues', [])

        if not leagues_data:
            return [], False, None, {}

        nfl_league = leagues_data[0]
        calendar_data = nfl_league.get('calendar', [])
        week_options = []
        selected_value = None
        current_date = datetime.now(timezone.utc)

        week_counter = 0
        for period in calendar_data:
            if 'entries' in period:
                for week in period['entries']:
                    start_date = datetime.fromisoformat(week['startDate'][:-1]).replace(tzinfo=timezone.utc)
                    end_date = datetime.fromisoformat(week['endDate'][:-1]).replace(tzinfo=timezone.utc)
                    week_label = f"{week['label']}: {start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}"

                    week_options.append({'label': week_label, 'value': week_counter})

                    if start_date <= current_date <= end_date:
                        selected_value = week_counter

                    week_counter += 1

        # if week_options_fetched or not week_options:  # If week options have already been fetched or no options available
        #    return week_options, True, selected_value, data  # Return the fetched data

        if selected_value is None and week_options:
            selected_value = week_options[0]['value']

        return week_options, True, selected_value, data  # Return the fetched data to store it

    @app.callback(
        [Output('static-game-info', 'children'), Output('init-complete', 'data')],
        [Input('nfl-events-data', 'data'), Input('week-selector', 'value')]
    )
    def display_static_game_info(nfl_events_data, selected_week_index):
        if not nfl_events_data:
            return html.P("No NFL events data available.")

        leagues_data = nfl_events_data.get('leagues', [])
        if not leagues_data:
            return html.P("No leagues data available.")

        nfl_league = leagues_data[0]
        calendar_data = nfl_league.get('calendar', [])
        week_data = None
        week_counter = 0

        for period in calendar_data:
            if 'entries' in period:
                for week in period['entries']:
                    if week_counter == selected_week_index:
                        week_data = week
                        break
                    week_counter += 1
            if week_data:
                break

        if not week_data:
            return html.P("Selected week data not found.")

        week_start = datetime.fromisoformat(week_data['startDate'][:-1]).replace(tzinfo=timezone.utc)
        week_end = datetime.fromisoformat(week_data['endDate'][:-1]).replace(tzinfo=timezone.utc)

        events_data = nfl_events_data.get('events', [])
        selected_week_games = [
            event for event in events_data
            if week_start <= datetime.fromisoformat(event['date'][:-1]).replace(tzinfo=timezone.utc) <= week_end
        ]

        sorted_games = sorted(selected_week_games, key=lambda x: (
            x['status']['type']['description'] == 'Final',
            x['status']['type']['description'] == 'Scheduled',
        ))

        games_info = []
        for game in sorted_games:
            game_info = extract_game_info(game, last_fetched_odds)
            game_id = game.get('id')
            home_color = game_info['Home Team Color']
            away_color = game_info['Away Team Color']
            game_status = game_info['Game Status']
            home_id = game_info['Home Team ID']
            away_id = game_info['Away Team ID']

            # Default placeholders for `home_team_extra` and `away_team_extra`
            home_team_extra_info = ""
            away_team_extra_info = ""

            # Set placeholders or final values based on game status
            if game_status.lower() == "final":
                home_score = game_info['Home Team Score']
                away_score = game_info['Away Team Score']
                quarter_time_display = ""
            else:
                home_score = ""
                away_score = ""
                quarter_time_display = ""

            # Construct the game row with appropriate values
            games_info.append(
                dbc.Button(
                    dbc.Row([
                        dbc.Col(html.Img(src=game_info['Home Team Logo'], height="60px"), width=1,
                                style={'textAlign': 'center'}),
                        dbc.Col(
                            html.Div([
                                html.H4(game_info['Home Team'], style={'color': home_color}),
                                html.P(f"{game_info['Home Team Record']}", style={'margin': '0', 'padding': '0'}),
                                html.H3(home_score, id={'type': 'home-score', 'index': game_id},
                                        style={'color': home_color, 'fontWeight': 'bold'}),
                                html.H6(home_team_extra_info, id={'type': 'home-extra', 'index': game_id},
                                        style={'color': home_color}),
                            ], style={'textAlign': 'center'}),
                            width=3
                        ),
                        dbc.Col(
                            html.Div([
                                html.H5(game_info['Game Status']),
                                html.H6(game_info['Odds']) if game_info['Odds'] else "",
                                html.P(game_info['Start Date (EST)'], style={'margin': '0', 'padding': '0'}),
                                html.P(f"{game_info['Location']} - {game_info['Network']}",
                                       style={'margin': '0', 'padding': '0'}),
                                html.H6(quarter_time_display, id={'type': 'quarter-time', 'index': game_id},
                                        style={'fontWeight': 'bold'}),
                            ], style={'textAlign': 'center'}),
                            width=4
                        ),
                        dbc.Col(
                            html.Div([
                                html.H4(game_info['Away Team'], style={'color': away_color}),
                                html.P(f"{game_info['Away Team Record']}", style={'margin': '0', 'padding': '0'}),
                                html.H3(away_score, id={'type': 'away-score', 'index': game_id},
                                        style={'color': away_color, 'fontWeight': 'bold'}),
                                html.H6(away_team_extra_info, id={'type': 'away-extra', 'index': game_id},
                                        style={'color': away_color}),
                            ], style={'textAlign': 'center'}),
                            width=3
                        ),
                        dbc.Col(html.Img(src=game_info['Away Team Logo'], height="60px"), width=1,
                                style={'textAlign': 'center'}),
                    ], className="game-row", style={'padding': '10px'}),
                    id={'type': 'game-button', 'index': game_id},
                    n_clicks=0,
                    color='light',
                    className='dash-bootstrap',
                    style={
                        '--team-home-color': home_color + '50',
                        '--team-away-color': away_color + '50',
                        'width': '100%',
                        'textAlign': 'left'
                    },
                    value=game_id,
                )
            )
            games_info.append(html.Div(id={'type': 'scoring-plays', 'index': game_id}, children=[]))
            games_info.append(html.Hr())

        return games_info, True


    @app.callback(
        [
            Output({'type': 'home-score', 'index': MATCH}, 'children'),
            Output({'type': 'away-score', 'index': MATCH}, 'children'),
            Output({'type': 'quarter-time', 'index': MATCH}, 'children'),
            Output({'type': 'home-extra', 'index': MATCH}, 'children'),
            Output({'type': 'away-extra', 'index': MATCH}, 'children')
        ],
        [Input('scores-data', 'data')],
        [State({'type': 'game-button', 'index': MATCH}, 'value')]
    )
    def display_dynamic_game_info(scores_data, game_id):
        game_data = next((game for game in scores_data if game['game_id'] == game_id), None)

        if not game_data:
            return [dash.no_update] * 5

        # Extract relevant data
        game_status = game_data.get('status', 'In Progress').lower()
        home_score = game_data.get('Home Team Score', "")
        away_score = game_data.get('Away Team Score', "")
        quarter = game_data.get('Quarter', "")
        time_remaining = game_data.get('Time Remaining', "")
        down_distance = game_data.get('Down Distance', "")
        possession_team = game_data.get('Possession', "")

        # Determine possession and extra info
        home_team_id = game_data.get('Home Team ID')
        away_team_id = game_data.get('Away Team ID')
        home_team_extra_info = "🏈 " + down_distance if possession_team == home_team_id else ""
        away_team_extra_info = "🏈 " + down_distance if possession_team == away_team_id else ""

        # Set quarter time display
        quarter_time_display = "Final" if game_status == "final" else f"{quarter} Qtr ● {time_remaining}"

        return home_score, away_score, quarter_time_display, home_team_extra_info, away_team_extra_info


    @app.callback(
        Output('scores-data', 'data'),
        Output('in-progress-flag', 'data', allow_duplicate=True),
        [Input('interval-scores', 'n_intervals'), Input('init-complete', 'data')],
        [State('scores-data', 'data')],
        prevent_initial_call=True
    )
    def update_game_data(n_intervals, init_complete, prev_scores_data):
        if not init_complete:
            return dash.no_update, dash.no_update
        response = requests.get("http://0.0.0.0:8001/nfl-scoreboard-day")  # Updated port to 8001
        games_data = response.json() if response.status_code == 200 else {}

        if not games_data:
            # print("No games data found.")
            return dash.no_update, False

        updated_game_data = []
        games_in_progress = False

        for game in games_data.get('events', []):
            game_id = game.get('id')
            competitions = game.get('competitions', [])

            if not competitions:
                # print(f"No competitions found for game ID {game_id}")
                continue

            status_info = competitions[0].get('status', {})
            game_status = status_info.get('type', {}).get('description', 'N/A')

            # Skip games with status "Scheduled" or "Final"
            if game_status in ["Scheduled", "Final"]:
                continue

            home_team = competitions[0]['competitors'][0]['team']['displayName']
            away_team = competitions[0]['competitors'][1]['team']['displayName']
            home_score = competitions[0]['competitors'][0].get('score', 'N/A')
            away_score = competitions[0]['competitors'][1].get('score', 'N/A')

            home_team_id = competitions[0]['competitors'][0]['team']['id']
            away_team_id = competitions[0]['competitors'][1]['team']['id']
            quarter = '' if game_status == "Final" else status_info.get('period', 'N/A')
            time_remaining = '' if game_status == "Final" else status_info.get('displayClock', 'N/A')

            situation = competitions[0].get('situation', {})
            possession = situation.get('downDistanceText', 'N/A')
            possession_team = situation.get('possession', 'N/A')

            if game_status.lower() == "in progress":
                games_in_progress = True

            updated_game_data.append({
                'game_id': game_id,
                'Home Team ID': home_team_id,
                'Away Team ID': away_team_id,
                'Home Team': home_team,
                'Away Team': away_team,
                'Home Team Score': home_score,
                'Away Team Score': away_score,
                'Quarter': quarter,
                'Time Remaining': time_remaining,
                'Down Distance': possession,
                'Possession': possession_team,
            })

        if prev_scores_data == updated_game_data:
            # print("No updates needed.")
            return dash.no_update, games_in_progress

        # print("Scores updated.")
        return updated_game_data, games_in_progress


    @app.callback(
        Output({'type': 'scoring-plays', 'index': dash.dependencies.ALL}, 'children'),
        [Input({'type': 'game-button', 'index': dash.dependencies.ALL}, 'n_clicks')],
        [State({'type': 'game-button', 'index': dash.dependencies.ALL}, 'id')]
    )
    def display_scoring_plays(n_clicks_list, button_ids):
        ctx = dash.callback_context
        if not ctx.triggered:
            return [[]] * len(n_clicks_list)

        triggered_button = ctx.triggered[0]['prop_id'].split('.')[0]
        game_id = json.loads(triggered_button)['index']

        response = requests.get(f"http://0.0.0.0:8001/nfl-scoringplays?game_id={game_id}")  # Updated port to 8001
        scoring_plays = response.json() if response.status_code == 200 else []

        outputs = []
        for i, button_id in enumerate(button_ids):
            if n_clicks_list[i] % 2 == 1:
                formatted_scoring_plays = []
                for play in scoring_plays:
                    team_logo = play['team'].get('logo', '')
                    period = play.get('period', {}).get('number', '')
                    clock = play.get('clock', {}).get('displayValue', '')
                    text = play.get('text', '')
                    away_score = play.get('awayScore', 'N/A')
                    home_score = play.get('homeScore', 'N/A')

                    formatted_play = html.Div([
                        html.Img(src=team_logo, height="30px", style={'margin-right': '10px'}),
                        html.Span(f"  Q{period} {clock} - {text}"),
                        html.Span(f" {away_score} - {home_score}  ",
                                  style={'margin-left': '10px', 'fontWeight': 'bold'}),
                    ], style={'display': 'flex', 'align-items': 'center'})

                    formatted_scoring_plays.append(formatted_play)

                outputs.append(formatted_scoring_plays)
            else:
                outputs.append([])

        return outputs