# Google OAuth Setup

This guide explains how to enable Google OAuth login in QuestByCycle.

## Prerequisites
- A Google Cloud project with the OAuth consent screen configured.
- Client ID and Client Secret for a web application.

## Configuration
1. Set the following environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
2. Ensure the authorized redirect URI in the Google Cloud Console matches:
   ```
   https://<your-domain>/auth/google/callback
   ```

## Usage
After configuration, users can select **Login with Google** from the login modal to authenticate.
