# OpenClaw Agent BRM

**Backup, Recovery, and Migration tool for OpenClaw Agents**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/jp-moregain/openclaw-brm)

A command-line tool to backup, restore, and migrate your OpenClaw agents between systems.

## 🚀 Features

- **Backup**: Create compressed archives of your agents with all configurations
- **Restore**: Recover agents from backups to any location
- **Migrate**: Move agents between systems via SSH/SCP (NEW in v0.2.0!)
- **List**: View all configured agents at a glance (NEW in v0.2.0!)
- **Dry-run**: Preview operations before executing
- **Smart Detection**: Automatically finds agent workspaces
- **Config Preservation**: Maintains openclaw.json entries

## 📦 Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/jp-moregain/openclaw-brm.git
cd openclaw-brm

# Make executable
chmod +x src/openclaw-brm.py

# Optional: Add to PATH
sudo ln -s $(pwd)/src/openclaw-brm.py /usr/local/bin/openclaw-brm
```

### Requirements

- Python 3.8 or higher
- OpenClaw installed and configured

## 🎯 Quick Start

### Backup an Agent

```bash
# Backup to default filename (agent_id_TIMESTAMP.oca)
./openclaw-brm.py backup drpowerscale

# Backup to specific file
./openclaw-brm.py backup drpowerscale -o my_backup.oca

# Preview what would be backed up
./openclaw-brm.py backup drpowerscale --dry-run

# Exclude knowledge directory
./openclaw-brm.py backup drpowerscale --no-knowledge
```

### Restore an Agent

```bash
# Restore to original location
./openclaw-brm.py restore drpowerscale_20260219_165613.oca

# Restore to custom directory
./openclaw-brm.py restore backup.oca --target-dir ./my_agent

# Preview restore
./openclaw-brm.py restore backup.oca --dry-run
```

### Migrate an Agent (NEW!)

```bash
# Migrate to remote host
./openclaw-brm.py migrate drpowerscale --to user@remote-server

# Migrate and keep local copy
./openclaw-brm.py migrate drpowerscale --to user@remote-server --keep-local

# Preview migration
./openclaw-brm.py migrate drpowerscale --to user@remote-server --dry-run

# Specify remote directory
./openclaw-brm.py migrate drpowerscale --to user@remote-server --remote-dir /opt/agents
```

### List Agents (NEW!)

```bash
# List all configured agents
./openclaw-brm.py list
```

## 📋 Commands

### `backup <agent_id>`

Create a backup archive of an OpenClaw agent.

**Options:**
- `-o, --output`: Output file path (default: `agent_id_TIMESTAMP.oca`)
- `--no-knowledge`: Exclude knowledge directory from backup
- `--dry-run`: Preview what would be backed up

### `restore <archive>`

Restore an agent from a backup archive.

**Options:**
- `--target-dir`: Target directory for restoration (default: original path)
- `--dry-run`: Preview restore without making changes

### `migrate <agent_id>`

Migrate an agent to a remote host via SSH/SCP.

**Options:**
- `--to` (required): Remote host (`user@hostname` or `hostname`)
- `--remote-dir`: Remote directory for temporary backup (default: `~/.openclaw/migrations/`)
- `--keep-local`: Keep local agent after migration (default: remove after verification)
- `--dry-run`: Preview migration without executing

**Requirements:**
- SSH access to remote host
- OpenClaw installed on remote host (for auto-restore)

### `list`

List all configured agents from openclaw.json.

Shows agent ID, name, workspace path, and whether the workspace exists.

## 📁 Archive Format (.oca)

OpenClaw Agent archives are gzipped tar files containing:

```
agent_name.oca
├── manifest.json          # Backup metadata
└── workspace/             # Agent workspace
    ├── SOUL.md
    ├── MEMORY.md
    ├── IDENTITY.md
    ├── USER.md
    ├── ACCESS.md
    ├── RAG.md
    ├── AGENTS.md
    ├── TOOLS.md
    ├── HEARTBEAT.md
    ├── knowledge/         # RAG knowledge base
    └── memory/            # Daily memory files
```

## 🔧 Configuration

The tool automatically detects:
- OpenClaw installation directory (`~/.openclaw`)
- Agent workspaces from `openclaw.json`
- Associated cron jobs

## 🛡️ Safety Features

- **Dry-run mode**: Preview all operations before executing
- **Overwrite protection**: Prompts before overwriting existing workspaces
- **Automatic backup**: Backs up existing workspaces before overwriting
- **Manifest validation**: Verifies archive integrity

## 📝 Example Workflow

```bash
# 1. Backup your agent
./openclaw-brm.py backup drpowerscale -o drpowerscale_v1.oca

# 2. Test restore to different location
./openclaw-brm.py restore drpowerscale_v1.oca --target-dir /tmp/test_restore --dry-run

# 3. Actually restore
./openclaw-brm.py restore drpowerscale_v1.oca --target-dir /tmp/test_restore

# 4. Verify restored files
ls -la /tmp/test_restore/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Created for the [OpenClaw](https://github.com/openclaw/openclaw) community
- Inspired by the need for agent portability and backup

## 📧 Support

- GitHub Issues: [Report a bug or request a feature](https://github.com/jp-moregain/openclaw-brm/issues)
- Discussions: [Ask questions or share ideas](https://github.com/jp-moregain/openclaw-brm/discussions)

---

**Made with ❤️ for the OpenClaw community**
