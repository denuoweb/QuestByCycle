# PWA and TWA Setup

This application exposes basic Progressive Web App (PWA) features and can also be deployed as a Trusted Web Activity (TWA) on Android. The following configuration options are available.

## Offline Support
- The file `app/static/offline.html` is served at `/offline.html` when the service worker is registered.
- The PWA manifest at `app/static/manifest.json` is available from `/manifest.json`.
- The manifest enables the `window-controls-overlay` display mode for desktop browsers using `display_override`.
- The service worker is registered from the root path: `/sw.js`.
- When a new version is detected, the user is prompted to reload. Confirming
  sends `SKIP_WAITING` to the service worker so updated assets load immediately.
- Background sync ensures actions performed while offline are sent when
  connectivity returns.
- The manifest includes a `share_target` entry so the site can receive shared
  images and text via the Web Share Target API. Shared data is POSTed to the
  route `/share-target`.
- The manifest sets `handle_links` to `preferred` so links open directly in the
  installed app when possible.
- The manifest includes a `launch_handler` object specifying `"client_mode": "focus-existing"` so that repeated launches reuse the existing window.

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
- The SHA256 fingerprint of your Android signing certificate must be configured in the `.env` file.

### Configuration Keys
- **Environment variable:** `TWA_SHA256_FINGERPRINT`
- **TOML:**
  ```toml
  [twa]
  SHA256_CERT_FINGERPRINT = "YOUR:SHA256:FINGERPRINT"
  ```

The fingerprint will be inserted into the generated `assetlinks.json` response at runtime.

## File Handlers

The manifest supports the `file_handlers` property so the application can register
itself as the default handler for specific file types. By default, the provided
manifest declares support for common image formats. When a user chooses
"Always open with QuestByCycle" for a supported image, the site will launch to
`/` where the uploaded file can be processed.
