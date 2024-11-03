from flask import Flask, redirect, request, session, url_for, render_template_string
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a random secret key for session management

# Strava API credentials (set these in Render's environment or in .env file for local testing)
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")

# Strava API endpoints
AUTHORIZATION_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
ATHLETE_URL = "https://www.strava.com/api/v3/athlete"

# Template for displaying athlete data
athlete_template = """
<!doctype html>
<html lang="en">
  <head>
    <title>Strava Profile</title>
  </head>
  <body>
    <h1>Strava Profile Information</h1>
    {% if athlete %}
      <p><strong>Name:</strong> {{ athlete['firstname'] }} {{ athlete['lastname'] }}</p>
      <p><strong>City:</strong> {{ athlete['city'] }}, {{ athlete['country'] }}</p>
      <p><strong>Weight:</strong> {{ athlete['weight'] }} kg</p>
      <img src="{{ athlete['profile'] }}" alt="Profile Picture" width="100">
    {% else %}
      <p>No athlete data available. Please <a href="{{ url_for('authorize') }}">authorize with Strava</a>.</p>
    {% endif %}
    <p><a href="{{ url_for('logout') }}">Logout</a></p>
  </body>
</html>
"""

@app.route('/')
def index():
    # Check if access token is in the session
    if 'access_token' in session:
        # Fetch athlete profile data
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        response = requests.get(ATHLETE_URL, headers=headers)
        if response.status_code == 200:
            athlete = response.json()
            return render_template_string(athlete_template, athlete=athlete)
        else:
            return "Failed to fetch athlete data. Please try reauthorizing."
    else:
        return render_template_string(athlete_template, athlete=None)

@app.route('/authorize')
def authorize():
    # Redirect to Strava's authorization page
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "read",
    }
    url = AUTHORIZATION_URL + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
    return redirect(url)

@app.route('/callback')
def callback():
    # Get authorization code from Strava
    code = request.args.get("code")
    if not code:
        return "Authorization failed."

    # Exchange the authorization code for an access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_info = response.json()
        session['access_token'] = token_info["access_token"]
        return redirect(url_for('index'))
    else:
        return "Failed to obtain access token."

@app.route('/logout')
def logout():
    # Clear the access token and redirect to the index
    session.pop('access_token', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
