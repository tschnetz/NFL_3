# callbacks.py
import dash
import json
from dash.dependencies import Input, Output, State, MATCH
from dash import html
import dash_bootstrap_components as dbc
from datetime import datetime, timezone
from utils import load_last_fetched_odds, extract_game_info, create_line_scores, format_line_score, format_game_leaders, format_scoring_play
from api import fetch_nfl_events, fetch_games_by_day, fetch_scoring_plays, fetch_current_odds

last_fetched_odds = load_last_fetched_odds()
initial_api_call_returned_events = True


def register_callbacks(app):
    @app.callback(
        Output('interval-odds', 'n_intervals'),  # Dummy output to trigger the callback
        [Input('interval-odds', 'n_intervals'),
         Input('week-selector', 'value')],  # Trigger on scores update
    )
    def update_odds(n_intervals, week_index):
        try:
            # Fetch new odds data
            new_odds = fetch_current_odds(week_index)

            # Load current odds file
            with open('data/last_fetched_odds.json', 'r') as odds_file:
                last_fetched_odds = json.load(odds_file)

            # Iterate over each game to update odds
            for event in new_odds['events']:
                game_id = event['id']  # Unique game identifier
                # Extract odds information
                if 'odds' in event['competitions'][0]:
                    odds_data = event['competitions'][0]['odds'][0]  # Assume first provider if multiple
                    spread = odds_data.get('details')
                    last_fetched_odds[game_id] = spread

            # Save updated odds back to last_fetched_odds.json
            with open('data/last_fetched_odds.json', 'w') as odds_file:
                json.dump(last_fetched_odds, odds_file, indent=2)

        except Exception as e:
            print(f"Error updating odds: {e}")

        return n_intervals  # Return current interval count to trigger update


    @app.callback(
        Output('week-selector', 'options'),
        Output('week-options-store', 'data'),
        Output('week-selector', 'value'),
        Output('nfl-events-data', 'data'),
        [Input('week-options-store', 'data')],
    )
    def update_week_options(week_options_fetched):
        data = fetch_nfl_events()
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

        if selected_value is None and week_options:
            selected_value = week_options[0]['value']

        return week_options, True, selected_value, data


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
            home_team_extra_info = ""
            away_team_extra_info = ""
            game_headline = game_info['Game Headline']

            if game_status.lower() == "final":
                home_score = game_info['Home Team Score']
                away_score = game_info['Away Team Score']
                quarter_time_display = ""
            else:
                home_score = ""
                away_score = ""
                quarter_time_display = ""

            games_info.append(
                dbc.Button(
                    dbc.Row([
                        dbc.Col(html.Img(src=game_info['Away Team Logo'], height="80px"), width=1,
                                style={'textAlign': 'center'}),
                        dbc.Col(
                            html.Div([
                                html.H4(game_info['Away Team'], style={'color': away_color, 'fontWeight': 'bold'}),
                                html.P(f"{game_info['Away Team Record']}", style={'margin': '0', 'padding': '0'}),
                                html.H3(away_score, id={'type': 'away-score', 'index': game_id},
                                        style={'color': away_color, 'fontWeight': 'bold'}),
                                html.H6(away_team_extra_info, id={'type': 'away-extra', 'index': game_id},
                                        style={'color': away_color}),
                            ], style={'textAlign': 'center'}),
                            width=3,
                        ),
                        dbc.Col(
                            html.Div([
                                # html.H5(game_info['Game Status']),
                                html.H6(game_status, id={'type': 'game-status', 'index': game_id},
                                        style={'fontWeight': 'bold'}),
                                html.H5(quarter_time_display, id={'type': 'quarter-time', 'index': game_id},
                                        style={'fontWeight': 'bold'}),
                                html.H6(game_info['Odds']) if game_info['Odds'] else "",
                                html.P(game_info['Start Date (EST)'], style={'margin': '0', 'padding': '0'}),
                                html.P(f"{game_info['Location']} - {game_info['Network']}",
                                       style={'margin': '0', 'padding': '0'}),
                            ], style={'textAlign': 'center'}),
                            width=4
                        ),
                        dbc.Col(
                            html.Div([
                                html.H4(game_info['Home Team'], style={'color': home_color, 'fontWeight': 'bold'}),
                                html.P(f"{game_info['Home Team Record']}", style={'margin': '0', 'padding': '0'}),
                                html.H3(home_score, id={'type': 'home-score', 'index': game_id},
                                        style={'color': home_color, 'fontWeight': 'bold'}),
                                html.H6(home_team_extra_info, id={'type': 'home-extra', 'index': game_id},
                                        style={'color': home_color}),
                            ], style={'textAlign': 'center'}),
                            width=3
                        ),
                        dbc.Col(html.Img(src=game_info['Home Team Logo'], height="80px"), width=1,
                                style={'textAlign': 'center'}),
                        dbc.Col(
                            html.Div(
                                game_info['Game Headline'],
                                style={
                                    'width': '100%',
                                    'textAlign': 'center',
                                    'fontStyle': 'italic',
                                    'fontSize': '1.0em',
                                    'marginTop': '10px',
                                }
                            ),
                            width=12  # Adjust width as needed
                        ),
                    ], className="game-row", style={'padding': '10px'}),
                    id={'type': 'game-button', 'index': game_id},
                    n_clicks=0,
                    color='medium',
                    className='dash-bootstrap',
                    style={
                        '--team-home-color': home_color,
                        '--team-away-color': away_color,
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
            Output({'type': 'away-extra', 'index': MATCH}, 'children'),
            Output({'type': 'game-status', 'index': MATCH}, 'className')
        ],
        [Input('scores-data', 'data')],
        [State({'type': 'game-button', 'index': MATCH}, 'value')]
    )
    def display_dynamic_game_info(scores_data, game_id):
        game_data = next((game for game in scores_data if game['game_id'] == game_id), None)

        if not game_data:
            html.P("Game data not found.")
            return [dash.no_update] * 6

        game_status = game_data.get('Status', '')
        home_score = game_data.get('Home Team Score', "")
        away_score = game_data.get('Away Team Score', "")
        quarter = game_data.get('Quarter', "")
        time_remaining = game_data.get('Time Remaining', "")
        down_distance = game_data.get('Down Distance', "")
        possession_team = game_data.get('Possession', "")

        home_team_id = game_data.get('Home Team ID')
        away_team_id = game_data.get('Away Team ID')
        home_team_extra_info = "🏈 " + down_distance if possession_team == home_team_id else ""
        away_team_extra_info = "🏈 " + down_distance if possession_team == away_team_id else ""

        quarter_time_display = "Final" if game_status == "final" else f"{quarter} Qtr ● {time_remaining}"

        return home_score, away_score, quarter_time_display, home_team_extra_info, away_team_extra_info, game_status



    @app.callback(
        Output('scores-data', 'data'),
        Output('in-progress-flag', 'data', allow_duplicate=True),
        Output('interval-scores', 'n_intervals'),
        [Input('interval-scores', 'n_intervals'), Input('init-complete', 'data')],
        [State('scores-data', 'data')],
        prevent_initial_call=True
    )
    def update_game_data(n_intervals, init_complete, prev_scores_data):
        global initial_api_call_returned_events

        if not init_complete:
            return dash.no_update, dash.no_update, n_intervals

        if initial_api_call_returned_events is False:
            return dash.no_update, False, n_intervals

        try:
            games_data = fetch_games_by_day()

            if not games_data or not games_data.get('events'):
                initial_api_call_returned_events = False
                return dash.no_update, False, n_intervals

            initial_api_call_returned_events = True
            updated_game_data = []
            games_in_progress = False

            for game in games_data.get('events', []):
                game_id = game.get('id')
                competitions = game.get('competitions', [])

                if not competitions:
                    continue

                status_info = competitions[0].get('status', {})
                game_status = status_info.get('type', {}).get('description', 'N/A')

                if game_status in ["Scheduled", "Final"]:
                    continue
                else:
                    games_in_progress = True

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

                updated_game_data.append({
                    'game_id': game_id,
                    'Status': game_status,
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
                return dash.no_update, games_in_progress, n_intervals
            return updated_game_data, games_in_progress, n_intervals

        except Exception as e:
            return dash.no_update, dash.no_update, n_intervals


    @app.callback(
        Output({'type': 'scoring-plays', 'index': dash.dependencies.ALL}, 'children'),
        [Input({'type': 'game-button', 'index': dash.dependencies.ALL}, 'n_clicks')],
        [State({'type': 'game-button', 'index': dash.dependencies.ALL}, 'id')]
    )
    def display_scoring_plays(n_clicks_list, button_ids):
        # Initialize output with empty lists for each button
        outputs = [[]] * len(n_clicks_list)

        # Identify which button triggered the callback
        ctx = dash.callback_context
        if not ctx.triggered:
            return outputs

        # Get the triggered button's index and n_click count
        triggered_button = ctx.triggered[0]['prop_id'].split('.')[0]
        game_id = json.loads(triggered_button)['index']
        triggered_button_index = next(i for i, btn_id in enumerate(button_ids) if btn_id['index'] == game_id)

        # Check if this is a request to show data (odd n_clicks)
        if n_clicks_list[triggered_button_index] % 2 == 1:
            # Only fetch and format data when displaying
            all_line_scores, nfl_events_data = create_line_scores()
            game_line_scores = all_line_scores.get(game_id, {
                "home_line_scores": [],
                "away_line_scores": []
            })

            scoring_plays = fetch_scoring_plays(game_id)
            game_data = next((event for event in nfl_events_data.get("events", []) if event.get("id") == game_id), None)

            if game_data:
                competition_data = game_data.get("competitions", [{}])[0]
                game_leaders = competition_data.get("leaders", [])
                teams = competition_data.get("competitors", [])
            else:
                game_leaders = []
                teams = []

            home_team = teams[0] if teams[0].get("homeAway") == "home" else teams[1]
            away_team = teams[1] if teams[0].get("homeAway") == "home" else teams[0]

            # Build the formatted display for scoring plays
            formatted_scoring_plays = [
                format_line_score(home_team, away_team, game_line_scores["home_line_scores"],
                                  game_line_scores["away_line_scores"]),
                format_game_leaders(game_leaders),
                format_scoring_play(scoring_plays)
            ]

            # Set the output only for the triggered button's index
            outputs[triggered_button_index] = formatted_scoring_plays

        return outputs

