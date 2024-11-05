# pages/players.py

import dash
from layout import roster_layout  # Import main layout for scores

dash.register_page(__name__)

# Define the scores layout
layout = roster_layout