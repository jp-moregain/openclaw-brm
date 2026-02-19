# Example: Backup and Restore Workflow

This example demonstrates a complete backup and restore workflow for an OpenClaw agent.

## Scenario

You have an agent called `drpowerscale` that you want to:
1. Backup before making major changes
2. Test the restore process
3. Restore to a new location

## Step 1: Check Your Agent

First, verify your agent exists:

```bash
ls ~/.openclaw/workspace-drpowerscale/
```

You should see files like:
- SOUL.md
- MEMORY.md
- IDENTITY.md
- knowledge/

## Step 2: Create a Backup

### Basic Backup

```bash
./openclaw-brm.py backup drpowerscale
```

Output:
```
[INFO] Backing up agent: drpowerscale
[OK] Found workspace: /home/ubuntu/.openclaw/workspace-drpowerscale
[OK] Agent config extracted from openclaw.json
[OK] Backup created: drpowerscale_20260219_165613.oca
[INFO] Archive size: 9.5 KB
```

### Backup with Custom Name

```bash
./openclaw-brm.py backup drpowerscale -o drpowerscale_before_update.oca
```

### Preview Backup (Dry Run)

```bash
./openclaw-brm.py backup drpowerscale --dry-run
```

Output:
```
[INFO] Backing up agent: drpowerscale
[WARN] DRY RUN MODE - No files will be created
[OK] Found workspace: /home/ubuntu/.openclaw/workspace-drpowerscale
==================================================
[INFO] DRY RUN SUMMARY
==================================================
[INFO] Agent: drpowerscale
[INFO] Workspace: /home/ubuntu/.openclaw/workspace-drpowerscale
[INFO] Files to backup: 11
[INFO] Output file: drpowerscale_20260219_165614.oca
[INFO] Include knowledge: True
[INFO] Cron jobs: 0
==================================================
```

## Step 3: Verify the Backup

Check the archive contents:

```bash
tar -tzf drpowerscale_20260219_165613.oca
```

You should see:
```
./
./manifest.json
./workspace/
./workspace/SOUL.md
./workspace/MEMORY.md
...
```

## Step 4: Test Restore (Dry Run)

Before actually restoring, preview what would happen:

```bash
./openclaw-brm.py restore drpowerscale_20260219_165613.oca --target-dir /tmp/test_restore --dry-run
```

## Step 5: Restore to Test Location

Restore the agent to a temporary location:

```bash
./openclaw-brm.py restore drpowerscale_20260219_165613.oca --target-dir /tmp/test_restore
```

Output:
```
[INFO] Restoring from archive: drpowerscale_20260219_165613.oca
[OK] Manifest read: Agent drpowerscale
[INFO] Original workspace: /home/ubuntu/.openclaw/workspace-drpowerscale
[INFO] Files in archive: 11
[OK] Agent restored to: /tmp/test_restore
[INFO] Agent drpowerscale already in openclaw.json
```

## Step 6: Verify Restored Files

Check the restored files:

```bash
ls -la /tmp/test_restore/
```

Compare with original:

```bash
diff ~/.openclaw/workspace-drpowerscale/SOUL.md /tmp/test_restore/SOUL.md
```

## Step 7: Clean Up Test Restore

Remove the test restore:

```bash
rm -rf /tmp/test_restore
```

## Step 8: Restore Over Original (if needed)

If you need to restore over the original workspace:

```bash
./openclaw-brm.py restore drpowerscale_20260219_165613.oca
```

You'll be prompted:
```
[WARN] Workspace already exists: /home/ubuntu/.openclaw/workspace-drpowerscale
Overwrite? (y/N): y
[INFO] Existing workspace backed up to: workspace-drpowerscale_backup_20260219_165615
[OK] Agent restored to: /home/ubuntu/.openclaw/workspace-drpowerscale
```

## Complete Workflow Script

Here's a complete script for automated backup:

```bash
#!/bin/bash

AGENT_NAME="drpowerscale"
BACKUP_DIR="$HOME/openclaw-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup agent
./openclaw-brm.py backup "$AGENT_NAME" -o "$BACKUP_DIR/${AGENT_NAME}_${DATE}.oca"

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t ${AGENT_NAME}_*.oca | tail -n +11 | xargs -r rm

echo "Backup complete: $BACKUP_DIR/${AGENT_NAME}_${DATE}.oca"
```

## Tips

1. **Always use dry-run first** when trying new operations
2. **Keep multiple backups** with timestamps
3. **Test restores regularly** to ensure backups are valid
4. **Back up before major changes** to agent configuration
5. **Use descriptive backup names** for important milestones

## Troubleshooting

### Agent Not Found

If you get "Agent workspace not found":

```bash
# Check if agent exists
ls ~/.openclaw/ | grep drpowerscale

# Check openclaw.json
 cat ~/.openclaw/openclaw.json | grep -A5 drpowerscale
```

### Archive Corrupted

If restore fails:

```bash
# Verify archive integrity
tar -tzf drpowerscale_20260219_165613.oca > /dev/null && echo "Archive OK"

# Extract manually to inspect
tar -xzf drpowerscale_20260219_165613.oca -C /tmp/inspect/
cat /tmp/inspect/manifest.json
```
