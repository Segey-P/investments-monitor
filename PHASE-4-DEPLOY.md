# Phase 4 Deployment Guide

## Overview

Path C separates local (full data) from cloud (summary only).

- **Local Mac:** `app/main.py` with `IM_DATA_SOURCE=local` (default) reads `data/portfolio.db`
- **Streamlit Cloud:** Second instance with `IM_DATA_SOURCE=cloud` reads `public/summary.json`
- **Refresh:** `scripts/refresh.py` runs daily at 5pm PT (launchd) or manually via GitHub Actions

---

## Step 1: Test Local Refresh Script

```bash
cd ~/AI_workspace/Projects/4\ Investments\ Monitor
python3 scripts/refresh.py
```

Expected output:
- Logs to `scripts/refresh.log`
- Creates/updates `public/summary.json`
- Commits and pushes to GitHub (via SSH)

If it fails, check:
- SSH key is loaded: `ssh-add -l`
- Can access repo: `git push origin main` (from the repo directory)

---

## Step 2: Install launchd Plist (Daily 5pm Refresh)

### Create log directory:
```bash
mkdir -p ~/.logs
```

### Copy plist to LaunchAgents:
```bash
cp scripts/com.sergey.investments-monitor.refresh.plist \
  ~/Library/LaunchAgents/
```

### Load the plist:
```bash
launchctl load ~/Library/LaunchAgents/com.sergey.investments-monitor.refresh.plist
```

### Verify it loaded:
```bash
launchctl list | grep investments-monitor
```

Should output something like:
```
-	0	com.sergey.investments-monitor.refresh
```

### To unload (disable):
```bash
launchctl unload ~/Library/LaunchAgents/com.sergey.investments-monitor.refresh.plist
```

### Check logs:
```bash
tail -f ~/.logs/investments-monitor-refresh.log
tail -f ~/.logs/investments-monitor-refresh-error.log
```

---

## Step 3: Set Up Streamlit Cloud (Second Instance)

