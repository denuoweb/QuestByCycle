# PWA and TWA Setup

This application exposes basic Progressive Web App (PWA) features and can also be deployed as a Trusted Web Activity (TWA) on Android. The following configuration options are available.

## Offline Support
- The file `app/static/offline.html` is served at `/offline.html` when the service worker is registered.
- The PWA manifest at `app/static/manifest.json` is available from `/manifest.json`.
- The service worker is registered from the root path: `/sw.js`.

## Background & Periodic Sync
- The service worker listens for `sync` and `periodicsync` events.
- A tag of `sync-notifications` triggers a refresh of the unread
  notification count when connectivity returns.
- A tag of `periodic-notifications` performs the same refresh at
  regular intervals when supported by the browser.

## Push Notifications
- If the user grants permission, push messages received by the
  service worker display a notification using the app icon.

## TWA Asset Links
- The route `/.well-known/assetlinks.json` dynamically returns the digital asset links used for TWA verification.
- The SHA256 fingerprint of your Android signing certificate must be configured in either `.env` or `config.toml`.

### Configuration Keys
- **Environment variable:** `TWA_SHA256_FINGERPRINT`
- **TOML:**
  ```toml
  [twa]
  SHA256_CERT_FINGERPRINT = "YOUR:SHA256:FINGERPRINT"
  ```

The fingerprint will be inserted into the generated `assetlinks.json` response at runtime.
