# Google Fit Integration

The `GoogleFitConnector` retrieves activity metrics from the Google Fit REST API.

## Google Cloud Setup

1. Create a project at [Google Cloud Console](https://console.cloud.google.com).
2. Enable the **Fitness API** for the project.
3. Configure the OAuth consent screen and create OAuth credentials.
4. Request an OAuth access token for the user with these scopes:

   - `https://www.googleapis.com/auth/fitness.activity.read`
   - `https://www.googleapis.com/auth/fitness.heart_rate.read`
   - `https://www.googleapis.com/auth/fitness.sleep.read`

Provide the access token to `GoogleFitConnector` to fetch metrics.
