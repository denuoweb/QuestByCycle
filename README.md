[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/en/stable/quickstart/)  [![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)]([https://www.postgresql.org/](https://www.postgresql.org/docs/current/index.html))  [![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)](https://docs.gunicorn.org/en/stable/)

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/denuoweb/QuestByCycle)

# QuestByCycle

## Overview

QuestByCycle is a Flask-based web application designed to engage and motivate the bicycling community through a gamified approach, promoting environmental sustainability and climate activism. Participants complete quests or missions related to bicycling and environmental stewardship, earning badges and recognition among the community. The platform features a competitive yet collaborative environment where users can view their standings on a leaderboard, track their progress through profile pages, and contribute to a greener planet.

## Features

- **User Authentication:** Secure sign-up and login functionality to manage user access and personalize user experiences.
- **Leaderboard/Homepage:** A dynamic display of participants, their rankings, and badges earned, fostering a sense of competition and achievement.
- **Quest Submission:** An interface for users to submit completed quests or missions, facilitating the review and award of badges.
- **User Profiles:** Dedicated pages for users to view their badges, completed quests, and ranking within the community.
- **Responsive Design:** Ensuring a seamless and engaging user experience across various devices and screen sizes.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- git
-

### Debian 12 Server Setup

1. Allocate Swap on low ram systems:

```sudo fallocate -l 4G /swapfile```
```sudo chmod 600 /swapfile```
```sudo mkswap /swapfile```
```sudo swapon /swapfile```
```echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab```

2. Install PostgreSQL
```sudo apt-get update```
```sudo apt-get install -y postgresql postgresql-contrib```

   Secure the postgres superuser
```sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'STRONG_SUPERSECRET';"```

   Create application database & role
```sudo -u postgres psql <<EOF```
```CREATE DATABASE questdb;```
```CREATE USER questuser WITH PASSWORD 'EVEN_STRONGER_PASSWORD';```
```GRANT ALL PRIVILEGES ON DATABASE questdb TO questuser;```
```EOF```

   Ensure Postgres listens only on localhost
```sudo sed -i "s/^#listen_addresses =.*/listen_addresses = 'localhost'/" /etc/postgresql/*/main/postgresql.conf```
```sudo systemctl restart postgresql``

3. Install python dependencies
```sudo apt-get install -y python3-pip```

4. Create User
```sudo adduser --system --group appuser```
```sudo mkdir -p /opt/QuestByCycle```
```sudo chown appuser:appuser /opt/QuestByCycle```
```sudo chmod 755 /opt/QuestByCycle```
```sudo -u appuser git clone https://github.com/denuoweb/QuestByCycle.git /opt/QuestByCycle```

5. Install Poetry
```sudo su -s /bin/bash appuser -c 'curl -sSL https://install.python-poetry.org | python3 - && \```
```echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> /home/appuser/.bashrc'```

6. Download QuestByCycle
```sudo -u appuser git clone https://github.com/denuoweb/QuestByCycle.git /opt/QuestByCycle```

7. Install Python VM
```cd /opt/QuestByCycle```
```sudo -u appuser /home/appuser/.local/bin/poetry env use /usr/bin/python3```
```sudo -u appuser /home/appuser/.local/bin/poetry install```

8. Install NGINX:
```sudo apt install curl gnupg2 ca-certificates lsb-release debian-archive-keyring python3-certbot-nginx```
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

12. PostgresDB Setup:

```sudo systemctl start postgresql```

```sudo systemctl enable postgresql```

```\c databasename```

```GRANT ALL PRIVILEGES ON DATABASE databasename TO username;```

```GRANT USAGE, CREATE ON SCHEMA public TO username;```

```GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO username;```

```ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO username;```

```\q```

```exit```

13. Build CSS

```cd /opt/QuestByCycle```
```sass app/static/scss/main.scss app/static/css/main.css --no-source-map --style=compressed```

14. Configure
    - Copy `config.toml.example` to `config.toml` and adjust the variables accordingly.
    - Copy `gunicorn.conf.py.example` to `gunicorn.conf.py` and adjust the variables accordingly.

15. Run the server in debug
```sudo -u APPUSER /home/APPUSER/.local/bin/poetry run flask   --app wsgi:app   run   --host=127.0.0.1   --port=5000```

16. Run the server in production:

```sudo nano /etc/systemd/system/questbycycleApp.service```

```markdown
[Unit]
Description=gunicorn daemon for QuestByCycle application
After=network.target

[Service]
User=APPUSER
Group=APPUSER
WorkingDirectory=/opt/QuestByCycle
ExecStart=/home/APPUSER/.cache/pypoetry/virtualenvs/questbycycle-BK-IO7k_-py3/bin/gunicorn  --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker  --config /opt/QuestByCycle/gunicorn.conf.py wsgi:app
Nice=-10
Environment="PATH=/home/APPUSER/.cache/pypoetry/virtualenvs/questbycycle-BK-IO7k_-py3/bin"

[Install]
WantedBy=multi-user.target
```
8. Run:

```sudo systemctl start questbycycleApp.service```
```sudo systemctl enable questbycycleApp.service```

Update Poetry:
$ sudo -u APPUSER HOME=/home/APPUSER /home/APPUSER/.local/bin/poetry update

## Connect Game to X
https://developer.x.com/en/portal/dashboard

## Connect Game to Facebook and Instagram
Create 'app' here to get app id and app secret: https://developers.facebook.com/
Use this to generate the access token: https://developers.facebook.com/tools/explorer/

Permissions required:
pages_show_list
pages_read_engagement
pages_read_user_content
pages_manage_posts
pages_manage_engagement
instagram_basic
instagram_branded_content_ads_brand
instagram_branded_content_brand
instagram_branded_content_creator

## Connect OpenAI API for Quest and Badge Generation
https://platform.openai.com/api-keys

## msmtp
```
sudo apt-get update
sudo apt-get install msmtp msmtp-mta
nano ~/.msmtprc

# Set default values for all accounts
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        ~/.msmtp.log

# Set a default account
account        default
host           smtp.gmail.com
port           587
from           no-reply@questbycycle.org
user           your-email@gmail.com
password       your-gmail-password

# Alternatively, if you are using another SMTP server
# host           smtp.your-email-provider.com
# port           587
# from           no-reply@questbycycle.org
# user           your-smtp-username
# password       your-smtp-password

# Map local user to this account
account default : default

chmod 600 ~/.msmtprc

echo "Subject: Test Email" | msmtp -a default your-email@gmail.com

pip install Flask-Mail


```
## Contributing

We welcome contributions from the community! Whether you're interested in adding new features, fixing bugs, or improving documentation, your help is appreciated. Please refer to CONTRIBUTING.md for guidelines on how to contribute to QuestByCycle.


## Acknowledgments

- The bicycling community for their endless passion and dedication to making the world a greener place.
- All contributors who spend their time and effort to improve QuestByCycle.

