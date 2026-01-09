# Deployment Guide
Now that you know the basics and advanced concepts, let's deploy your bot!

---

## Table of Contents
1. [Uploading to GitHub](#1-uploading-to-github)
2. [Deployment Options](#2-deployment-options)
3. [Railway Deployment](#3-railway-deployment)
4. [VPS Deployment](#4-vps-deployment)
5. [Docker Deployment](#5-docker-deployment)
6. [Best Practices](#6-best-practices)

---

## 1. Uploading to GitHub

To upload your files to GitHub, use these git commands in your console (git must be installed):

### Initial Setup
```bash
# Initialize git repository
git init

# Add files to staging
git add .
```
The "." adds all files. To add specific files, replace with filenames.

```bash
# Commit changes
git commit -m "Initial commit"
```
Replace the message between quotes with your commit description.

```bash
# Add remote repository
git remote add origin https://github.com/your-username/your-repo.git
```

```bash
# Verify remote connection
git remote -v

# Push to GitHub
git push -u origin main
```

### Subsequent Updates
```bash
git add .
git commit -m "Your update message"
git push origin main
```

### Important: .gitignore File
Create a `.gitignore` file to exclude sensitive files:

```gitignore
# Environment variables
.env
*.env

# Virtual environment
venv/
.venv/
env/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Database files
*.db
*.sqlite
*.sqlite3

# IDE settings
.vscode/
.idea/
*.swp

# Logs
*.log
logs/

# OS files
.DS_Store
Thumbs.db
```

---

## 2. Deployment Options

### Free Hosting Options

| Platform | Free Tier | Pros | Cons |
|----------|-----------|------|------|
| **Railway** | $5 credit/month | Easy setup, GitHub integration | Limited free credits |
| **Render** | 750 hours/month | Simple deployment, auto-deploy | Sleeps after inactivity |
| **Fly.io** | 3 VMs free | Good performance | Complex configuration |
| **Heroku** | No longer free | - | Paid only now |
| **Oracle Cloud** | Always free tier | Generous resources | Complex setup |
| **Google Cloud** | $300 credit | Professional tools | Steep learning curve |

### Paid Options

| Platform | Starting Price | Best For |
|----------|---------------|----------|
| **DigitalOcean** | $4/month | VPS, scalable |
| **Linode** | $5/month | Simple VPS |
| **AWS EC2** | $3.50/month | Enterprise level |
| **Contabo** | €4/month | Budget VPS |

---

## 3. Railway Deployment

Railway is beginner-friendly with GitHub integration.

### Step 1: Prepare Your Project

**requirements.txt**
```txt
discord.py>=2.3.2
python-dotenv>=1.0.0
aiosqlite>=0.19.0
asyncpg>=0.29.0
```

**Procfile** (create in root directory)
```
worker: python main.py
```

**runtime.txt** (optional - specify Python version)
```
python-3.11.6
```

### Step 2: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Authorize Railway to access your repositories

### Step 3: Deploy

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your bot repository
4. Railway will auto-detect Python and install dependencies

### Step 4: Add Environment Variables

1. Go to **Variables** tab
2. Click **"New Variable"**
3. Add your variables:
   ```
   DISCORD_TOKEN=your_bot_token_here
   DATABASE_URL=your_database_url (if using PostgreSQL)
   ```

### Step 5: Monitor and Logs

- View logs in the **Deployments** tab
- Monitor resource usage in **Metrics**
- Check build status and errors

### Railway Configuration (optional)

Create `railway.json` for custom settings:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 4. VPS Deployment

For more control, use a Virtual Private Server (VPS).

### Step 1: Choose a VPS Provider

Popular options:
- **DigitalOcean** - Easy to use
- **Linode** - Great documentation
- **Contabo** - Budget-friendly
- **Oracle Cloud** - Free tier available

### Step 2: Initial Server Setup

```bash
# Connect via SSH
ssh root@your_server_ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3-pip git -y

# Create a new user for security
sudo adduser botuser
sudo usermod -aG sudo botuser

# Switch to new user
su - botuser
```

### Step 3: Clone Your Repository

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add SSH key to GitHub
cat ~/.ssh/id_ed25519.pub

# Clone repository
git clone git@github.com:your-username/your-repo.git
cd your-repo
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add your variables:
```env
DISCORD_TOKEN=your_token_here
DATABASE_URL=your_database_url
```

### Step 6: Keep Bot Running with PM2

```bash
# Install Node.js and PM2
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Start bot with PM2
pm2 start main.py --name discord-bot --interpreter python3

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup

# Check status
pm2 status

# View logs
pm2 logs discord-bot
```

### PM2 Useful Commands

```bash
# Restart bot
pm2 restart discord-bot

# Stop bot
pm2 stop discord-bot

# Monitor resources
pm2 monit

# Delete bot from PM2
pm2 delete discord-bot
```

### Alternative: systemd Service

Create `/etc/systemd/system/discord-bot.service`:

```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/your-repo
Environment="PATH=/home/botuser/your-repo/venv/bin"
ExecStart=/home/botuser/your-repo/venv/bin/python main.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-bot
sudo systemctl start discord-bot

# Check status
sudo systemctl status discord-bot

# View logs
sudo journalctl -u discord-bot -f
```

---

## 5. Docker Deployment

Docker provides consistent environments across platforms.

### Step 1: Create Dockerfile

**Dockerfile**
```dockerfile
# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Run bot
CMD ["python", "main.py"]
```

### Step 2: Create docker-compose.yml

**docker-compose.yml**
```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: discord-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    container_name: postgres-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: botdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Step 3: Build and Run

```bash
# Build image
docker build -t discord-bot .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop containers
docker-compose down
```

### Docker Commands

```bash
# List containers
docker ps

# View logs
docker logs discord-bot

# Restart container
docker restart discord-bot

# Execute commands in container
docker exec -it discord-bot bash

# Remove container
docker rm -f discord-bot

# Rebuild and restart
docker-compose up -d --build
```

---

## 6. Best Practices

### Security

1. **Never commit tokens or secrets**
   - Use `.env` files
   - Add `.env` to `.gitignore`
   - Use environment variables on hosting platforms

2. **Use SSH keys for server access**
   ```bash
   # Generate SSH key
   ssh-keygen -t ed25519
   
   # Copy to server
   ssh-copy-id user@server_ip
   ```

3. **Setup firewall**
   ```bash
   # UFW firewall
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

4. **Regular updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### Monitoring

1. **Setup logging**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('bot.log'),
           logging.StreamHandler()
       ]
   )
   ```

2. **Monitor uptime**
   - Use [UptimeRobot](https://uptimerobot.com)
   - Setup Discord webhook alerts

3. **Error tracking**
   - Use [Sentry](https://sentry.io) for error reporting
   - Setup Discord error webhooks

### Backup

```bash
# Backup database
pg_dump -U botuser botdb > backup_$(date +%Y%m%d).sql

# Automate with cron
crontab -e
# Add: 0 2 * * * pg_dump -U botuser botdb > /backups/backup_$(date +\%Y\%m\%d).sql
```

### Auto-Update from GitHub

```bash
# Create update script
nano update.sh
```

```bash
#!/bin/bash
cd /home/botuser/your-repo
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart discord-bot
```

```bash
chmod +x update.sh
```

### Environment-Specific Settings

**config.py**
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('DISCORD_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Development settings
    if ENVIRONMENT == 'development':
        DEBUG = True
        LOG_LEVEL = 'DEBUG'
    
    # Production settings
    else:
        DEBUG = False
        LOG_LEVEL = 'INFO'
```

---

## Troubleshooting

### Bot not starting

1. Check logs for errors
2. Verify token is correct
3. Ensure all dependencies are installed
4. Check Python version compatibility

### Bot goes offline randomly

1. Check hosting platform limits
2. Monitor memory usage
3. Implement reconnection logic:
   ```python
   @bot.event
   async def on_disconnect():
       print("Bot disconnected! Attempting to reconnect...")
   ```

### Database connection issues

1. Verify connection string
2. Check firewall rules
3. Ensure database service is running
4. Test connection manually

---

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [DigitalOcean Tutorials](https://www.digitalocean.com/community/tutorials)
- [Docker Documentation](https://docs.docker.com)
- [PM2 Documentation](https://pm2.keymetrics.io/docs)
- [discord.py Hosting Guide](https://discordpy.readthedocs.io/en/stable/intro.html#hosting)

---

## Cost Optimization

### Free Tier Strategies

1. **Use multiple free tiers** - Rotate between platforms
2. **Optimize code** - Reduce CPU/memory usage
3. **Database optimization** - Use connection pooling
4. **Caching** - Reduce database queries

### Monitoring Costs

```python
# Log resource usage
import psutil

@bot.command()
@commands.is_owner()
async def stats(ctx):
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    await ctx.send(f"CPU: {cpu}% | Memory: {mem}%")
```

---

Good luck with your deployment! 🚀