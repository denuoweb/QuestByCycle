# API

QuestByCycle exposes a small public JSON API documented using OpenAPI.

## Documentation

In non-production environments the API specification can be viewed at `/docs`. The page requires an authenticated user and uses Redoc for a read-only display.

## Specification

The OpenAPI document lives in `docs/openapi.yaml` and describes the following endpoints:

- `GET /games/get_game/{game_id}` – fetch details about a game.
- `GET /games/get_game_points/{game_id}` – retrieve a game's total points and goal.
- `GET /manifest.json` – dynamic PWA manifest.
- `GET /.well-known/assetlinks.json` – Android digital asset links.
