# DEVELOPER.md

Welcome to the Developer Guide for our Ultimate Challenge and Reward Platform! This document will provide you with an in-depth understanding of the architecture, codebase, and development practices. Whether you're adding new features, fixing bugs, or maintaining the system, this guide will help you navigate the code and understand its intricacies.

## Table of Contents

1. [Project Structure](#project-structure)
    - [Directory Overview](#directory-overview)
    - [Important Files](#important-files)
2. [Setting Up the Development Environment](#setting-up-the-development-environment)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
3. [Key Components](#key-components)
    - [Flask Blueprints](#flask-blueprints)
    - [Database Models](#database-models)
    - [Forms](#forms)
    - [Utilities](#utilities)
4. [Admin Functionality](#admin-functionality)
    - [Admin Dashboard](#admin-dashboard)
    - [Badge Management](#badge-management)
    - [Quest Management](#quest-management)
    - [Shout Board](#shout-board)
5. [User Functionality](#user-functionality)
    - [Quest Submission](#quest-submission)
    - [Profile Management](#profile-management)
    - [Social Media Integration](#social-media-integration)
6. [AI Quest Generation](#ai-quest-generation)
7. [Static Assets](#static-assets)
    - [CSS](#css)
    - [JavaScript](#javascript)
    - [Images and Videos](#images-and-videos)
8. [Testing and Debugging](#testing-and-debugging)
    - [Running Tests](#running-tests)
    - [Debugging](#debugging)
9. [Deployment](#deployment)
    - [Production Configuration](#production-configuration)
    - [Deployment Steps](#deployment-steps)

## Project Structure

### Directory Overview

The project is organized as follows:

- `app/`: The main application directory.
  - `static/`: Contains static assets like CSS, JavaScript, images, and fonts.
    - `css/`: Stylesheets.
    - `js/`: JavaScript files.
    - `qr_codes/`: QR code images.
    - `videos/`: Video files.
    - `webfonts/`: Font files.
  - `templates/`: Contains HTML templates for rendering views.
    - `modals/`: Templates for modal dialogs.
  - `__init__.py`: Initializes the Flask application.
  - `admin.py`: Admin-specific routes and logic.
  - `ai.py`: AI quest generation logic.
  - `auth.py`: Authentication routes and logic.
  - `badges.py`: Badge management logic.
  - `config.py`: Configuration settings.
  - `forms.py`: WTForms definitions.
  - `games.py`: Game management logic.
  - `main.py`: Main routes and views.
  - `models.py`: SQLAlchemy models.
  - `profile.py`: User profile management logic.
  - `social.py`: Social media integration logic.
  - `quests.py`: Quest management and submission logic.
  - `utils.py`: Utility functions.
- `csv/`: Contains CSV files for bulk data import.
- `docs/`: Documentation files.
- `migrations/`: Database migration scripts.
- `venv/`: Virtual environment directory.
- `.gitignore`: Git ignore file.
- `.env`: Environment configuration file.
- `LICENSE.md`: License information.
- `README.md`: Project overview and setup instructions.
- `pyproject.toml`: Project configuration and Python dependencies managed by Poetry.
- `wsgi.py`: WSGI entry point for deploying the application.

### Important Files

- **`app/__init__.py`**: Initializes the Flask application and registers blueprints.
- **`app/models.py`**: Defines the database models.
- **`app/forms.py`**: Defines the forms used in the application.
- **`app/utils/`**: Package of utility modules used across the application.
- **`app/templates/`**: Contains HTML templates for rendering views.
- **`pyproject.toml`**: Lists the dependencies required for the project and is managed by Poetry.

## Setting Up the Development Environment

### Prerequisites

Ensure you have the following installed:

- Python 3.x
- PostgreSQL
- Virtualenv
- ffmpeg (optional for video compression)

### Installation

1. **Clone the repository**:
   \`\`\`bash
   git clone https://github.com/your-repo/your-project.git
   cd your-project
   \`\`\`

2. **Create a virtual environment**:
   \`\`\`bash
   python3 -m venv venv
   source venv/bin/activate
   \`\`\`

3. **Install dependencies**:
   \`\`\`bash
   poetry install
   \`\`\`

4. **Set up the database**:
   Create a PostgreSQL database and update the `.env` file with your database credentials.

5. **Run database migrations**:
   \`\`\`bash
   flask db upgrade
   \`\`\`

### Configuration

Update the `.env` file with the appropriate configuration settings for your development environment.
Important variables include:

- `GCS_BUCKET` – name of the Google Cloud Storage bucket used for uploads
- `GCS_BASE_URL` – base URL for serving uploaded media
- `GCS_STORAGE_CLASS` – storage class for uploaded files (`ARCHIVE` is cheapest)

## Key Components

### Flask Blueprints

The application is modularized using Flask Blueprints:

- **`main_bp`**: Main routes and views (defined in `main.py`).
- **`admin_bp`**: Admin-specific routes and views (defined in `admin.py`).
- **`auth_bp`**: Authentication routes and views (defined in `auth.py`).
- **`badges_bp`**: Badge management routes and views (defined in `badges.py`).
- **`ai_bp`**: AI quest generation routes and views (defined in `ai.py`).
- **`profile_bp`**: User profile management routes and views (defined in `profile.py`).
- **`quests_bp`**: Quest management and submission routes and views (defined in `quests.py`).

### Database Models

The database models are defined in `app/models.py` and include:

- **`User`**: Represents a user in the system.
- **`Game`**: Represents a game that users can participate in.
- **`Quest`**: Represents a quest that users can complete.
- **`Badge`**: Represents a badge that users can earn.
- **`UserQuest`**: Represents a user's completion of a quest.
- **`QuestSubmission`**: Represents a user's submission for a quest.
- **`ShoutBoardMessage`**: Represents a message posted on the Shout Board.

### Forms

Forms are defined using WTForms in `app/forms.py` and include:

- **`ProfileForm`**: Form for updating user profiles.
- **`ShoutBoardForm`**: Form for posting messages on the Shout Board.
- **`QuestForm`**: Form for creating and updating quests.
 - **`PhotoForm`**: Form for submitting photos or videos for quest verification.
- **`ContactForm`**: Form for contacting support.

### Utilities

Utility functions are organized under `app/utils/` and include:

- **`save_profile_picture`**: Saves profile pictures.
- **`save_badge_image`**: Saves badge images.
- **`update_user_score`**: Updates a user's score.
- **`award_badges`**: Awards badges to users.
- **`can_complete_quest`**: Checks if a user can complete a quest.
- **`send_email`**: Sends emails.

## Admin Functionality

### Admin Dashboard

The admin dashboard provides an overview of the platform's activity and allows admins to manage various aspects of the system. It includes:

- **User Management**: View and manage user accounts.
- **Game Management**: Create, update, and delete games.
- **Quest Management**: Create, update, and delete quests.
- **Badge Management**: Create, update, and delete badges.
- **Shout Board Management**: View and delete Shout Board messages.

### Badge Management

Admins can manage badges using the following routes:

- **Create Badge**: `/badges/create`
- **Manage Badges**: `/badges/manage_badges`
- **Update Badge**: `/badges/update/<int:badge_id>`
- **Delete Badge**: `/badges/delete/<int:badge_id>`

### Quest Management

Admins can manage quests using the following routes:

- **Create Quest**: `/quests/<int:game_id>/add_quest`
- **Manage Quests**: `/quests/<int:game_id>/manage_quests`
- **Update Quest**: `/quests/quest/<int:quest_id>/update`
- **Delete Quest**: `/quests/quest/<int:quest_id>/delete`

### Shout Board

The Shout Board allows admins to post and pin messages that are viewable by all users. Admins can manage Shout Board messages using the following routes:

- **Post Message**: `/shout-board`
- **Pin Message**: `/pin_message/<int:message_id>`
- **Delete Message**: Managed via the admin dashboard.

## User Functionality

### Quest Submission

Users can complete quests and submit verification using the following routes:

- **Submit Quest**: `/quests/quest/<int:quest_id>/submit`
- **View Quest Submissions**: `/quests/quest/<int:quest_id>/submissions`
- **Delete Submission**: `/quests/quest/delete_submission/<int:submission_id>`

### View User Submissions

Users can view their submissions using the following routes:

- **View My Submissions**: `/quests/quest/my_submissions`
- **Delete My Submission**: `/quests/quest/delete_submission/<int:submission_id>`

### Profile Management

Users can manage their profiles using the following routes:

- **View Profile**: `/profile/<int:user_id>`
- **Edit Profile**: `/profile/<int:user_id>/edit`
- **Post Message on Profile Wall**: `/profile/<int:user_id>/messages`
- **Delete Profile Wall Message**: `/profile/<int:user_id>/messages/<int:message_id>/delete`
- **Reply to Profile Wall Message**: `/profile/<int:user_id>/messages/<int:message_id>/reply`
- **Edit Profile Wall Message**: `/profile/<int:user_id>/messages/<int:message_id>/edit`

### Social Media Integration

Users can integrate their social media accounts to share their achievements:

- **Twitter Integration**: Post quest completions on Twitter.
- **Facebook Integration**: Share quest completions and photos on Facebook.
- **Instagram Integration**: Post photos related to quest completions on Instagram.

## AI Quest Generation

Our platform leverages AI to generate new quests for users. This functionality is powered by OpenAI and involves the following steps:

1. **Generate Quest**: `/ai/generate_quest`
   - This route accepts a quest description and uses OpenAI to generate quest details such as title, description, tips, points, completion limit, frequency, verification type, badge name, and badge description.
   
2. **Create Quest**: `/ai/create_quest`
   - After generating quest details, this route creates the quest in the database.

3. **Generate Badge Image**: `/ai/generate_badge_image`
   - This route uses OpenAI to generate a badge image based on the badge description.

## Static Assets

### CSS and JavaScript

Third-party libraries (Bootstrap, KaTeX, Font Awesome, and Highlight.js) are now loaded directly from public CDNs.
Only project specific assets remain under `app/static`.

### Images and Videos

Images and videos are located in `app/static/images`, `app/static/qr_codes`, and `app/static/videos`.

## Testing and Debugging

### Running Tests

Tests are crucial for maintaining the integrity of the codebase. To run tests:

1. **Navigate to the project directory**:
   \`\`\`bash
   cd your-project
   \`\`\`

2. **Run tests**:
   \`\`\`bash
   pytest
   \`\`\`

### Debugging

To enable debugging, set `DEBUG=true` in your `.env` file. This enables Flask's debugger with detailed error messages and an interactive browser debugger.

If login requests fail with a "CSRF session token is missing" message, the session cookie was not
sent. Ensure `SECRET_KEY` is defined and access the site using the host specified by
`LOCAL_DOMAIN` (typically `localhost:5000`).

When `DEBUG=true`, JavaScript helpers skip sending CSRF tokens to simplify local testing.

## Deployment

### Production Configuration

Before deploying to production, ensure the following settings in your `.env` file:

- `DEBUG = false`
- `SESSION_COOKIE_SECURE = true`
- `SESSION_COOKIE_DOMAIN` should match your production domain or be left blank to
  use the request host.
- `SQLALCHEMY_DATABASE_URI` is set to the production database URL.
- `SECRET_KEY` is set to a secure value.

### Deployment Steps

1. **Set up the server**:
   - Install required packages: `Python`, `PostgreSQL`, `Nginx`, `Gunicorn`.

   - NGINX Config:
\`\`\`
    # Serve robots.txt
    location = /robots.txt {
        alias /var/www/html/app/robots.txt;
    }
    a
    # Security Headers
    add_header Strict-Transport-Security "max-age=3600; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Content Security Policy
    add_header Content-Security-Policy "
        default-src 'self';
        script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com https://www.googletagmanager.com;
        style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;
        img-src 'self' data:;
        font-src 'self' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;
        connect-src 'self' https://www.google-analytics.com https://questbycycle.org wss://questbycycle.org;
        frame-src 'self';
        object-src 'none';
        base-uri 'self';
        form-action 'self';
    ";

    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;


    # Serve Static Files - CSS
    location /static/css/ {
        alias /var/www/html/app/static/css/;
        expires 1h; # Cache CSS files for 1 hour
        add_header Cache-Control "public, max-age=3600, must-revalidate";
        try_files $uri $uri/ =404;
    }

   # Serve Static Files - Video
    location /static/videos/ {
        alias /var/www/html/app/static/videos/;
        expires 30d;
        add_header Cache-Control "public, max-age=, max-age=2592000, must-revalidate";
        try_files $uri $uri/ =404;
    }


    # Serve Static Files - Photos
    location /static/photos/ {
        alias /var/www/html/app/static/photos/;
        expires 30d; # Cache photos for 30 days
        add_header Cache-Control "public, max-age=2592000, must-revalidate";
        try_files $uri $uri/ =404;
    }

    # Serve Other Static Files
    location /static/ {
        alias /var/www/html/app/static/;
        expires 1h; # Cache other static files for 1 hour
        add_header Cache-Control "public, max-age=3600, must-revalidate";
        try_files $uri $uri/ =404;
    }

    # Proxy Pass for Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }


    client_max_body_size 10M;

    # First attempt to serve request as file, then as directory, then fall back to displaying a 404.
    try_files $uri $uri/ =404;
}
\`\`\`
2. **Clone the repository**:
   \`\`\`bash
   git clone https://github.com/your-repo/your-project.git
   cd your-project
   \`\`\`

3. **Set up the virtual environment**:
   \`\`\`bash
   python3 -m venv venv
   source venv/bin/activate
   \`\`\`

4. **Install dependencies**:
   \`\`\`bash
   poetry install
   \`\`\`

5. **Configure the database**:
   - Update the `.env` file with the production database credentials.

6. **Run database migrations**:
   \`\`\`bash
   flask db upgrade
   \`\`\`

7. **Set up Gunicorn**:
   \`\`\`bash
   gunicorn --bind 0.0.0.0:8000 wsgi:app
   \`\`\`

8. **Configure Nginx**:
   - Set up an Nginx server block to proxy requests to Gunicorn.

9. **Start the application**:
   - Ensure Gunicorn and Nginx are running.

10. **Start the task worker**:
    - Run `poetry run rqworker` to process background jobs.

## Calendar Integration

The application can automatically create quests from Google Calendar events. Set
the `GOOGLE_CALENDAR_CREDENTIALS` environment variable to the path of a Google
service account JSON file. Each `Game` may define a `google_calendar_id`.
APScheduler runs a job every 15 minutes to fetch new events and create quests.

By following this guide, you should have a comprehensive understanding of the project's architecture, codebase, and development practices. Happy coding!
