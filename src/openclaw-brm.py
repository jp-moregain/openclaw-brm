#!/usr/bin/env python3
"""
OpenClaw Agent BRM (Backup, Recovery, Migrate) Tool
Version: 0.1.0 MVP

A command-line tool to backup, restore, and migrate OpenClaw agents.

Usage:
    openclaw-brm backup <agent_id> [options]
    openclaw-brm restore <archive.oca> [options]
    openclaw-brm migrate <agent_id> --to <host> [options]

For more information: https://github.com/yourusername/openclaw-brm
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Constants
VERSION = "0.2.0"
OCA_EXTENSION = ".oca"
OPENCLAW_DIR = Path.home() / ".openclaw"
MANIFEST_FILENAME = "manifest.json"


class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")


def get_agent_workspace(agent_id: str) -> Optional[Path]:
    """Find agent workspace directory"""
    possible_paths = [
        OPENCLAW_DIR / agent_id,
        OPENCLAW_DIR / f"workspace-{agent_id}",
        Path.cwd() / agent_id,
    ]

    config_path = OPENCLAW_DIR / "openclaw.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            agents = config.get("agents", {}).get("list", [])
            for agent in agents:
                if agent.get("id") == agent_id:
                    workspace = agent.get("workspace")
                    if workspace:
                        possible_paths.insert(0, Path(workspace))
        except Exception:
            pass

    for path in possible_paths:
        if path.exists() and path.is_dir():
            if (path / "AGENTS.md").exists() or (path / "SOUL.md").exists():
                return path

    return None


def get_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
    """Extract agent config from openclaw.json"""
    config_path = OPENCLAW_DIR / "openclaw.json"
    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            config = json.load(f)

        agents = config.get("agents", {}).get("list", [])
        for agent in agents:
            if agent.get("id") == agent_id:
                return agent
    except Exception as e:
        log_error(f"Failed to read openclaw.json: {e}")

    return None


def get_agent_cron_jobs(agent_id: str) -> List[Dict[str, Any]]:
    """Get cron jobs associated with agent"""
    cron_path = OPENCLAW_DIR / "cron" / "jobs.json"
    if not cron_path.exists():
        return []

    try:
        with open(cron_path) as f:
            data = json.load(f)

        jobs = data.get("jobs", [])
        return [job for job in jobs if job.get("agentId") == agent_id]
    except Exception as e:
        log_warning(f"Failed to read cron jobs: {e}")
        return []


def create_manifest(agent_id: str, workspace_path: Path,
                    include_knowledge: bool = True) -> Dict[str, Any]:
    """Create backup manifest"""
    return {
        "version": VERSION,
        "created_at": datetime.now().isoformat(),
        "agent_id": agent_id,
        "workspace_path": str(workspace_path),
        "include_knowledge": include_knowledge,
        "files": [],
        "config": {},
        "cron_jobs": []
    }


def backup_agent(agent_id: str, output_file: Optional[str] = None,
                 include_knowledge: bool = True, dry_run: bool = False,
                 include_dirs: Optional[List[str]] = None) -> bool:
    """Backup an OpenClaw agent to .oca file"""

    log_info(f"Backing up agent: {agent_id}")
    if dry_run:
        log_warning("DRY RUN MODE - No files will be created")

    workspace = get_agent_workspace(agent_id)
    if not workspace:
        log_error(f"Agent workspace not found: {agent_id}")
        log_info("Searched in:")
        log_info(f"  - {OPENCLAW_DIR / agent_id}")
        log_info(f"  - {OPENCLAW_DIR / f'workspace-{agent_id}'}")
        return False

    log_success(f"Found workspace: {workspace}")

    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{agent_id}_{timestamp}{OCA_EXTENSION}"

    output_path = Path(output_file)
    if not output_path.suffix == OCA_EXTENSION:
        output_path = output_path.with_suffix(OCA_EXTENSION)

    manifest = create_manifest(agent_id, workspace, include_knowledge)
    files_to_backup = []

    # Well-known workspace files (used for informational logging)
    core_files = [
        "AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md",
        "MEMORY.md", "HEARTBEAT.md", "TOOLS.md", "ACCESS.md", "RAG.md",
        "IDEAS.md", "BOOTSTRAP.md", "STORY.md",
    ]

    # Collect all .md files in the workspace root so user-created
    # markdown files are never missed.
    seen: set[str] = set()
    for md_file in sorted(workspace.glob("*.md")):
        if md_file.name not in seen:
            seen.add(md_file.name)
            files_to_backup.append(md_file)
            manifest["files"].append(md_file.name)

    # Log which well-known files were found / missing
    for filename in core_files:
        if filename in seen:
            log_success(f"Included core file: {filename}")
        else:
            log_info(f"Core file not present: {filename}")

    extra_md = seen - set(core_files)
    if extra_md:
        log_success(
            f"Included {len(extra_md)} extra .md file(s): "
            f"{', '.join(sorted(extra_md))}"
        )

    # --- Subdirectories ---------------------------------------------------
    # Always back up knowledge/ (respecting --no-knowledge) and memory/.
    # Users can specify additional directories via --include-dir.

    knowledge_dir = workspace / "knowledge"
    if knowledge_dir.exists() and include_knowledge:
        for item in knowledge_dir.rglob("*"):
            if item.is_file():
                files_to_backup.append(item)
                manifest["files"].append(str(item.relative_to(workspace)))
    elif knowledge_dir.exists() and not include_knowledge:
        log_warning("Excluding knowledge directory (--no-knowledge)")

    memory_dir = workspace / "memory"
    if memory_dir.exists():
        for item in memory_dir.rglob("*"):
            if item.is_file():
                files_to_backup.append(item)
                manifest["files"].append(str(item.relative_to(workspace)))

    # Back up user-specified extra directories
    for dir_name in (include_dirs or []):
        extra_dir = workspace / dir_name
        if not extra_dir.exists():
            log_warning(f"--include-dir '{dir_name}' not found, skipping")
            continue
        if not extra_dir.is_dir():
            log_warning(f"--include-dir '{dir_name}' is not a directory, skipping")
            continue
        count = 0
        for item in extra_dir.rglob("*"):
            if item.is_file():
                files_to_backup.append(item)
                manifest["files"].append(str(item.relative_to(workspace)))
                count += 1
        log_success(f"Included directory '{dir_name}': {count} file(s)")

    config = get_agent_config(agent_id)
    if config:
        manifest["config"] = config
        log_success("Agent config extracted from openclaw.json")
    else:
        log_warning("Agent config not found in openclaw.json")

    cron_jobs = get_agent_cron_jobs(agent_id)
    manifest["cron_jobs"] = cron_jobs
    if cron_jobs:
        log_success(f"Found {len(cron_jobs)} associated cron job(s)")

    if dry_run:
        log_info("\n" + "="*50)
        log_info("DRY RUN SUMMARY")
        log_info("="*50)
        log_info(f"Agent: {agent_id}")
        log_info(f"Workspace: {workspace}")
        log_info(f"Files to backup: {len(files_to_backup)}")
        log_info(f"Output file: {output_path}")
        log_info(f"Include knowledge: {include_knowledge}")
        log_info(f"Cron jobs: {len(cron_jobs)}")
        log_info("="*50)
        return True

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            ws_tmp = tmpdir_path / "workspace"
            ws_tmp.mkdir()

            for file_path in files_to_backup:
                rel_path = file_path.relative_to(workspace)
                dest_path = ws_tmp / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)

            manifest_path = tmpdir_path / MANIFEST_FILENAME
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(tmpdir_path, arcname=".")

        log_success(f"Backup created: {output_path}")
        log_info(f"Archive size: {output_path.stat().st_size / 1024:.1f} KB")
        return True

    except Exception as e:
        log_error(f"Failed to create backup: {e}")
        return False


def read_manifest(archive_path: Path) -> Optional[Dict[str, Any]]:
    """Read manifest from .oca archive"""
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            manifest_member = tar.getmember(f"./{MANIFEST_FILENAME}")
            f = tar.extractfile(manifest_member)
            if f:
                return json.loads(f.read().decode('utf-8'))
    except Exception as e:
        log_error(f"Failed to read manifest from archive: {e}")
    return None


def update_openclaw_config(agent_config: Dict[str, Any], dry_run: bool = False) -> bool:
    """Add agent to openclaw.json if not present"""
    config_path = OPENCLAW_DIR / "openclaw.json"
    if not config_path.exists():
        log_warning("openclaw.json not found, skipping config update")
        return False

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        agents = config.get("agents", {}).get("list", [])
        agent_id = agent_config.get("id")

        for agent in agents:
            if agent.get("id") == agent_id:
                log_info(f"Agent {agent_id} already in openclaw.json")
                return True

        if dry_run:
            log_info(f"Would add agent {agent_id} to openclaw.json")
            return True

        agents.append(agent_config)
        config["agents"]["list"] = agents

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        log_success(f"Added agent {agent_id} to openclaw.json")
        return True

    except Exception as e:
        log_error(f"Failed to update openclaw.json: {e}")
        return False


def restore_agent(archive_path: str, target_dir: Optional[str] = None,
                  dry_run: bool = False) -> bool:
    """Restore an OpenClaw agent from .oca file"""

    archive = Path(archive_path)
    if not archive.exists():
        log_error(f"Archive not found: {archive_path}")
        return False

    if not archive.suffix == OCA_EXTENSION:
        log_warning(f"Archive should have {OCA_EXTENSION} extension")

    log_info(f"Restoring from archive: {archive}")
    if dry_run:
        log_warning("DRY RUN MODE - No files will be restored")

    manifest = read_manifest(archive)
    if not manifest:
        log_error("Failed to read manifest from archive")
        return False

    agent_id = manifest.get("agent_id")
    original_workspace = manifest.get("workspace_path")
    files = manifest.get("files", [])
    config = manifest.get("config", {})

    log_success(f"Manifest read: Agent {agent_id}")
    log_info(f"Original workspace: {original_workspace}")
    log_info(f"Files in archive: {len(files)}")

    if target_dir:
        workspace = Path(target_dir)
    else:
        workspace = Path(original_workspace) if original_workspace else OPENCLAW_DIR / agent_id

    if workspace.exists():
        log_warning(f"Workspace already exists: {workspace}")
        if not dry_run:
            response = input("Overwrite? (y/N): ")
            if response.lower() != 'y':
                log_info("Restore cancelled")
                return False
            backup_name = f"{workspace.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = workspace.parent / backup_name
            shutil.move(workspace, backup_path)
            log_info(f"Existing workspace backed up to: {backup_path}")

    if dry_run:
        log_info("\n" + "="*50)
        log_info("DRY RUN SUMMARY")
        log_info("="*50)
        log_info(f"Agent: {agent_id}")
        log_info(f"Target workspace: {workspace}")
        log_info(f"Files to restore: {len(files)}")
        log_info(f"Update openclaw.json: {bool(config)}")
        log_info("="*50)
        return True

    try:
        workspace.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.startswith("./workspace/"):
                    tar.extract(member, workspace.parent)

        extracted_ws = workspace.parent / "workspace"
        if extracted_ws.exists():
            for item in extracted_ws.iterdir():
                dest = workspace / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            extracted_ws.rmdir()

        log_success(f"Agent restored to: {workspace}")

        if config:
            config["workspace"] = str(workspace)
            update_openclaw_config(config, dry_run=False)

        return True

    except Exception as e:
        log_error(f"Failed to restore agent: {e}")
        return False


def migrate_agent(agent_id: str, remote_host: str, remote_dir: Optional[str] = None,
                  keep_local: bool = False, dry_run: bool = False) -> bool:
    """Migrate an OpenClaw agent to a remote host via SSH/SCP"""

    log_info(f"Migrating agent: {agent_id} to {remote_host}")
    if dry_run:
        log_warning("DRY RUN MODE - No files will be transferred")

    workspace = get_agent_workspace(agent_id)
    if not workspace:
        log_error(f"Agent workspace not found: {agent_id}")
        return False

    log_success(f"Found workspace: {workspace}")

    # Create temporary backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{agent_id}_migrate_{timestamp}{OCA_EXTENSION}"

    if dry_run:
        log_info("\n" + "="*50)
        log_info("DRY RUN SUMMARY - MIGRATION")
        log_info("="*50)
        log_info(f"Agent: {agent_id}")
        log_info(f"Source: {workspace}")
        log_info(f"Remote host: {remote_host}")
        log_info(f"Backup file: {backup_filename}")
        log_info(f"Keep local: {keep_local}")
        log_info("="*50)
        log_info("\nSteps that would be executed:")
        log_info("1. Create local backup archive")
        log_info("2. Transfer backup to remote host via SCP")
        log_info("3. Extract backup on remote host")
        log_info("4. Update remote openclaw.json")
        if not keep_local:
            log_info("5. Remove local agent (after verification)")
        return True

    # Step 1: Create backup
    log_info("\n[1/4] Creating local backup...")
    temp_dir = tempfile.gettempdir()
    backup_path = Path(temp_dir) / backup_filename

    success = backup_agent(agent_id, output_file=str(backup_path),
                           include_knowledge=True, dry_run=False)
    if not success:
        log_error("Failed to create backup")
        return False

    log_success(f"Backup created: {backup_path}")

    # Step 2: Transfer to remote
    log_info("\n[2/4] Transferring to remote host...")
    remote_path = remote_dir or f"~/.openclaw/migrations/"

    try:
        # Create remote directory
        mkdir_cmd = ["ssh", remote_host, f"mkdir -p {remote_path}"]
        result = subprocess.run(mkdir_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_error(f"Failed to create remote directory: {result.stderr}")
            backup_path.unlink(missing_ok=True)
            return False

        # Transfer file
        scp_cmd = ["scp", str(backup_path), f"{remote_host}:{remote_path}/"]
        log_info(f"Running: {' '.join(scp_cmd)}")
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_error(f"SCP failed: {result.stderr}")
            backup_path.unlink(missing_ok=True)
            return False

        log_success(f"Backup transferred to {remote_host}:{remote_path}/")

    except FileNotFoundError:
        log_error("SSH/SCP not found. Please ensure ssh and scp are installed.")
        backup_path.unlink(missing_ok=True)
        return False
    except Exception as e:
        log_error(f"Transfer failed: {e}")
        backup_path.unlink(missing_ok=True)
        return False

    # Step 3: Extract and restore on remote
    log_info("\n[3/4] Restoring agent on remote host...")

    remote_backup_path = f"{remote_path}/{backup_filename}"

    # Check if openclaw-brm exists on remote
    check_cmd = ["ssh", remote_host, "which openclaw-brm || echo 'not found'"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    brm_available = "not found" not in result.stdout

    if brm_available:
        # Use openclaw-brm on remote
        restore_cmd = ["ssh", remote_host,
                       f"openclaw-brm restore {remote_backup_path}"]
        log_info(f"Restoring using remote openclaw-brm...")
    else:
        # Manual extraction
        remote_workspace = f"~/.openclaw/workspace-{agent_id}"
        restore_cmd = ["ssh", remote_host,
                       f"mkdir -p {remote_workspace} && "
                       f"cd {remote_workspace} && "
                       f"tar -xzf {remote_backup_path} --strip-components=2"]
        log_info(f"Remote openclaw-brm not found, extracting manually...")
        log_warning("You'll need to manually update openclaw.json on the remote host")

    result = subprocess.run(restore_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_error(f"Remote restore failed: {result.stderr}")
        log_info("Backup is still on remote host, you can restore manually")
        backup_path.unlink(missing_ok=True)
        return False

    log_success("Agent restored on remote host")

    # Clean up local temp backup
    backup_path.unlink(missing_ok=True)
    log_info("Local temp backup cleaned up")

    # Step 4: Optionally remove local agent
    if not keep_local:
        log_info("\n[4/4] Removing local agent...")

        # Verify remote agent works
        verify_cmd = ["ssh", remote_host, f"test -d ~/.openclaw/workspace-{agent_id} && echo 'exists'"]
        result = subprocess.run(verify_cmd, capture_output=True, text=True)

        if "exists" not in result.stdout:
            log_warning("Remote agent not verified, keeping local copy")
            log_info("Use --keep-local to skip this check in the future")
        else:
            # Remove from openclaw.json
            config_path = OPENCLAW_DIR / "openclaw.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)

                    agents = config.get("agents", {}).get("list", [])
                    config["agents"]["list"] = [a for a in agents if a.get("id") != agent_id]

                    with open(config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    log_success("Agent removed from openclaw.json")
                except Exception as e:
                    log_warning(f"Failed to update openclaw.json: {e}")

            # Backup and remove workspace
            archive_name = f"{agent_id}_pre_migration_{timestamp}{OCA_EXTENSION}"
            archive_path = OPENCLAW_DIR / archive_name

            shutil.make_archive(str(archive_path.with_suffix('')), 'gztar', workspace)
            log_info(f"Local workspace archived to: {archive_path}")

            shutil.rmtree(workspace)
            log_success(f"Local workspace removed: {workspace}")
            log_info(f"Archive kept at: {archive_path}")
    else:
        log_info("\n[4/4] Keeping local agent (--keep-local specified)")

    log_success("\n" + "="*50)
    log_success("MIGRATION COMPLETE")
    log_success("="*50)
    log_info(f"Agent '{agent_id}' migrated to {remote_host}")
    log_info(f"Remote workspace: ~/.openclaw/workspace-{agent_id}")
    if not keep_local:
        log_info(f"Local archive: {OPENCLAW_DIR}/{agent_id}_pre_migration_{timestamp}{OCA_EXTENSION}")
    log_success("="*50)

    return True


def list_agents() -> bool:
    """List available OpenClaw agents"""
    config_path = OPENCLAW_DIR / "openclaw.json"
    if not config_path.exists():
        log_error("openclaw.json not found")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)

        agents = config.get("agents", {}).get("list", [])

        if not agents:
            log_warning("No agents configured")
            return True

        print("\n" + "="*70)
        print(f"{'Agent ID':<20} {'Name':<20} {'Workspace':<30}")
        print("="*70)

        for agent in agents:
            agent_id = agent.get("id", "N/A")
            name = agent.get("name", "N/A")
            workspace = agent.get("workspace", "N/A")

            # Truncate long paths
            workspace_display = (workspace[:27] + "...") if len(workspace) > 30 else workspace

            # Check if workspace exists
            ws_exists = Path(workspace).exists() if workspace else False
            status = "✓" if ws_exists else "✗"

            print(f"{status} {agent_id:<18} {name:<20} {workspace_display:<30}")

        print("="*70)
        print(f"\nTotal agents: {len(agents)}")
        print("✓ = workspace exists | ✗ = workspace not found")

        return True

    except Exception as e:
        log_error(f"Failed to list agents: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Agent BRM (Backup, Recovery, Migrate) Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Backup:
    %(prog)s backup drpowerscale                    # Backup to default filename
    %(prog)s backup drpowerscale -o mybackup.oca    # Backup to specific file
    %(prog)s backup drpowerscale --dry-run          # Preview what would be backed up
    %(prog)s backup drpowerscale --no-knowledge     # Exclude knowledge directory
    %(prog)s backup drpowerscale --include-dir projects  # Include extra subdirectory

  Restore:
    %(prog)s restore drpowerscale_20260219.oca      # Restore agent
    %(prog)s restore backup.oca --target-dir ./ws   # Restore to specific directory
    %(prog)s restore backup.oca --dry-run           # Preview restore

  Migrate:
    %(prog)s migrate drpowerscale --to user@server  # Migrate to remote host
    %(prog)s migrate drpowerscale --to server --keep-local  # Keep local copy
    %(prog)s migrate drpowerscale --to server --dry-run      # Preview migration

  List:
    %(prog)s list                                   # List all agents
        """
    )

    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup an agent')
    backup_parser.add_argument('agent_id', help='Agent ID to backup')
    backup_parser.add_argument('-o', '--output', help='Output file path')
    backup_parser.add_argument('--no-knowledge', action='store_true',
                              help='Exclude knowledge directory from backup')
    backup_parser.add_argument('--include-dir', action='append', default=[],
                              metavar='DIR',
                              help='Extra workspace subdirectory to include '
                                   '(repeatable, e.g. --include-dir projects '
                                   '--include-dir data)')
    backup_parser.add_argument('--dry-run', action='store_true',
                              help='Show what would be backed up without creating files')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore an agent from backup')
    restore_parser.add_argument('archive', help='Archive file (.oca)')
    restore_parser.add_argument('--target-dir', help='Target directory for restoration')
    restore_parser.add_argument('--dry-run', action='store_true',
                               help='Preview restore without making changes')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate agent to remote host via SSH')
    migrate_parser.add_argument('agent_id', help='Agent ID to migrate')
    migrate_parser.add_argument('--to', required=True, help='Remote host (user@hostname or hostname)')
    migrate_parser.add_argument('--remote-dir', help='Remote directory for backup (default: ~/.openclaw/migrations/)')
    migrate_parser.add_argument('--keep-local', action='store_true',
                               help='Keep local agent after migration (default: remove after verification)')
    migrate_parser.add_argument('--dry-run', action='store_true',
                               help='Preview migration without executing')

    # List command
    list_parser = subparsers.add_parser('list', help='List available agents')
    list_parser.add_argument('--json', action='store_true', help='Output in JSON format')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'backup':
        success = backup_agent(
            args.agent_id,
            output_file=args.output,
            include_knowledge=not args.no_knowledge,
            dry_run=args.dry_run,
            include_dirs=args.include_dir
        )
        sys.exit(0 if success else 1)

    elif args.command == 'restore':
        success = restore_agent(
            args.archive,
            target_dir=args.target_dir,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)

    elif args.command == 'migrate':
        success = migrate_agent(
            args.agent_id,
            remote_host=args.to,
            remote_dir=args.remote_dir,
            keep_local=args.keep_local,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)

    elif args.command == 'list':
        success = list_agents()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
