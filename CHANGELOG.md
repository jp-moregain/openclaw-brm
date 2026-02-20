# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-20

### Added
- `migrate` command for remote agent migration via SSH/SCP
  - Backup agent locally
  - Transfer to remote host via SCP
  - Auto-restore on remote (if openclaw-brm available)
  - Verify remote restore before removing local copy
  - `--keep-local` option to preserve local agent
  - `--remote-dir` option to specify remote path
- `list` command to show all configured agents
  - Shows agent ID, name, workspace path
  - Indicates if workspace exists (✓/✗)
  - Clean tabular output
- `--version` flag to show version info

### Changed
- Updated help text with examples for all commands
- Enhanced dry-run mode for migrate command
- Version bumped to 0.2.0

## [0.1.0] - 2026-02-19

### Added
- Initial release of OpenClaw Agent BRM
- `backup` command to create agent archives (.oca files)
- `restore` command to restore agents from archives
- Dry-run mode for both backup and restore operations
- Automatic workspace detection
- openclaw.json integration
- Knowledge directory backup/restore
- Safety features (overwrite protection, backups)

### Features
- Backup all agent configuration files (SOUL.md, MEMORY.md, etc.)
- Include/exclude knowledge directory
- Restore to original or custom location
- Manifest-based archive format
- Colored terminal output

## [0.3.0] - Planned

### Added
- Encryption support for sensitive backups
- Compression level options
- Progress bars for large operations
- Web UI for visual agent management
- Two-way sync between instances
- Scheduled backups (cron integration)
- Cloud storage support (S3, etc.)

---

## Release Notes

### v0.1.0 MVP
First working version with backup and restore functionality. Tested with:
- Dr. PowerScale agent backup/restore
- Knowledge directory preservation
- openclaw.json integration

**Known Limitations:**
- No encryption for sensitive data (coming in v0.3.0)
- Requires SSH key auth for seamless migration (password auth may prompt interactively)
- Remote host must have OpenClaw installed for auto-restore (otherwise manual extraction)
- Requires manual PATH setup for global access
