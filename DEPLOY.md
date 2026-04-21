# MY DSP Platform — Deployment Guide

## Run Locally (Windows)

```cmd
cd C:\Users\User\OneDrive\Desktop\Budget\mydsp_app
python -m pip install -r requirements.txt
python app.py
```
Open your browser at: **http://localhost:5000**

**Default Credentials**
| Username | Password   | Role  |
|----------|------------|-------|
| admin    | Admin@123  | Admin |
| staff    | Staff@123  | Staff |

> Change passwords immediately after first login via the key icon in the sidebar.

---

## Deploy to Render (Free Cloud Hosting)

1. Create a free account at https://render.com
2. Push this folder to a GitHub repository
3. In Render: **New → Web Service** → connect your repo
4. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `python app.py`
   - **Environment variable:** `SECRET_KEY` → set a long random string
5. Click **Deploy** — your app will be live at `https://your-app.onrender.com`

---

## Deploy to Railway

1. Create account at https://railway.app
2. **New Project → Deploy from GitHub repo**
3. Add environment variable: `SECRET_KEY=your-secret-here`
4. Railway auto-detects Python and deploys

---

## Deploy to a VPS (Ubuntu)

```bash
# Install Python & pip
sudo apt update && sudo apt install python3 python3-pip -y

# Copy app files to server, then:
cd /opt/mydsp_app
pip3 install -r requirements.txt

# Run with gunicorn (production)
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:80 app:app
```

For HTTPS, set up Nginx as a reverse proxy with a Let's Encrypt certificate.

---

## Production Security Checklist

- [ ] Change `SECRET_KEY` to a random 32+ character string
- [ ] Change default admin and staff passwords
- [ ] Enable HTTPS (SSL certificate)
- [ ] Back up `mydsp.db` daily (it contains all your data)
- [ ] Set `FLASK_DEBUG=false` in production

---

## Database Backup (Windows)

The database file is `mydsp.db` in this folder.
To back up, simply copy it:

```cmd
copy mydsp.db mydsp_backup_%date%.db
```

Or set up a scheduled task to copy it to OneDrive/cloud storage automatically.

---

## Modules Included

| Module | Description |
|--------|-------------|
| Dashboard | Live KPI summary with charts |
| Participants | Full NDIS participant master register |
| Income Ledger | NDIS invoice entry per participant |
| Expenditure | Business cost tracking by category |
| Staff Costs | Wages, NDIS rates, super auto-calc |
| Petty Cash | Cash register with running balance |
| Task Manager | Staff duties & compliance tasks |
| Communication Log | Calls, emails, meetings |
| Issues Register | Risk-rated matters to attend |
| Reports | P&L summary, export to Excel & PDF |
| Admin | User management & audit log |
