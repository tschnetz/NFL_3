# pages/standings.py

import dash
from layout import standings_layout


dash.register_page(__name__)

# Define the scores layout
layout = standings_layout
