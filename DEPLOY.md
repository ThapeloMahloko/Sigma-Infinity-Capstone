# Deployment Guide — Hugging Face Spaces

This guide walks you through deploying the Smart Farm Dashboard to Hugging Face Spaces using Docker.

## Prerequisites

- Hugging Face account: https://huggingface.co
- A Hugging Face Space (Docker runtime): https://huggingface.co/spaces/sigma10goat/sitech_smart_farm
- Write-capable HF token (scope: `repo`)
- Git and SSH or HTTPS credentials configured

## Option 1: Push via Git (Recommended)

### 1. Create a Write-Capable Token

1. Go to https://huggingface.co/settings/tokens → **New token**
2. Name: `sigma10goat-deploy`
3. Role: **User**
4. Scope: `repo` (write access)
5. Click **Create** and copy the token

### 2. Authenticate Locally

**Using HF CLI (recommended):**
```bash
hf auth login
# Paste the NEW token when prompted
```

**Or configure Git manually:**
```bash
git config --global credential.helper store
```

### 3. Add Remote & Push

```bash
git remote add hf https://huggingface.co/spaces/sigma10goat/sitech_smart_farm
# or if hf remote exists:
git remote set-url hf https://huggingface.co/spaces/sigma10goat/sitech_smart_farm

git push hf main
```

### 4. Monitor Build

- Open https://huggingface.co/spaces/sigma10goat/sitech_smart_farm
- Watch the build log
- Fix any errors and push again

---

## Option 2: Use SSH

### 1. Add SSH Key to HF Account

1. Generate SSH key (if you don't have one):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/hf_key -N ""
   ```

2. Add public key to https://huggingface.co/settings/ssh

### 2. Update Remote to SSH

```bash
git remote set-url hf git@huggingface.co:spaces/sigma10goat/sitech_smart_farm

git push hf main
```

---

## Option 3: Manual Web Upload (HF Spaces UI)

1. Open https://huggingface.co/spaces/sigma10goat/sitech_smart_farm
2. Click "Files" tab
3. Upload or edit:
   - `Dockerfile`
   - `main.py`
   - `requirements.txt`
   - `.dockerignore`
   - `.gitignore`
4. Commit changes via the UI

---

## Environment Setup & Secrets

### Add MQTT Credentials (if needed)

In the Space UI → **Settings → Secrets**, add:
- `MQTT_BROKER`: Your MQTT broker address
- `MQTT_PORT`: MQTT port (default 1883)
- `MQTT_USER`: MQTT username
- `MQTT_PASSWORD`: MQTT password

These will be available as environment variables in the Docker container.

### Port Configuration

- Hugging Face Spaces automatically sets `PORT=7860`
- The `Dockerfile` and `main.py` already use this env var
- No manual config needed

---

## Local Testing (Optional)

Test the Docker image locally before pushing:

```bash
# Build
docker build -t smart-farm-dashboard .

# Run
docker run -e PORT=7860 -p 7860:7860 smart-farm-dashboard

# Open browser
# http://localhost:7860
```

---

## Troubleshooting

### Push fails with "unauthorized"

- Token doesn't have `repo` (write) scope → Create a new token with write scope
- Token is read-only → Delete and create a new write-capable token
- Credentials not saved → Run `hf auth login` with the new token

### Build fails in Space

- Check build log for missing dependencies → Update `requirements.txt`
- Check for Python/system errors → Review logs and push fixes
- Port conflicts → `main.py` already handles `PORT` env var

### App doesn't start

- Make sure `main.py` accepts `--port` or `PORT` env var (already done)
- Check MQTT connection requirements in Space secrets
- Review Space logs for runtime errors

---

## Files Modified for Deployment

- `Dockerfile` — Docker container definition for Spaces
- `main.py` — Updated to read `PORT` env var and `--port` CLI arg
- `.dockerignore` — Excludes unnecessary files from Docker build
- `.gitignore` — Now ignores database files (*.db, *.sqlite, etc.)
- `requirements.txt` — Python dependencies (existing)

---

## Next Steps

1. **Create a write token** at https://huggingface.co/settings/tokens
2. **Log in**: `hf auth login` (or use SSH)
3. **Push**: `git push hf main`
4. **Monitor**: Watch build in Space UI
5. **Add secrets** (MQTT creds) in Space settings if needed
6. **Access your app** at your Space URL once deployed

---

## Useful Links

- HF Spaces Docs: https://huggingface.co/docs/hub/spaces
- HF CLI Docs: https://huggingface.co/docs/hub/cli-main
- Docker Docs: https://docs.docker.com
- Panel (Bokeh) Deployment: https://panel.holoviz.org/getting_started/index.html
