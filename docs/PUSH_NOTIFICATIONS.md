# Push Notifications

QuestByCycle supports optional Web Push notifications so users can receive updates even when the web app is not open. Notifications are delivered through the browser's Push API and require HTTPS.

## Configuration

1. Generate VAPID keys using the `pywebpush` utility:
   ```bash
   python -m py_vapid generate --mailto you@example.com
   ```
   This prints a public and private key pair.

2. Add the keys to `config.toml` or `.env`:
   ```toml
   [push]
   VAPID_PUBLIC_KEY = "YOUR_PUBLIC_KEY"
   VAPID_PRIVATE_KEY = "YOUR_PRIVATE_KEY"
   VAPID_ADMIN_EMAIL = "you@example.com"
   ```

3. Restart the application so the new configuration is loaded.

## How It Works

- When the site loads, `push.js` registers the service worker and subscribes the browser using the public VAPID key.
- The subscription details are stored in the `push_subscriptions` table.
- A push message can be sent using the `/push/send` endpoint which delivers the payload to all of a user's subscriptions.

## Testing

You can trigger a test notification with:
```bash
curl -X POST /push/send -H 'Content-Type: application/json' \
     -d '{"title": "Hello", "body": "Push works!"}' \
     -b sessioncookie
```
Ensure your browser has granted notification permission to receive the message.
