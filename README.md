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

### Server Setup


1. Login with SSH key:

```ssh-keygen -t rsa -b 4096 -C "YOUR_EMAIL"```
```cat ~/.ssh/id_rsa.pub``` <- Copy this key from local computer
```mkdir -p ~/.ssh && nano ~/.ssh/authorized_keys``` Paste the key in here on remote server 
Now login with ```ssh USER@HOST```

2. Allocate Swap on low ram systems:

```sudo fallocate -l 4G /swapfile```
```sudo chmod 600 /swapfile```
```sudo mkswap /swapfile```
```sudo swapon /swapfile```
```echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab```

3. Install NGINX:
```sudo apt-get install curl gnupg2 ca-certificates lsb-release ubuntu-keyring```
```sudo apt install nginx```
```sudo ufw allow 'Nginx Full'```
```sudo ufw allow 'OpenSSH'```
```sudo ufw enable```

4. Edit NGINX config:
```sudo nano /etc/nginx/conf.d/default.conf```
    [Example default](/docs/default.NGINX)
```sudo systemctl restart nginx.service```
```sudo certbot --nginx -d DOMAINNAME```

### Installation and Deployment

1. Create new user:

```sudo adduser --system --group --disabled-login APPUSER```
```sudo -u APPUSER mkdir /opt/QuestByCycle```

2.Clone and open the repository:

``` cd /opt```
``` sudo mkdir QuestByCycle```
``` chown APPUSER:APPUSER QuestByCycle```
```git clone https://github.com/denuoweb/QuestByCycle.git```
```cd QuestByCycle```

2. Install python3.11:

```sudo add-apt-repository ppa:deadsnakes/ppa```
```sudo apt install python3.11 python3.11-venv python3-pip python3-gevent python3-certbot-nginx```

3. Install Poetry:
```sudo -u APPUSER HOME=/home/APPUSER curl -sSL https://install.python-poetry.org | sudo -u APPUSER HOME=/home/APPUSER python3 -```
```sudo -u APPUSER /home/APPUSER/.local/bin/poetry env use /usr/bin/python3.11```
```sudo -u APPUSER /home/APPUSER/.local/bin/poetry install```

4. Prepare the Deployment:

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

7. PostgresDB Setup:
```sudo apt install postgresql postgresql-contrib```

```sudo systemctl start postgresql```

```sudo systemctl enable postgresql```

```sudo su - postgres```

```psql -U postgres```

```CREATE DATABASE databasename;```

```\c databasename```

```CREATE USER username WITH PASSWORD 'password';```

```GRANT ALL PRIVILEGES ON DATABASE databasename TO username;```

```GRANT USAGE, CREATE ON SCHEMA public TO username;```

```GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO username;```

```ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO username;```

```\q```

```exit```

8. Set up the environment variables:
    
    - Copy `config.toml.example` to `config.toml` and adjust the variables accordingly.


9. Deploy

Development:
```flask run```

Production Without service provider:
```gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 127.0.0.1:5000 wsgi:app```

Production With service provider:
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

