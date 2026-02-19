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
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Constants
VERSION = "0.1.0"
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
                 include_knowledge: bool = True, dry_run: bool = False) -> bool:
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
    
    core_files = [
        "AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md", 
        "MEMORY.md", "HEARTBEAT.md", "TOOLS.md", "ACCESS.md", "RAG.md"
    ]
    
    for filename in core_files:
        file_path = workspace / filename
        if file_path.exists():
            files_to_backup.append(file_path)
            manifest["files"].append(filename)
    
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


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Agent BRM (Backup, Recovery, Migrate) Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s backup drpowerscale                    # Backup to default filename
  %(prog)s backup drpowerscale -o mybackup.oca    # Backup to specific file
  %(prog)s backup drpowerscale --dry-run          # Preview what would be backed up
  %(prog)s backup drpowerscale --no-knowledge     # Exclude knowledge directory
  
  %(prog)s restore drpowerscale_20260219.oca      # Restore agent
  %(prog)s restore backup.oca --target-dir ./ws   # Restore to specific directory
  %(prog)s restore backup.oca --dry-run           # Preview restore
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
    backup_parser.add_argument('--dry-run', action='store_true',
                              help='Show what would be backed up without creating files')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore an agent from backup')
    restore_parser.add_argument('archive', help='Archive file (.oca)')
    restore_parser.add_argument('--target-dir', help='Target directory for restoration')
    restore_parser.add_argument('--dry-run', action='store_true',
                               help='Preview restore without making changes')
    
    # Migrate command (placeholder)
    migrate_parser = subparsers.add_parser('migrate', help='Migrate agent to remote host (coming soon)')
    migrate_parser.add_argument('agent_id', help='Agent ID to migrate')
    migrate_parser.add_argument('--to', required=True, help='Remote host (user@hostname)')
    migrate_parser.add_argument('--dry-run', action='store_true',
                               help='Preview migration without executing')
    
    # List command (placeholder)
    list_parser = subparsers.add_parser('list', help='List available agents (coming soon)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'backup':
        success = backup_agent(
            args.agent_id,
            output_file=args.output,
            include_knowledge=not args.no_knowledge,
            dry_run=args.dry_run
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
        log_error("Migrate command not yet implemented (coming in v0.2.0)")
        sys.exit(1)
    
    elif args.command == 'list':
        log_error("List command not yet implemented (coming in v0.2.0)")
        sys.exit(1)


if __name__ == '__main__':
    main()
