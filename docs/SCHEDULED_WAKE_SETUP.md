# Scheduled Wake/Sleep Setup Guide

**Purpose:** Configure your Mac to automatically wake for the overnight workflow, then return to sleep
**Date:** October 9, 2025
**Estimated Cost:** ~$0.20/month in electricity

---

## Quick Setup (2 minutes)

### Step 1: Run the Configuration Script

Open Terminal and run:

```bash
cd /Users/ryanranft/nba-simulator-aws
sudo bash scripts/setup/configure_scheduled_wake.sh
```

**You will be prompted for your admin password.**

The script will:
- Configure daily wake at 2:55 AM (5 min before workflow)
- Enable Power Nap
- Display current configuration

---

### Step 2: Verify Configuration

After running the script, verify with:

```bash
pmset -g sched
```

**Expected output:**
```
Scheduled power events:
 wakeorpoweron at 02:55:00 every day
```

---

### Step 3: Tonight - Just Sleep Your Mac

**Before bed:**
- Close your laptop lid (or let it sleep normally)
- **Do NOT shut down**

**What happens overnight:**
1. **2:55 AM** - Mac wakes from sleep
2. **3:00 AM** - Overnight workflow runs (~6 minutes)
3. **3:06 AM** - Workflow completes
4. Mac returns to sleep automatically

**Tomorrow morning:**
```bash
bash scripts/monitoring/check_overnight_status.sh
```

Expected: `✅ Overnight workflow is running successfully`

---

## How It Works

### Power Management

**Sleep mode vs Shutdown:**
- **Sleep:** 1-2 watts, ~$0.20/month
- **Wake at scheduled time:** Mac wakes automatically
- **After workflow:** Returns to sleep

**Why this is better than shutdown:**
- No manual intervention needed
- No password storage required
- Completely secure
- Negligible power cost
- macOS designed for this use case

### Scheduled Wake Details

**Schedule:** Every day at 2:55 AM (MTWRFSU)
- Monday through Sunday
- Wakes 5 minutes before workflow
- Ensures Mac is fully awake when job starts

**Power Nap enabled:**
- Allows certain low-power tasks during sleep
- Improves wake reliability
- macOS feature designed for this

---

## Troubleshooting

### Mac didn't wake overnight

**Check scheduled events:**
```bash
pmset -g sched
```

**Re-run configuration if missing:**
```bash
sudo bash scripts/setup/configure_scheduled_wake.sh
```

**Common issues:**
1. **Mac was shut down (not sleeping)** → Must sleep, not shutdown
2. **Scheduled event removed** → Re-run setup script
3. **Battery-only wake disabled** → Some Macs only wake when plugged in

---

### Check if Mac woke overnight

**View wake history:**
```bash
pmset -g log | grep -E "Wake from|Sleep" | tail -20
```

Look for wake event around 2:55 AM.

---

### Mac won't stay asleep

**If Mac keeps waking randomly:**
```bash
# Check what's waking your Mac
pmset -g assertions

# View wake reasons
pmset -g log | grep -E "Wake.*due to" | tail -10
```

**Common culprits:**
- Network activity (disable "Wake for network access" if needed)
- Bluetooth devices
- External drives

**Fix:**
```bash
# Disable wake for network access (if problematic)
sudo pmset -a womp 0

# Keep wake for power button
sudo pmset -a powerbuttonwake 1
```

---

### Workflow didn't run despite wake

**Verify launchd job loaded:**
```bash
launchctl list | grep nba-simulator
```

**Expected:** `-	0	com.nba-simulator.overnight-workflow`

