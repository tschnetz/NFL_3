# layout.py
from dash import dcc, html
import dash_bootstrap_components as dbc
from utils import create_standings, hex_to_rgba

# Get the prepared standings data
standings_df = create_standings()

# Main layout with styled header and centered dropdown
main_layout = dbc.Container([
    dcc.Interval(id='interval-scores', interval=10 * 1000, n_intervals=0),
    dcc.Interval(id='interval-odds', interval=300 * 1000, n_intervals=0),
    dcc.Store(id='init-complete', data=False),
    dcc.Store(id='in-progress-flag', data=False),
    dcc.Store(id='selected-week', data={'value': None}),
    dcc.Store(id='week-options-store', data=False),
    dcc.Store(id='scores-data', data=[]),
    dcc.Store(id='nfl-events-data', data={}),

    # Header with NFL Logo and Title for Main Layout
    dbc.Card([
        dbc.CardBody(
            html.Div([
                html.Img(src="assets/nfl-3644686_1280.webp", height="50px", style={"marginRight": "15px"}),
                html.H1("NFL Games", style={
                    "display": "inline-block",
                    "verticalAlign": "middle",
                    "color": "white",
                    "padding": "10px 20px",
                    # "backgroundColor": "#1E3A5F",
                    "borderRadius": "8px",
                    "fontSize": "2.5rem",
                    "fontWeight": "bold",
                    "margin": "0"
                })
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
        )
    ], style={
        "backgroundColor": "#1E3A5F",
        "marginBottom": "20px",
        "borderRadius": "8px",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.3)",
        "padding": "10px"
    }),

    dbc.Row(
        dbc.Col(
            dcc.Dropdown(
                id='week-selector',
                options=[],
                placeholder="Select a week",
                style={
                    "width": "100%",
                    "textAlign": "center",
                    "fontSize": "18px",
                    "padding": "3px",
                    "border": "none",
                    "borderRadius": "8px",
                    # "backgroundColor": "#FFFFFF",  # Fully opaque white background
                    "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)",  # Subtle shadow
                }
            ),
            width=6,  # Adjust width as needed
            style={"display": "flex", "justifyContent": "center"}  # Center the dropdown in the column
        ),
        justify="center",
        style={"marginBottom": "20px"}
    ),

    # Game information loading section
    dbc.Row(
        dbc.Col(
            dcc.Loading(
                id='loading',
                type='circle',
                children=[html.Div(id='static-game-info'), html.Div(id='dynamic-game-info')]
            ),
            width=12
        )
    )
], fluid=True)


# Standings layout
# Filter divisions based on AFC or NFC
afc_divisions = standings_df[standings_df["division_name"].str.startswith("AFC")]
nfc_divisions = standings_df[standings_df["division_name"].str.startswith("NFC")]

# Standings layout with AFC and NFC subheadings
standings_layout = dbc.Container([
    # Header with NFL Logo and Title
    dbc.Card([
        dbc.CardBody(
            html.Div([
                html.Img(src="assets/nfl-3644686_1280.webp", height="50px", style={"marginRight": "15px"}),
                html.H1("Current Standings", style={
                    "display": "inline-block",
                    "verticalAlign": "middle",
                    "color": "white",
                    "padding": "10px 20px",
                    # "backgroundColor": "#1E3A5F",
                    "borderRadius": "8px",
                    "fontSize": "2.5rem",
                    "fontWeight": "bold",
                    "margin": "0"
                })
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
        )
    ], style={
        "backgroundColor": "#1E3A5F",
        "marginBottom": "20px",
        "borderRadius": "8px"
    }),

    # AFC Subheading with background and logo
    dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Img(src="/assets/afc.webp", height="40px", style={"marginRight": "10px"}),
                html.H2("AFC", style={"display": "inline-block", "verticalAlign": "middle", "marginBottom": "0"}),
            ], style={"display": "flex", "alignItems": "center", "color": "white"})
        ])
    ], style={
        "backgroundColor": "#003f5c",
        "padding": "10px",
        "marginTop": "20px",
        "marginBottom": "10px",
        "borderRadius": "8px",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.2)"
    }),

    # AFC Division tables
    *[
        dbc.Card([
            dbc.CardHeader(html.H3(division_df["division_name"].iloc[0], style={"textAlign": "left"})),
            dbc.CardBody([
                html.Table(
                    [
                        # Header Row with Overall and Division section headers
                        html.Tr([
                            html.Th(),
                            html.Th("Overall", colSpan="4", style={
                                "textAlign": "center",
                                "fontWeight": "bold",
                                "backgroundColor": "#f0f0f0",
                                "borderTopLeftRadius": "8px",
                                "borderTopRightRadius": "8px",
                                "boxShadow": "0px 2px 4px rgba(0, 0, 0, 0.1)",
                            }),
                            html.Th("Division", colSpan="4", style={
                                "textAlign": "center",
                                "fontWeight": "bold",
                                "backgroundColor": "#e0e0e0",
                                "borderTopLeftRadius": "8px",
                                "borderTopRightRadius": "8px"
                            })
                        ]),
                        # Subheader Row for Overall and Division details
                        html.Tr([
                            html.Th(),
                            html.Th("W", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("L", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("T", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("Win %", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("W", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"}),
                            html.Th("L", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"}),
                            html.Th("T", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"}),
                            html.Th("Win %", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"})
                        ])
                    ] + [
                        html.Tr([
                            html.Td(
                                [html.Img(src=row["logo"], style={"height": "40px", "marginRight": "10px"}),
                                 html.Span(row["display_name"], style={"color": row["color"], "fontWeight": "bold"})],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "padding": "5px",
                                    "backgroundColor": hex_to_rgba(row["color"], alpha=0.2),
                                    "borderRadius": "5px",
                                    "boxShadow": "0px 2px 4px rgba(0, 0, 0, 0.1)",
                                }
                            ),
                            # Overall section with background
                            html.Td(row["wins"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),
                            html.Td(row["losses"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),
                            html.Td(row["ties"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),
                            html.Td(f"{row['overall_win%']:.3f}", style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),

                            # Division section with background
                            html.Td(row["division_wins"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                            html.Td(row["division_losses"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                            html.Td(row["division_ties"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                            html.Td(f"{row['division_win%']:.3f}", style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                        ])
                        for _, row in division_df.iterrows()
                    ],
                    style={"width": "100%", "borderCollapse": "collapse", "marginTop": "10px", "fontSize": "24px"}
                )
            ])
        ], style={
            "marginBottom": "20px",
            "boxShadow": "0px 2px 4px rgba(0, 0, 0, 0.1)",
            "backgroundColor": "rgba(255, 255, 255, 0.8)",
            "borderRadius": "8px",
            "padding": "10px"
        })
        for division_name, division_df in afc_divisions.groupby("division_name")
    ],

    # NFC Subheading with background and logo
    dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Img(src="/assets/nfc.webp", height="40px", style={"marginRight": "10px"}),
                html.H2("NFC", style={"display": "inline-block", "verticalAlign": "middle", "marginBottom": "0"}),
            ], style={"display": "flex", "alignItems": "center", "color": "white"})
        ])
    ], style={
        "backgroundColor": "#2f4b7c",
        "padding": "10px",
        "marginTop": "20px",
        "marginBottom": "10px",
        "borderRadius": "8px",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.2)"
    }),

    # NFC Division tables
    *[
        dbc.Card([
            dbc.CardHeader(html.H3(division_df["division_name"].iloc[0], style={"textAlign": "left"})),
            dbc.CardBody([
                html.Table(
                    [
                        # Header Row with Overall and Division section headers
                        html.Tr([
                            html.Th(),
                            html.Th("Overall", colSpan="4", style={
                                "textAlign": "center",
                                "fontWeight": "bold",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",                                "borderTopLeftRadius": "8px",
                                "borderTopRightRadius": "8px"
                            }),
                            html.Th("Division", colSpan="4", style={
                                "textAlign": "center",
                                "fontWeight": "bold",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                                "borderTopLeftRadius": "8px",
                                "borderTopRightRadius": "8px"
                            })
                        ]),
                        # Subheader Row for Overall and Division details
                        html.Tr([
                            html.Th(),
                            html.Th("W", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("L", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("T", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("Win %", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
                            html.Th("W", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"}),
                            html.Th("L", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"}),
                            html.Th("T", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"}),
                            html.Th("Win %", style={"padding": "5px", "textAlign": "center", "backgroundColor": "#e0e0e0"})
                        ])
                    ] + [
                        html.Tr([
                            html.Td(
                                [html.Img(src=row["logo"], style={"height": "40px", "marginRight": "10px"}),
                                 html.Span(row["display_name"], style={"color": row["color"], "fontWeight": "bold"})],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "padding": "5px",
                                    "backgroundColor": hex_to_rgba(row["color"], alpha=0.2),
                                    "borderRadius": "5px",
                                    "boxShadow": "0px 2px 4px rgba(0, 0, 0, 0.1)",
                                }
                            ),
                            # Overall section with background
                            html.Td(row["wins"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),
                            html.Td(row["losses"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),
                            html.Td(row["ties"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),
                            html.Td(f"{row['overall_win%']:.3f}", style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(220, 220, 220, 0.5)",
                            }),

                            # Division section with background
                            html.Td(row["division_wins"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                            html.Td(row["division_losses"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                            html.Td(row["division_ties"], style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                            html.Td(f"{row['division_win%']:.3f}", style={
                                "padding": "5px",
                                "textAlign": "center",
                                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                            }),
                        ])
                        for _, row in division_df.iterrows()
                    ],
                    style={"width": "100%", "borderCollapse": "collapse", "marginTop": "10px", "fontSize": "24px"}
                )
            ])
        ], style={
            "marginBottom": "20px",
            "boxShadow": "0px 2px 4px rgba(0, 0, 0, 0.1)",
            "backgroundColor": "rgba(255, 255, 255, 0.8)",
            "borderRadius": "8px",
            "padding": "10px"
        })
        for division_name, division_df in nfc_divisions.groupby("division_name")
    ]
], fluid=True, style={"fontFamily": "Arial, sans-serif", "padding": "20px"})

