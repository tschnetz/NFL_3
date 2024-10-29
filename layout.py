# layout.py
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from utils import create_standings

# Get the prepared standings data
standings_df = create_standings()
main_layout = dbc.Container([
    dcc.Interval(id='interval-scores', interval=10 * 1000, n_intervals=0),
    dcc.Interval(id='interval-odds', interval=60 * 60 * 1000, n_intervals=0),
    dcc.Store(id='init-complete', data=False),
    dcc.Store(id='in-progress-flag', data=False),
    dcc.Store(id='selected-week', data={'value': None}),
    dcc.Store(id='week-options-store', data=False),
    dcc.Store(id='scores-data', data=[]),
    dcc.Store(id='nfl-events-data', data={}),

    dbc.Row(
        dbc.Col(
            html.Div(
                [
                    html.Img(src="assets/nfl-3644686_1280.webp", height="50px", style={"marginRight": "10px"}),
                    html.H1("NFL Games", style={"display": "inline-block", "verticalAlign": "middle"}),
                ],
                style={"display": "flex", "alignItems": "center", "justifyContent": "center"}
            ),
            width=12,
            className="text-center"
        ),
        style={'marginBottom': '20px'}
    ),

    dbc.Row(dbc.Col(dcc.Dropdown(
        id='week-selector',
        options=[],
        placeholder="Select a week",
        style={
            'padding': '3px',
            'textAlign': 'center',
            'textAlignLast': 'center',
            'fontSize': '20px',
            'color': 'black',
            'alignItems': 'center',
            'justifyContent': 'center'
        },
    ), width=12)),

    dbc.Row(
        dbc.Col(
            dcc.Loading(
                id='loading',
                type='circle',
                children=[html.Div(id='static-game-info'), html.Div(id='dynamic-game-info')]
            ),
            width=12
        )
    ),
], fluid=True)

# Standings layout
standings_layout = dbc.Container([
    html.H1("NFL Standings", style={"textAlign": "center"}),

    # Division tables wrapped in dbc.Card
    *[
        dbc.Card([
            dbc.CardHeader(html.H2(division_df["division_name"].iloc[0], style={"textAlign": "left"})),
            dbc.CardBody([
                html.Table(
                    [html.Tr([
                        html.Th("Team", style={"padding": "5px", "textAlign": "left"}),
                        html.Th("Wins", style={"padding": "5px"}),
                        html.Th("Losses", style={"padding": "5px"}),
                        html.Th("Ties", style={"padding": "5px"}),
                        html.Th("Div. Wins", style={"padding": "5px"}),
                        html.Th("Div. Losses", style={"padding": "5px"}),
                        html.Th("Div. Ties", style={"padding": "5px"}),
                        html.Th("Overall Win %", style={"padding": "5px"}),
                        html.Th("Division Win %", style={"padding": "5px"})
                    ])] +
                    [
                        html.Tr([
                            html.Td(
                                [html.Img(src=row["logo"], style={"height": "30px", "marginRight": "10px"}),
                                 html.Span(row["display_name"], style={"color": row["color"], "fontWeight": "bold"})],
                                style={"display": "flex", "alignItems": "center", "padding": "5px"}
                            ),
                            html.Td(row["wins"], style={"padding": "5px", "textAlign": "center"}),
                            html.Td(row["losses"], style={"padding": "5px", "textAlign": "center"}),
                            html.Td(row["ties"], style={"padding": "5px", "textAlign": "center"}),
                            html.Td(row["division_wins"], style={"padding": "5px", "textAlign": "center"}),
                            html.Td(row["division_losses"], style={"padding": "5px", "textAlign": "center"}),
                            html.Td(row["division_ties"], style={"padding": "5px", "textAlign": "center"}),
                            html.Td(f"{row['overall_win%']:.3f}", style={"padding": "5px", "textAlign": "center"}),
                            html.Td(f"{row['division_win%']:.3f}", style={"padding": "5px", "textAlign": "center"})
                        ])
                        for _, row in division_df.iterrows()
                    ],
                    style={"width": "100%", "borderCollapse": "collapse", "marginTop": "10px"}
                )
            ])
        ], style={
            "marginBottom": "20px",
            "boxShadow": "0px 2px 4px rgba(0, 0, 0, 0.1)",
            "backgroundColor": "rgba(255, 255, 255, 0.8)",  # Light color with opacity for transparency
            "borderRadius": "8px",  # Rounded corners
            "padding": "10px"
        })
        for division_id, division_df in standings_df.groupby("division_id")
    ]
], fluid=True, style={"fontFamily": "Arial, sans-serif", "padding": "20px"})