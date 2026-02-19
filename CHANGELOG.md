# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [0.2.0] - Planned

### Added
- `migrate` command for remote agent migration via SSH
- `list` command to show available agents
- Encryption support for sensitive backups
- Compression level options
- Progress bars for large operations

## [0.3.0] - Planned

### Added
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
- Migrate command not yet implemented
- No encryption for sensitive data
- Requires manual PATH setup for global access
