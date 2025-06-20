sudo apt update

sudo apt -y upgrade

sudo apt -y install postgresql postgresql-contrib ffmpeg ufw redis-server git python3-pip curl gnupg2 ca-certificates lsb-release debian-archive-keyring

sudo adduser --system --group --home /home/USER --shell /usr/sbin/nologin USER
sudo mkdir -p /opt/QuestByCycle
sudo chown USER:USER /opt/QuestByCycle
sudo chmod 755 /opt/QuestByCycle

sudo -u USER git clone https://github.com/denuoweb/QuestByCycle.git /opt/QuestByCycle

cd /opt/QuestByCycle

sudo -u USER curl -sSL https://install.python-poetry.org | sudo -u USER python3
sudo -u USER /home/USER/.local/bin/poetry install

sudo -u USER cp .env.example .env
sudo -u USER cp gunicorn.conf.py.example gunicorn.conf.py
sudo -u USER nano .env
sudo -u USER nano gunicorn.conf.py

sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'password';"

sudo -u postgres psql <<EOF
CREATE DATABASE database;
CREATE USER user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE database TO USER;
\c database
ALTER SCHEMA public OWNER TO user;
EOF

sudo sed -i "s/^#listen_addresses =.*/listen_addresses = 'localhost'/" /etc/postgresql/*/main/postgresql.conf


curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor | sudo tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null

echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] http://nginx.org/packages/mainline/debian `lsb_release -cs` nginx" | sudo tee /etc/apt/sources.list.d/nginx.list

echo -e "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" | sudo tee /etc/apt/preferences.d/99nginx

sudo apt update

sudo apt -y install nginx 
sudo apt -y install python3-certbot-nginx
sudo nano /etc/nginx/conf.d/default.conf
sudo nano /etc/nginx/nginx.conf
sudo nano /etc/letsencrypt/options-ssl-nginx.conf

sudo apt -y install postfix
sudo nano /etc/postfix/main.cf

sudo ufw allow 'WWW Full'
sudo ufw allow 'OpenSSH'
sudo ufw enable

# Build the frontend assets with Vite

sudo -u USER bash -c '
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 22
nvm use 22
npm install
npm run build
'