# TN Compliance Copilot — v1 app

A FastAPI + SQLite app around the compliance-check feature: enter plot
details, get computed setbacks/FSI/parking, a buildable-envelope preview,
and DXF + PDF exports. Every check is saved so history persists.

## Structure

```
app/
  main.py                  # app entrypoint, registers feature routers
  database.py               # SQLite/SQLAlchemy setup
  features/
    compliance/              # the one feature so far
      rules.py                 # TNCDBR rule tables + compute_compliance()
      models.py                # ComplianceCheck DB model
      schemas.py                # request/response validation
      dxf_export.py             # DXF generation (ezdxf)
      pdf_export.py             # PDF report generation (fpdf2)
      router.py                 # /api/compliance/* endpoints
static/                    # frontend (plain HTML/CSS/JS, no build step)
```

Adding the next feature (CMDA/GCC jurisdictions, sketch upload, accounts)
means adding a new folder under `app/features/` with its own router and
adding one `app.include_router(...)` line in `main.py` — the compliance
feature doesn't need to change.

**Before using this for real work:** `app/features/compliance/rules.py`
carries the setback/FSI/parking figures. They're from secondary TNCDBR
2019 summaries, not the official gazette text — verify and update that
one file once you have confirmed figures; everything else reads from it.

## Run locally (no Docker)

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit http://localhost:8000

## Deploy on an Ubuntu/Debian VPS

This VPS already runs several other services. A port scan
(`sudo ss -tulpn | grep LISTEN`) showed:

- 22 (ssh), 53 (systemd-resolve) — system
- 80, 443 — **Traefik**, already running as a reverse proxy for other apps
- 8000 (127.0.0.1 only), 3000 (127.0.0.1 only), 5432 (127.0.0.1 only), 8080, 8443, 8501, 32768 — other docker services on this box

So: 8000, the app's original default, is taken. **8001 was free** and is
now the default (`docker-compose.yml` / `.env.example`). No domain yet, so
this runs as plain HTTP on that port for now — you'll reach it at
`http://<your-vps-ip>:8001`.

Re-run the port scan before deploying if time has passed, in case
something new has claimed 8001 in the meantime.

### Option A — Docker (recommended, easiest to keep updated)

```
# on the VPS, one-time setup (skip if docker's already installed — it
# clearly is, given the other containers running)
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker

# copy this project to the VPS, e.g. via scp or git clone, then:
cd tn-compliance-app
sudo docker compose up -d --build
```

The app is now running on `http://<your-vps-ip>:8001`. `data/app.db` on
the host persists across container restarts/rebuilds via the volume
mount. If 8001 turns out to be taken too: `cp .env.example .env`, edit
`HOST_PORT` in `.env`, then `docker compose up -d --build` again.

To update after code changes: `sudo docker compose up -d --build` again.

### Option B — systemd, no Docker

```
sudo apt update && sudo apt install -y python3-venv python3-pip

# as a deploy user, in /opt/tn-compliance-app (copy the project there)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Create `/etc/systemd/system/tn-compliance.service`. `--host 0.0.0.0` is
deliberate here — there's no reverse proxy in front of this service yet,
so uvicorn needs to listen on the public interface directly, not just
localhost:

```
[Unit]
Description=TN Compliance Copilot
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/tn-compliance-app
ExecStart=/opt/tn-compliance-app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable --now tn-compliance
```

### Firewall, if you have one enabled

```
sudo ufw allow 8001/tcp
```

(Skip if you're not running ufw — with Traefik already handling 80/443,
you may be relying on Docker's own port publishing instead.)

### When you get a domain later — use Traefik, not nginx

Installing nginx would try to bind port 80, which Traefik already owns on
this box — that install would fail as-is. Since Traefik is already running
and (almost certainly) already using Docker-based service discovery for
your other containers, the natural path is to add Traefik labels to this
app's `docker-compose.yml` instead of introducing a second reverse proxy.

The exact labels depend on how Traefik is already configured on this VPS
(entrypoint names, certificate resolver name, and whether it's on a shared
Docker network) — check the compose file of one of the other services
already running behind it and mirror that pattern. As a starting template:

```yaml
services:
  app:
    build: .
    restart: unless-stopped
    volumes:
      - ./data:/app/data
    networks:
      - traefik-network   # match whatever network your other Traefik services use
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.tn-compliance.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.tn-compliance.entrypoints=websecure"
      - "traefik.http.routers.tn-compliance.tls.certresolver=letsencrypt"
      - "traefik.http.services.tn-compliance.loadbalancer.server.port=8000"

networks:
  traefik-network:
    external: true
```

Once that's wired up and confirmed working, the direct `HOST_PORT` mapping
in the current `docker-compose.yml` can be dropped — Traefik becomes the
only public entry point for this app, same as your other services.

## What's verified vs. not

The compliance rules engine (`rules.py`) was tested directly and produces
identical results to the browser prototype it was ported from, including
a fix for a two-dimensional side-setback lookup bug found during that
testing. The rest of the app (FastAPI routes, DXF/PDF export, SQLite
persistence) was written carefully and syntax-checked, but could not be
run end-to-end in this environment — the sandbox's network policy blocks
PyPI, so FastAPI/ezdxf/fpdf2 couldn't be installed here. Run it locally
or on the VPS first and sanity-check a few checks, exports, and the
history list before treating it as reliable.
