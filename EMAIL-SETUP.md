# Daily Email Summary Setup

Daily portfolio summary email at **12:30 PM PT**. Fetches live prices, generates HTML email, sends automatically.

---

## Step 1: Generate Gmail App Password

Gmail requires an **app-specific password** (not your regular password).

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - May need to enable 2FA first if not already done
2. Select: **Mail** + **macOS**
3. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

---

## Step 2: Update the Plist with Your Password

Edit the plist and replace the placeholder:

```bash
nano ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
```

Find this line:
```xml
<string>YOUR_GMAIL_APP_PASSWORD_HERE</string>
```

Replace with your 16-char password (remove spaces):
```xml
<string>abcdefghijklmnop</string>
```

Save: `Ctrl+X` → `Y` → Enter

---

## Step 3: Install and Load Launchd

```bash
# Copy plist
cp scripts/com.sergey.investments-monitor.email.plist ~/Library/LaunchAgents/

# Load it
launchctl load ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist

# Verify it's running
launchctl list | grep investments-monitor
```

Expected output:
```
-	0	com.sergey.investments-monitor.email
```

---

## Step 4: Test It (Optional)

Run the script manually to verify it works:

```bash
python3 scripts/email_summary.py
```

Should see in terminal:
```
2026-04-24 12:30:00,123 — INFO — Loading holdings...
2026-04-24 12:30:05,456 — INFO — Fetching live prices...
2026-04-24 12:30:10,789 — INFO — Sending email to sergey.pochikovskiy@gmail.com...
2026-04-24 12:30:11,234 — INFO — ✓ Email sent successfully
```

Email should arrive in your inbox within seconds.

---

## What's in the Email

✅ **Header:** Portfolio value, P/L, leverage, net worth  
✅ **Allocations:** Asset class breakdown (bars) + account breakdown  
✅ **Top 8 holdings:** Ticker, market value, P/L, % of portfolio  
✅ **Watchlist:** Top 5 favorites with current vs. target price  
✅ **FX rate:** Latest USD/CAD (for reference)  
✅ **Timestamp:** When email was generated

---

## Daily Automation

Every day at **12:30 PM PT**, launchd will:
1. Run `email_summary.py`
2. Fetch live prices from yfinance
3. Fetch FX from BOC
4. Generate HTML email
5. Send to your inbox

**Your Mac just needs to be on.** No terminal, no manual trigger.

---

## Logs

Check if the script ran successfully:

```bash
tail ~/.logs/investments-monitor-email.log
```

If there are errors:
```bash
tail ~/.logs/investments-monitor-email-error.log
```

---

## Managing the Scheduler

### Check if it's running:
```bash
launchctl list | grep investments-monitor
```

### Unload (pause) it:
```bash
launchctl unload ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
```

### Reload (resume) it:
```bash
launchctl load ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
```

### Remove it entirely:
```bash
launchctl unload ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
rm ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
```

---

## Changing the Email Time

Edit the plist to change when the email sends:

```bash
nano ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
```

Find:
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>12</integer>
    <key>Minute</key>
    <integer>30</integer>
</dict>
```

- `Hour`: 0–23 (0 = midnight, 12 = noon, 17 = 5pm)
- `Minute`: 0–59

Save and reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
launchctl load ~/Library/LaunchAgents/com.sergey.investments-monitor.email.plist
```

---

## Troubleshooting

### "Email send failed: (535, b'5.7.8 Username and App password not accepted')"
- **Cause:** Wrong Gmail app password
- **Fix:** Regenerate app password and update plist

### "Email send failed: No such file or directory"
- **Cause:** Script path in plist is wrong (system may have different path)
- **Fix:** Check path exists: `ls /Users/sergeypochikovskiy/AI_workspace/Projects/4\ Investments\ Monitor/scripts/email_summary.py`

### "Price fetch failed..."
- **Cause:** yfinance down or no internet
- **Fix:** Script uses cached prices as fallback; email still sends
- Check logs: `tail ~/.logs/investments-monitor-email.log`

### "No holdings to email"
- **Cause:** Portfolio.db empty or no holdings imported
- **Fix:** Import data via Settings → Imports tab in the app

---

## Email Recipients

Currently emails to: `sergey.pochikovskiy@gmail.com`

To change, edit the plist or set env var:
```bash
export GMAIL_RECIPIENT="other@example.com"
python3 scripts/email_summary.py
```

---

**Done!** You'll get a polished portfolio email every day at 12:30 PM PT. 📧
