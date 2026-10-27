# God's Eye View — Command Cheat Sheet

Quick reference for running this project on Windows.

- **Project folder:** `D:\Projects\gods-eye-view`
- **App address:** http://localhost:4173
- **Node.js:** 24.x (24.14.0 or later) or 26.x. Don't use 25.

Run every command from the project folder in PowerShell, Command Prompt,
Git Bash or the VS Code terminal:

```bash
cd D:\Projects\gods-eye-view
```

> If a terminal says `node` or `npm` is not recognized, close it and open a
> new one. Terminals opened before Node.js was installed don't know where it is.

---

## Start

```bash
npm run dev
```

Wait for `Local: http://localhost:4173/`, then open that address in your
browser. Keep the terminal window open while you use the app.

## Stop

In the terminal that is running the app, press **Ctrl + C**. Answer `Y` if
asked "Terminate batch job?". Closing that terminal window also stops it.

### If the app won't stop or port 4173 is already in use

Find what is using the port (PowerShell):

```powershell
Get-NetTCPConnection -LocalPort 4173 -State Listen | Select-Object OwningProcess
```

Stop that process, replacing `12345` with the number shown:

```powershell
Stop-Process -Id 12345
```

## Restart

Press **Ctrl + C**, then run `npm run dev` again. Restart after you change the
`.env` file.

---

## Check that everything is set up

```bash
npm run doctor
```

Checks Node, npm and dependencies, and lists which data providers have keys.

## Reinstall dependencies

Use this if the app errors after an update or `node_modules` looks broken:

```bash
npm ci
```

---

## Update to the newest version

Your fork has two remotes: `origin` (your copy on GitHub) and `upstream` (the
original project by bilawalsidhu).

```bash
git pull upstream main
```

```bash
npm ci
```

```bash
npm run doctor
```

Push the update to your fork on GitHub:

```bash
git push origin main
```

You can also click **Sync fork** on https://github.com/thompsojmd-md/gods-eye-view
and then run `git pull` here.

---

## API keys (optional)

The app works without keys. Keys unlock extra layers:

| Feature                  | Key in `.env`                 |
| ------------------------ | ----------------------------- |
| Photorealistic 3D globe  | `CESIUM_ION_TOKEN` or `GOOGLE_MAPS_API_KEY` |
| Ships / vessels          | `AISSTREAM_API_KEY`           |
| Wildfires                | `FIRMS_MAP_KEY`               |
| Voice assistant          | `OPENAI_API_KEY`              |
| Street-level imagery     | `MAPILLARY_CLIENT_TOKEN`      |
| Better flight rate limits| `OPENSKY_CLIENT_ID` / `OPENSKY_CLIENT_SECRET` |

**Easiest:** open the app and use the **POWER UP** panel at the bottom right.

**Or with a file:** copy the template, then edit `.env` and fill in the keys
you have:

```bash
copy .env.example .env
```

Restart the app after editing `.env`. The `.env` file is ignored by git, so your
keys are never pushed to GitHub. Don't share it.

> Keep the app bound to `localhost`, which is the default. The dev server uses
> your keys, so anyone who can reach it can spend your quota.

---

## Other commands

| Command              | What it does                                         |
| -------------------- | ---------------------------------------------------- |
| `npm run build`      | Builds a production copy into the `dist` folder      |
| `npm run preview`    | Serves that production build locally                 |
| `npm test`           | Runs the project's unit tests                        |
| `npm run format`     | Auto-formats the code                                |
| `npm run mcp`        | Starts the MCP server so AI assistants can drive the app |

## Change the port

Set `PORT` in `.env` (for example `PORT=5000`), then restart. The app is then
at `http://localhost:5000`.