**If not loaded:**
```bash
launchctl load ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

**Check stderr log:**
```bash
cat /tmp/overnight_workflow_stderr.log
```

---

## Advanced Configuration

### Wake Only on Weekdays

If you only want automation during the work week:

```bash
# Monday through Friday only
sudo pmset repeat wakeorpoweron MTWRF 02:55:00
```

### Multiple Wake Times

Schedule multiple daily wakes:

```bash
# Morning and evening
sudo pmset repeat wakeorpoweron MTWRFSU 02:55:00
sudo pmset repeat wakeorpoweron MTWRFSU 18:00:00
```

**Note:** Only one repeat schedule at a time. For multiple, use energy schedule in System Settings.

### Wake Only When Plugged In

Some MacBooks only support scheduled wake when connected to power:

**Check capability:**
```bash
pmset -g cap
```

Look for `womp` (Wake on Magic Packet) and `acwake` (AC Wake).

**If limited to AC power:**
- Keep laptop plugged in overnight
- Or change workflow schedule to daytime hours

---

## Power Consumption Details

### Sleep Mode Power Usage

**Modern MacBooks:**
- Standby mode: ~0.5-1 watts
- Sleep mode: ~1-2 watts

**Desktop Macs:**
- Sleep mode: ~2-4 watts

### Cost Calculations

**Assuming 1.5 watts average:**
- Daily: 1.5W × 24h = 36 Wh = 0.036 kWh
- Monthly: 0.036 × 30 = 1.08 kWh
- Cost (at $0.12/kWh): 1.08 × $0.12 = **$0.13/month**

**Annual cost:** ~$1.56

**Comparison:**
- Keeping Mac on 24/7: ~$15-30/month
- Sleep mode with scheduled wake: ~$0.13-0.20/month
- **Difference:** Negligible

---

## Removing Scheduled Wake

If you want to disable automatic wake:

```bash
# Remove all scheduled wakes
sudo pmset repeat cancel

# Verify removal
pmset -g sched
```

You can still manually trigger the workflow anytime:
```bash
launchctl start com.nba-simulator.overnight-workflow
```

---

## Alternative: Energy Schedule (GUI)

You can also configure via System Settings:

**macOS Ventura/Sonoma:**
1. System Settings → Lock Screen → (Scroll down)
2. "Put display to sleep after..." settings
3. Click "Schedule" button
4. Add wake schedule

**Note:** GUI method may not be as reliable as `pmset` command for automation.

---

## Verification Checklist

After setup, verify all components:

- [ ] Scheduled wake configured: `pmset -g sched`
- [ ] Power Nap enabled: `pmset -g | grep powernap`
- [ ] launchd job loaded: `launchctl list | grep nba-simulator`
- [ ] Monitoring script works: `bash scripts/monitoring/check_overnight_status.sh`
- [ ] Test manual trigger successful (already done)

**All checked?** ✅ Ready for automatic overnight execution!

---

## FAQ

### Q: Will this drain my battery?
**A:** No. Sleep mode uses minimal power (~1-2 watts). A fully charged MacBook can stay in sleep mode for weeks.

### Q: What if I shut down by mistake?
**A:** The workflow won't run. Just manually trigger it later:
```bash
launchctl start com.nba-simulator.overnight-workflow
```

### Q: Can I use my Mac during the workflow?
**A:** Yes. The workflow runs in the background. You can work normally, but it may slow down slightly for ~6 minutes.

### Q: What if I'm traveling?
**A:** Mac will wake at 2:55 AM local time. If you prefer, temporarily disable scheduled wake:
```bash
sudo pmset repeat cancel
```

### Q: Does this work on battery?
**A:** Depends on your Mac model. Most modern MacBooks support it. Desktop Macs require AC power. Check with `pmset -g cap`.

### Q: Can I change the wake time?
**A:** Yes! Edit and re-run:
```bash
# Example: Wake at 7:55 AM instead
sudo pmset repeat wakeorpoweron MTWRFSU 07:55:00
```

---

## Related Documentation

- **Overnight Workflow Guide:** `scripts/workflows/OVERNIGHT_SCHEDULING_GUIDE.md`
- **Verification Checklist:** `docs/OVERNIGHT_VERIFICATION_CHECKLIST.md`
- **Monitoring Script:** `scripts/monitoring/check_overnight_status.sh`

---

**Last Updated:** October 9, 2025
**Version:** 1.0
**Status:** Ready for production use