### Prerequisites:
- Streamlit Cloud account logged in at [share.streamlit.io](https://share.streamlit.io)
- GitHub repo linked
- SSH key configured for local pushes ✓

### Create the cloud instance:

1. Click **"Create app"** on Streamlit Community Cloud
2. Fill in:
   - **Repository:** `Segey-P/investments-monitor`
   - **Branch:** `main`
   - **Main file path:** `app/main.py`
   - **App name:** `investments-monitor-public` (or your choice)

3. Click **Deploy**

### Configure the instance:

1. Once deployed, click the **⚙ Settings** (gear icon)
2. Go to **Secrets** section
3. Add:
   ```
   IM_DATA_SOURCE = "cloud"
   ```

4. Go to **Advanced settings** → **Password protected app** → Toggle ON
5. Set a password (can be different from local app)

---

## Step 4: Test the Cloud Instance

1. Visit your Streamlit Cloud URL (e.g., `https://investments-monitor-public.streamlit.app`)
2. See the **pre-auth page** with:
   - Allocation breakdowns (by account, asset class, country, currency)
   - Leverage ratio, HELOC utilization, D/E, YTD return
   - Watchlist (top 5 favorites)
   - Last update timestamp
3. Click **Sign in** with the password you set
4. After login, see simplified Dashboard + Holdings (read-only from `public/summary.json`)
5. Click **🔄 Refresh Now** to trigger GitHub Actions

---

## Step 5: GitHub Actions Setup (Manual Refresh from Cloud)

The **"Refresh Now"** button in the cloud app triggers `.github/workflows/refresh.yml`.

### Verify the workflow exists:

Go to **GitHub repo** → **Actions** tab → Should see **"Refresh Portfolio Summary"** workflow.

### Manual trigger test (no button needed yet):

1. Go to GitHub repo → **Actions** tab
2. Select **"Refresh Portfolio Summary"** workflow
3. Click **"Run workflow"** dropdown
4. Click **"Run workflow"** button
5. Should see a new run executing

This manually runs `scripts/refresh.py` on GitHub's servers and commits the result.

---

## Step 6: Connect "Refresh Now" Button to GitHub Actions (Advanced)

The cloud app button needs to trigger GitHub Actions. This requires:

1. **GitHub Personal Access Token** with `repo` + `workflow` scope
2. Store token in Streamlit Cloud **Secrets**:
   ```
   GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
   GITHUB_REPO = "Segey-P/investments-monitor"
   GITHUB_WORKFLOW = "refresh.yml"
   ```

Then the cloud app's "Refresh Now" button calls:
```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GITHUB_REPO/actions/workflows/$GITHUB_WORKFLOW/dispatches \
  -d '{"ref":"main"}'
```

For now, users can manually trigger via GitHub Actions tab. Full integration can be added later.

---

## Testing Checklist

### Local Mode (default):
- [ ] Start app: `streamlit run app/main.py`
- [ ] All 5 tabs load (Dashboard, Holdings, Leverage, Net Worth, Settings)
- [ ] Dashboard shows live prices + allocations
- [ ] Holdings editable
- [ ] Settings → Imports work

### Cloud Mode:
- [ ] Visit cloud app URL
- [ ] Pre-auth page shows allocations + watchlist
- [ ] Sign in with password
- [ ] Dashboard + Holdings tabs load (read-only)
- [ ] No Leverage/Settings/Net Worth tabs visible
- [ ] Stale banner appears if `public/summary.json` is >6h old

### Refresh Pipeline:
- [ ] Manual: `python3 scripts/refresh.py` creates `public/summary.json`
- [ ] Manual: File is committed + pushed to GitHub
- [ ] Scheduled: launchd runs daily at 5pm (check logs)
- [ ] Cloud: Public summary updates after refresh (wait ~30s for Streamlit rebuild)

---

## Troubleshooting

### "refresh.py: git push failed"
- **Cause:** SSH key not loaded
- **Fix:** `ssh-add ~/.ssh/id_ed25519` (or your key path)

### "Streamlit Cloud: ModuleNotFoundError"
- **Cause:** `requirements.txt` missing a dependency
- **Fix:** Add package to `requirements.txt`, commit, cloud will auto-rebuild

### "Stale banner always shows"
- **Cause:** launchd not running or failed silently
- **Fix:** Check logs: `tail ~/.logs/investments-monitor-refresh.log`

### "Cloud app password not working"
- **Cause:** Using local app password instead of cloud password
- **Fix:** Use the password you set in Streamlit Cloud settings

### "Manual refresh button does nothing"
- **Cause:** GitHub token not configured (expected for now)
- **Fix:** Manually trigger via GitHub Actions tab for now

---

## Maintenance

### Daily check:
```bash
tail -1 ~/.logs/investments-monitor-refresh.log
# Should show: "✓ Summary refreshed: 2026-04-24T17:00:00+00:00"
```

### If launchd refresh fails:
1. Check logs
2. Manually run: `python3 scripts/refresh.py`
3. Fix the error (usually SSH key or git config)
4. launchd will retry tomorrow

### Updating the app:
1. Make changes locally
2. Push to GitHub
3. Streamlit Cloud auto-rebuilds
4. Local app reads fresh code on next run

---

## One-Time Manual Refresh (without launchd)

To refresh `public/summary.json` right now:

```bash
cd ~/AI_workspace/Projects/4\ Investments\ Monitor
python3 scripts/refresh.py
```

Then visit the cloud app — it will auto-reload `public/summary.json` within 30s.

---

## File Locations

| File | Purpose |
|------|---------|
| `scripts/refresh.py` | Daily refresh script |
| `scripts/com.sergey.investments-monitor.refresh.plist` | macOS scheduler |
| `.github/workflows/refresh.yml` | GitHub Actions manual trigger |
| `public/summary.json` | Cloud-readable summary (generated) |
| `app/cloud_mode.py` | Cloud mode helpers (load JSON, detect stale) |
| `app/main.py` | Dual-mode entry point (local/cloud toggle) |
| `data/portfolio.db` | Local database (never committed) |
| `~/.logs/investments-monitor-refresh*.log` | Refresh logs |
| `~/Library/LaunchAgents/com.sergey.investments-monitor.refresh.plist` | Active launchd job |

---

## Next: Real Data Testing

Once launchd is running and the cloud app is live:

1. **Week 1:** Verify daily refreshes happen (check `public/summary.json` timestamp)
2. **Week 1:** Test stale detection (unplug Mac for 6+ hours, see banner on cloud)
3. **Week 2:** Monitor for errors in `refresh.log`
4. **Ongoing:** Check cloud app accessibility from phone via Claude mobile app

**You're done! Phase 4 is live. 🚀**
