
# QuestByCycle

[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/en/stable/quickstart/) [![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)]([https://www.postgresql.org/](https://www.postgresql.org/docs/current/index.html)) [![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)](https://docs.gunicorn.org/en/stable/)
[![Python](https://img.shields.io/badge/python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Git](https://img.shields.io/badge/git-F05032.svg?style=for-the-badge&logo=git&logoColor=white)](https://git-scm.com/) [![FFmpeg](https://img.shields.io/badge/FFmpeg-007808.svg?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Poetry](https://img.shields.io/badge/Poetry-60A5FA.svg?style=for-the-badge&logo=poetry&logoColor=white)](https://python-poetry.org/) [![NGINX](https://img.shields.io/badge/NGINX-009639.svg?style=for-the-badge&logo=nginx&logoColor=white)](https://www.nginx.com/)
[![Let's Encrypt](https://img.shields.io/badge/Let%27s_Encrypt-003A70.svg?style=for-the-badge&logo=letsencrypt&logoColor=white)](https://letsencrypt.org/) [![UFW](https://img.shields.io/badge/UFW-000000.svg?style=for-the-badge&logo=ufw&logoColor=white)](https://help.ubuntu.com/community/UFW) [![Postfix](https://img.shields.io/badge/Postfix-E60033.svg?style=for-the-badge&logo=postfix&logoColor=white)](http://www.postfix.org/)
[![GeoIP2](https://img.shields.io/badge/GeoIP2-0072B5.svg?style=for-the-badge&logo=maxmind&logoColor=white)](https://www.maxmind.com/en/geoip2-services-and-databases) [![Sass](https://img.shields.io/badge/Sass-CC6699.svg?style=for-the-badge&logo=sass&logoColor=white)](https://sass-lang.com/) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/denuoweb/QuestByCycle)

A gamified bicycling platform built with Flask.

## Table of Contents
- [Overview](#overview)
- [Package Icons](#package-icons)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Developer Setup](#quick-developer-setup)
  - [Debian 12 Server Setup (Production)](#debian-12-server-setup-production)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)

## Overview

QuestByCycle is a Flask-based web application designed to engage and motivate the bicycling community through a gamified approach, promoting environmental sustainability and climate activism. Participants complete quests or missions related to bicycling and environmental stewardship, earning badges and recognition among the community. The platform features a competitive yet collaborative environment where users can view their standings on a leaderboard, track their progress through profile pages, and contribute to a greener planet.

## Package Icons

This project relies on a variety of open source libraries. The badges below link directly to the GitHub repository for each package.

### Flask Core & Extensions

[![Flask](https://img.shields.io/badge/Flask-000?style=for-the-badge&logo=flask&logoColor=white)](https://github.com/pallets/flask)
[![Werkzeug](https://img.shields.io/badge/Werkzeug-333?style=for-the-badge&logo=github&logoColor=white)](https://github.com/pallets/werkzeug)
[![Flask-WTF](https://img.shields.io/badge/Flask--WTF-555?style=for-the-badge&logo=github&logoColor=white)](https://github.com/wtforms/flask-wtf)
[![Flask-SQLAlchemy](https://img.shields.io/badge/Flask--SQLAlchemy-555?style=for-the-badge&logo=github&logoColor=white)](https://github.com/pallets/flask-sqlalchemy)
[![Flask-Login](https://img.shields.io/badge/Flask--Login-555?style=for-the-badge&logo=github&logoColor=white)](https://github.com/maxcountryman/flask-login)

### Data Layer

[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-000?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://github.com/sqlalchemy/sqlalchemy)
[![psycopg](https://img.shields.io/badge/psycopg-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/psycopg/psycopg)

### Forms, Validation & Security

[![WTForms](https://img.shields.io/badge/WTForms-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/wtforms/wtforms)
[![email-validator](https://img.shields.io/badge/email--validator-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/JoshData/python-email-validator)
[![cryptography](https://img.shields.io/badge/cryptography-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/pyca/cryptography)
[![PyJWT](https://img.shields.io/badge/PyJWT-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/jpadilla/pyjwt)
[![html-sanitizer](https://img.shields.io/badge/html--sanitizer-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/matthiask/html-sanitizer)
[![flask-Humanify](https://img.shields.io/badge/flask--Humanify-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/tn3w/flask-Humanify)

### Infrastructure & Runtime

[![Gunicorn](https://img.shields.io/badge/Gunicorn-872729?style=for-the-badge&logo=gunicorn&logoColor=white)](https://github.com/benoitc/gunicorn)
[![APScheduler](https://img.shields.io/badge/APScheduler-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/agronholm/apscheduler)

For automated provisioning details see [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md).

### Utility Libraries

[![qrcode](https://img.shields.io/badge/qrcode-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/lincolnloop/python-qrcode)
[![OpenAI](https://img.shields.io/badge/OpenAI-000000?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/openai-python)
[![Tomli](https://img.shields.io/badge/Tomli-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/hukkinj1/tomli)

### Development & Testing

[![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/pytest-dev/pytest)
[![python-dotenv](https://img.shields.io/badge/python--dotenv-000?style=for-the-badge&logo=dotenv&logoColor=white)](https://github.com/theskumar/python-dotenv)
[![rsa](https://img.shields.io/badge/rsa-555?style=for-the-badge&logo=python&logoColor=white)](https://github.com/sybrenstuvel/python-rsa)

## Features

- **User Authentication:** Secure sign-up and login functionality to manage user access and personalize user experiences.
- **Bot Protection:** Login and registration forms are guarded by flask-Humanify to challenge automated requests.
- **Leaderboard/Homepage:** A dynamic display of participants, their rankings, and badges earned, fostering a sense of competition and achievement.
- **Quest Submission:** An interface for users to submit completed quests or missions, facilitating the review and award of badges.
- **User Profiles:** Dedicated pages for users to view their badges, completed quests, and ranking within the community.
- **Responsive Design:** Ensuring a seamless and engaging user experience across various devices and screen sizes.
- **PWA/TWA Support:** Service worker and offline page. See [docs/PWA.md](docs/PWA.md) for configuration.
- **Push Notifications:** Optional Web Push support keeps users informed even when the site is closed. See [docs/PUSH_NOTIFICATIONS.md](docs/PUSH_NOTIFICATIONS.md) for setup.
- **Calendar Sync:** Link a Google Calendar to auto-create quests from events.
- **Calendar Quest View:** Upcoming and past calendar quests are shown in separate tables for clarity.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- git
- ffmpeg (optional, for video compression)
- Poetry (for dependency management)
- redis-server
- NGINX with Certbot
- UFW firewall
- Postfix (for email)
- GeoIP2 module and database
- Sass CLI for building CSS
- Node.js and npm

### Quick Developer Setup

1. Clone the repository and enter the directory:
   ```bash
   git clone https://github.com/denuoweb/QuestByCycle.git
   cd QuestByCycle
   ```

   Install Poetry and project dependencies:
   ```bash
   curl -sSL https://install.python-poetry.org | python3
   poetry install
   ```

   Copy `.env.example` to `.env` and adjust the values.

   Copy `gunicorn.conf.py.example` to `gunicorn.conf.py`.


#### RAM Allocation
  Allocate Swap on low ram systems:

```sudo fallocate -l 4G /swapfile```
```sudo chmod 600 /swapfile```
```sudo mkswap /swapfile```
```sudo swapon /swapfile```
```echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab```

#### Database Install and Setup
   Secure the postgres superuser
```sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'STRONG_SUPERSECRET';"```

   Create application database & role
```sudo -u postgres psql <<EOF```
```CREATE DATABASE questdb;```
```CREATE USER questuser WITH PASSWORD 'questpassword';```
```GRANT ALL PRIVILEGES ON DATABASE questdb TO questuser;```
```\c questdb```
```ALTER SCHEMA public OWNER TO questuser;```
```EOF```

   Ensure Postgres listens only on localhost
```sudo sed -i "s/^#listen_addresses =.*/listen_addresses = 'localhost'/" /etc/postgresql/*/main/postgresql.conf```
```sudo systemctl restart postgresql``


   Install NGINX:
```curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \```
```    | sudo tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null```
```echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \```
```http://nginx.org/packages/mainline/debian `lsb_release -cs` nginx" \```
```    | sudo tee /etc/apt/sources.list.d/nginx.list```
```echo -e "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" \```
```    | sudo tee /etc/apt/preferences.d/99nginx```
```sudo apt update```
```sudo apt install nginx nginx-common```

9. Install the GeoIP2 module and database

10. Set up UFW
```sudo apt install ufw```
```sudo ufw allow 'WWW Full'```
```sudo ufw allow 'OpenSSH'```
```sudo ufw enable```

11. Edit NGINX config:
```sudo nano /etc/nginx/conf.d/default.conf```
    [Example default](/docs/default.NGINX)
```sudo systemctl restart nginx.service```
```sudo certbot --nginx -d DOMAINNAME```

   Set up Emailing
```sudo apt update```
```sudo apt install postfix```
```sudo nano /etc/postfix/main.cf```

   Build frontend assets

```cd /opt/QuestByCycle```
```npm install```
```npm run build```

Vite outputs two entry points: `main.js` for the majority of pages and
`submitPhoto.js` which is loaded only on `submit_photo.html`.

   Copy `.env.example` to `.env` and set all variables.
   Copy `gunicorn.conf.py.example` to `gunicorn.conf.py`.
   If you have `ffmpeg` installed, ensure it is accessible or set
    `FFMPEG_PATH` in `.env`. Without `ffmpeg` videos are stored unmodified.
   Run the server in debug
```sudo -u APPUSER /home/APPUSER/.local/bin/poetry run flask --app wsgi:app run --host=127.0.0.1 --port=5000```

   Run the server in production:

```sudo nano /etc/systemd/system/questbycycle.service```

```markdown
[Unit]
Description=gunicorn daemon for QuestByCycle application
After=network.target

[Service]
User=APPUSER
Group=APPUSER
WorkingDirectory=/opt/QuestByCycle
ExecStart=/home/APPUSER/.cache/pypoetry/virtualenvs/questbycycle-BK-IO7k_-py3/bin/gunicorn --config /opt/QuestByCycle/gunicorn.conf.py wsgi:app
Nice=-10
Environment="PATH=/home/APPUSER/.cache/pypoetry/virtualenvs/questbycycle-BK-IO7k_-py3/bin"

[Install]
WantedBy=multi-user.target
```
Run:

```sudo systemctl start questbycycle.service```
```sudo systemctl enable questbycycle.service```

   Start the background worker:
```sudo -u APPUSER /home/APPUSER/.local/bin/poetry run rqworker```

Update Poetry:
```sudo -u APPUSER HOME=/home/APPUSER /home/APPUSER/.local/bin/poetry update```

## Contributing

We welcome contributions from the community! Whether you're interested in adding new features, fixing bugs, or improving documentation, your help is appreciated. Please refer to CONTRIBUTING.md for guidelines on how to contribute to QuestByCycle.


## Acknowledgments

- The bicycling community for their endless passion and dedication to making the world a greener place.
- All contributors who spend their time and effort to improve QuestByCycle.

