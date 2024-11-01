# app.py
import dash
import dash_bootstrap_components as dbc
from flask import Flask
from config import PORT
from callbacks import register_callbacks
from cache_config import cache  # Import cache configuration


# Initialize Flask server
server = Flask(__name__)
# Initialize Dash app with Flask server
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], title="NFL Games", use_pages=True)

# Initialize diskcache as the backend for caching
cache.init_app(app.server)
# Configure cache



# Clear cache at the start
with app.server.app_context():
    cache.clear()

# Set up the app layout with navigation and page container
app.layout = dbc.Container([
    dbc.Nav([
        dbc.NavLink(
            "Scores", href="/", active="exact",
            className="nav-link-custom",
        ),
        dbc.NavLink(
            "Standings", href="/standings", active="exact",
            className="nav-link-custom",
        ),
    ], pills=True, style={"margin": "20px 0"}),

    dash.page_container  # Display selected page content
], fluid=True)


# Register callbacks
register_callbacks(app)


# Run Dash server
if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=PORT)