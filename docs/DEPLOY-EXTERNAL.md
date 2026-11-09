# Make your private God's Eye View available externally

Target: a Linux VPS (AWS Lightsail), Docker, Caddy for HTTPS + login. Cloudflare Tunnel alternative at the end.

## Read first: what the repo says about this

- The app is the Vite server (client + API proxies in one process). `SECURITY.md`: it is a dev/preview server, **no built-in auth**. If you expose it, put your own auth in front.
- A reachable server **brokers every key in `.env`** to whoever reaches it. Auth in front is mandatory, not optional.
- Behind a reverse proxy, the cost-bearing endpoints **refuse requests carrying forwarding headers** (`X-Forwarded-*` etc.) with `403`: voice (`/api/realtime/*`), AI HUD, Google Places/search, Mapillary, TomTom. Keyless layers (flights, ships, satellites, quakes, CCTV, transit, terrain) work. This is deliberate; don't strip the headers to get around it. If you need voice remotely, run the app locally and use it from there.
- Provider Settings (POWER UP) refuses proxied requests. Keys go in `.env` by hand.
- Browser-exposed keys (Google Maps, Cesium ion, Mapillary) are visible in devtools. Restrict them at the provider (HTTP referrer = your domain).

## Plan

- [ ] 1. VPS + DNS
- [ ] 2. App up on loopback via Docker
- [ ] 3. Caddy with HTTPS + basic auth in front
- [ ] 4. Lock down firewall, keys, spend limits
- [ ] 5. Verify

## 1. VPS + DNS

1. Lightsail instance: Ubuntu 24.04, 2 GB RAM minimum (4 GB comfortable; `npm ci` + Vite optimizer is heavy). Attach a **static IP**.
2. Lightsail firewall: allow only TCP 22 (restrict to your IP), 80, 443. **Do not open 4173.**
3. DNS: `A` record `globe.example.com` -> static IP. In Cloudflare, set it to **DNS only** (grey cloud) for now; Cloudflare's proxy adds forwarding headers too, and Caddy needs to see the ACME challenge.

Install Docker + Caddy:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update && sudo apt-get install -y caddy
```

## 2. App on loopback

```bash
git clone <your-repo-url> gods-eye-view && cd gods-eye-view
cat > .env <<'EOF'
# Required for a proxied instance
GEV_ALLOWED_HOSTS=globe.example.com
GEV_KEY_SETUP_TRUSTED_PEERS=none

# Keys: only the ones you want exposed through the proxy
CESIUM_ION_TOKEN=...            # public assets:read token, URL-restricted to globe.example.com
GOOGLE_MAPS_API_KEY=...         # referrer-restricted to globe.example.com (Map Tiles + Maps JS only)
# Tighten throttles for a non-localhost instance
GEV_RATELIMIT_GOOGLE_PER_MIN=60
EOF
chmod 600 .env
env UID=$(id -u) GID=$(id -g) docker compose up -d --build
docker compose logs -f   # wait for the Vite "Local:" line, Ctrl+C to leave
```

`compose.yaml` already publishes `127.0.0.1:4173` only. **Leave it that way**: Caddy on the same host is the only way in. Check:

```bash
curl -sI http://127.0.0.1:4173/ | head -1     # 200
curl -sI http://<public-ip>:4173/ | head -1   # must fail
```

## 3. Caddy: HTTPS + login

```bash
caddy hash-password        # type a long passphrase, copy the hash
sudo tee /etc/caddy/Caddyfile >/dev/null <<'EOF'
globe.example.com {
    basic_auth {
        john PASTE_HASH_HERE
    }
    reverse_proxy 127.0.0.1:4173
}
EOF
sudo systemctl reload caddy
```

Caddy gets a Let's Encrypt cert automatically. The Vite dev client uses a websocket; Caddy proxies it with no extra config.

Basic auth is fine for one user over HTTPS. For more people or SSO, use Cloudflare Access (below) or `forward_auth` to an auth service.

## 4. Lock down

- Provider spend limits are the real backstop (app throttles are per-IP, in-memory, reset on restart): OpenAI usage limit, Google Cloud budget alerts + per-API quotas.
- Google key: HTTP referrer `https://globe.example.com/*`, API restriction Map Tiles + Maps JavaScript only. Cesium token: `assets:read`, URL-restricted.
- Keep `.env` `chmod 600`, never commit it (already gitignored).
- `sudo apt-get install -y unattended-upgrades`. Pull and rebuild periodically: `git pull && docker compose up -d --build` (after dependency changes: `docker compose down -v && docker compose up -d --build`).
- Rate-limit brute force on the login: `fail2ban` against Caddy logs, or use Access below.

## 5. Verify

```bash
curl -sI https://globe.example.com/                 # 401 without credentials
curl -sI -u john https://globe.example.com/ | head -1   # 200
```

In a browser: log in, globe loads, a keyless layer (Earthquakes, Satellites) shows data. Expected: voice and Google place search return `403` behind the proxy (see above). Optionally check an unauthenticated request to `https://globe.example.com/api/flights` is also `401`.

## Alternative: Cloudflare Tunnel + Access (no open ports)

1. Run the app as in step 2 (loopback only, no Caddy, firewall can close 80/443).
2. Zero Trust dashboard -> Networks -> Tunnels -> create tunnel, install `cloudflared` on the VPS, add public hostname `globe.example.com` -> `http://127.0.0.1:4173`.
3. Zero Trust -> Access -> Applications -> self-hosted app for `globe.example.com`, policy: allow only your email (one-time PIN or your IdP).
4. Same `.env` as above (`GEV_ALLOWED_HOSTS=globe.example.com`). Same forwarding-header caveat applies.

Do **not** use Pinokio's built-in LAN/Cloudflare sharing: the launcher deliberately disables it.

## Not verified

Written from the repo's Dockerfile, compose, `README.md` and `SECURITY.md`; I did not deploy it. Unconfirmed: whether any specific layer you rely on needs a key-bearing endpoint (those 403 behind a proxy). Check `DATA_SOURCES.md` for the 🟢 (keyless) layers.
