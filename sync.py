#!/usr/bin/env python3
"""
Figma Project Sync Manager
Intelligently manages changes between Figma exports and your local project
"""

import os
import sys
import shutil
import json
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import hashlib

class FigmaSyncManager:
    def __init__(self, old_project: str, new_figma: str, output_dir: str = "./figma-sync"):
        self.old_project = Path(old_project)
        self.new_figma = Path(new_figma)
        self.output_dir = Path(output_dir)
        
        # Create organized structure
        self.new_folders_dir = self.output_dir / "01_NEW_FOLDERS"
        self.new_files_dir = self.output_dir / "02_NEW_FILES"
        self.updated_files_dir = self.output_dir / "03_UPDATED_FILES"
        self.deleted_items_dir = self.output_dir / "04_DELETED_ITEMS"
        self.reports_dir = self.output_dir / "00_REPORTS"
        
        # Set tracking file path
        self.tracking_file = self.reports_dir / "sync_tracking.json"
        
        # Tracking
        self.new_folders = []
        self.new_files = []
        self.updated_files = []
        self.deleted_folders = []
        self.deleted_files = []
        self.identical_files = []
        
        # Labels for easy selection
        self.folder_labels = {}
        self.file_labels = {}
        self.update_labels = {}
        
    def initialize_structure(self):
        """Create the organized output structure"""
        print("📁 Creating sync structure...")
        
        # Create all directories
        for dir_path in [self.new_folders_dir, self.new_files_dir, 
                        self.updated_files_dir, self.deleted_items_dir, 
                        self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
    def scan_projects(self):
        """Scan both projects and identify all changes"""
        print("🔍 Scanning projects for changes...")
        
        # Get all files and folders from both projects
        old_structure = self._get_project_structure(self.old_project)
        new_structure = self._get_project_structure(self.new_figma)
        
        # Find new folders
        for folder in new_structure['folders']:
            if folder not in old_structure['folders']:
                self.new_folders.append(folder)
        
        # Find deleted folders
        for folder in old_structure['folders']:
            if folder not in new_structure['folders']:
                self.deleted_folders.append(folder)
        
        # Find file changes
        for file_path, file_hash in new_structure['files'].items():
            if file_path not in old_structure['files']:
                self.new_files.append(file_path)
            elif old_structure['files'][file_path] != file_hash:
                self.updated_files.append(file_path)
            else:
                self.identical_files.append(file_path)
        
        # Find deleted files
        for file_path in old_structure['files']:
            if file_path not in new_structure['files']:
                self.deleted_files.append(file_path)
    
    def _get_project_structure(self, project_path: Path) -> Dict:
        """Get complete project structure with file hashes"""
        structure = {
            'folders': [],
            'files': {}
        }
        
        for root, dirs, files in os.walk(project_path):
            # Skip node_modules and build directories
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.next', 'dist', '.git', 'build']]
            
            # Add folders
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                rel_path = dir_path.relative_to(project_path)
                structure['folders'].append(str(rel_path))
            
            # Add files with hash
            for file_name in files:
                # Skip certain file types
                if file_name.startswith('.') or file_name.endswith(('.pyc', '.log')):
                    continue
                    
                file_path = Path(root) / file_name
                rel_path = file_path.relative_to(project_path)
                
                # Calculate file hash for comparison
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    structure['files'][str(rel_path)] = file_hash
                except Exception as e:
                    print(f"  ⚠️  Error reading {file_path}: {e}")
        
        return structure
    
    def process_new_folders(self):
        """Process and label new folders"""
        if not self.new_folders:
            print("  ✅ No new folders found")
            return
        
        print(f"\n📂 Found {len(self.new_folders)} NEW FOLDERS:")
        
        # Create info file
        info_file = self.new_folders_dir / "README.md"
        with open(info_file, 'w') as f:
            f.write("# New Folders from Figma Export\n\n")
            f.write("Use `python3 sync.py --add-folder [LABEL]` to add a folder to your project\n\n")
            f.write("| Label | Folder Path | Files Inside |\n")
            f.write("|-------|-------------|-------------|\n")
            
            for idx, folder in enumerate(self.new_folders, 1):
                label = f"F{idx:03d}"
                self.folder_labels[label] = folder
                
                # Count files in this folder
                folder_full_path = self.new_figma / folder
                file_count = sum(1 for _ in folder_full_path.rglob('*') if _.is_file())
                
                # Create a preview directory
                preview_dir = self.new_folders_dir / label
                preview_dir.mkdir(exist_ok=True)
                
                # Copy the folder structure
                shutil.copytree(
                    self.new_figma / folder,
                    preview_dir / folder,
                    ignore=shutil.ignore_patterns('node_modules', '.git')
                )
                
                f.write(f"| **{label}** | `{folder}` | {file_count} files |\n")
                print(f"  [{label}] 📁 {folder} ({file_count} files)")
    
    def process_new_files(self):
        """Process and label new files"""
        if not self.new_files:
            print("  ✅ No new files found")
            return
        
        print(f"\n📄 Found {len(self.new_files)} NEW FILES:")
        
        # Group files by directory
        files_by_dir = {}
        for file_path in self.new_files:
            dir_path = str(Path(file_path).parent)
            if dir_path not in files_by_dir:
                files_by_dir[dir_path] = []
            files_by_dir[dir_path].append(file_path)
        
        # Create info file
        info_file = self.new_files_dir / "README.md"
        with open(info_file, 'w') as f:
            f.write("# New Files from Figma Export\n\n")
            f.write("Use `python3 sync.py --add-file [LABEL]` to add a file to your project\n\n")
            f.write("| Label | File Path | Size | Type |\n")
            f.write("|-------|-----------|------|------|\n")
            
            label_counter = 1
            for dir_path in sorted(files_by_dir.keys()):
                f.write(f"\n### Directory: `{dir_path}`\n\n")
                
                for file_path in sorted(files_by_dir[dir_path]):
                    label = f"N{label_counter:03d}"
                    self.file_labels[label] = file_path
                    
                    # Get file info
                    src_file = self.new_figma / file_path
                    file_size = src_file.stat().st_size
                    file_ext = Path(file_path).suffix
                    
                    # Copy file to preview area
                    dest_file = self.new_files_dir / label / Path(file_path).name
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                    
                    # Create info file for each new file
                    info_txt = self.new_files_dir / label / "INFO.txt"
                    with open(info_txt, 'w') as info:
                        info.write(f"Original Path: {file_path}\n")
                        info.write(f"File Type: {file_ext}\n")
                        info.write(f"Size: {file_size} bytes\n")
                        info.write(f"Will be copied to: {self.old_project / file_path}\n")
                    
                    size_kb = file_size / 1024
                    f.write(f"| **{label}** | `{file_path}` | {size_kb:.1f}KB | {file_ext} |\n")
                    print(f"  [{label}] 📄 {Path(file_path).name} ({size_kb:.1f}KB)")
                    
                    label_counter += 1
    
    def process_updated_files(self):
        """Create diffs for all updated files"""
        if not self.updated_files:
            print("  ✅ No updated files found")
            return
        
        print(f"\n📝 Found {len(self.updated_files)} UPDATED FILES:")
        
        # Create info file
        info_file = self.updated_files_dir / "README.md"
        with open(info_file, 'w') as f:
            f.write("# Updated Files - Figma Changes\n\n")
            f.write("Use `python3 sync.py --apply-update [LABEL]` to apply changes\n")
            f.write("Use `python3 sync.py --view-diff [LABEL]` to view detailed diff\n\n")
            f.write("| Label | File | Added | Removed | Status |\n")
            f.write("|-------|------|-------|---------|--------|\n")
            
            for idx, file_path in enumerate(sorted(self.updated_files), 1):
                label = f"U{idx:03d}"
                self.update_labels[label] = file_path
                
                # Create diff
                old_file = self.old_project / file_path
                new_file = self.new_figma / file_path
                
                # Create labeled directory
                update_dir = self.updated_files_dir / label
                update_dir.mkdir(exist_ok=True)
                
                # Generate diff file
                diff_file = update_dir / f"{Path(file_path).name}.diff"
                stats = self._create_diff_file(old_file, new_file, diff_file)
                
                # Copy both versions for comparison
                shutil.copy2(old_file, update_dir / f"{Path(file_path).name}.OLD")
                shutil.copy2(new_file, update_dir / f"{Path(file_path).name}.NEW")
                
                # Create summary file
                summary_file = update_dir / "SUMMARY.txt"
                with open(summary_file, 'w') as s:
                    s.write(f"File: {file_path}\n")
                    s.write(f"Lines Added: {stats['added']}\n")
                    s.write(f"Lines Removed: {stats['removed']}\n")
                    s.write(f"Total Changes: {stats['added'] + stats['removed']}\n")
                    s.write(f"\nTo apply: python3 sync.py --apply-update {label}\n")
                    s.write(f"To view: python3 sync.py --view-diff {label}\n")
                
                status = "⚠️ Major" if (stats['added'] + stats['removed']) > 50 else "Minor"
                f.write(f"| **{label}** | `{Path(file_path).name}` | +{stats['added']} | -{stats['removed']} | {status} |\n")
                print(f"  [{label}] 📝 {Path(file_path).name} (+{stats['added']}/-{stats['removed']})")
    
    def _create_diff_file(self, old_file: Path, new_file: Path, diff_file: Path) -> Dict:
        """Create a diff file and return statistics"""
        try:
            with open(old_file, 'r', encoding='utf-8') as f:
                old_lines = f.readlines()
            with open(new_file, 'r', encoding='utf-8') as f:
                new_lines = f.readlines()
            
            diff = list(difflib.unified_diff(
                old_lines, new_lines,
                fromfile=f"a/{old_file.name}",
                tofile=f"b/{new_file.name}",
                n=3
            ))
            
            # Count changes
            added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
            removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
            
            with open(diff_file, 'w') as f:
                f.writelines(diff)
            
            return {'added': added, 'removed': removed}
            
        except Exception as e:
            print(f"    ⚠️  Error creating diff for {old_file.name}: {e}")
            return {'added': 0, 'removed': 0}
    
    def process_deleted_items(self):
        """Track deleted items"""
        if not self.deleted_files and not self.deleted_folders:
            print("  ✅ No deleted items found")
            return
        
        print(f"\n🗑️  Found {len(self.deleted_files)} deleted files, {len(self.deleted_folders)} deleted folders")
        
        info_file = self.deleted_items_dir / "DELETED_ITEMS.md"
        with open(info_file, 'w') as f:
            f.write("# Items Removed in Figma Export\n\n")
            f.write("⚠️  These items exist in your project but NOT in the new Figma export\n\n")
            
            if self.deleted_folders:
                f.write("## Deleted Folders\n\n")
                for folder in self.deleted_folders:
                    f.write(f"- 📁 `{folder}`\n")
                    print(f"  ❌ Folder removed: {folder}")
            
            if self.deleted_files:
                f.write("\n## Deleted Files\n\n")
                for file_path in self.deleted_files:
                    f.write(f"- 📄 `{file_path}`\n")
                    print(f"  ❌ File removed: {file_path}")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n📊 Generating summary report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'old_project': str(self.old_project),
            'new_figma': str(self.new_figma),
            'statistics': {
                'new_folders': len(self.new_folders),
                'new_files': len(self.new_files),
                'updated_files': len(self.updated_files),
                'deleted_folders': len(self.deleted_folders),
                'deleted_files': len(self.deleted_files),
                'identical_files': len(self.identical_files)
            },
            'labels': {
                'folders': self.folder_labels,
                'files': self.file_labels,
                'updates': self.update_labels
            }
        }
        
        # Save JSON report
        with open(self.tracking_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create human-readable report
        summary_file = self.reports_dir / "SUMMARY.md"
        with open(summary_file, 'w') as f:
            f.write("# Figma Sync Summary Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Statistics\n\n")
            f.write(f"- 📂 **New Folders:** {len(self.new_folders)}\n")
            f.write(f"- 📄 **New Files:** {len(self.new_files)}\n")
            f.write(f"- 📝 **Updated Files:** {len(self.updated_files)}\n")
            f.write(f"- ❌ **Deleted Folders:** {len(self.deleted_folders)}\n")
            f.write(f"- ❌ **Deleted Files:** {len(self.deleted_files)}\n")
            f.write(f"- ✅ **Unchanged Files:** {len(self.identical_files)}\n\n")
            
            f.write("## Quick Commands\n\n")
            f.write("```bash\n")
            f.write("# Add a new folder\n")
            f.write("python3 sync.py --add-folder F001\n\n")
            f.write("# Add a new file\n")
            f.write("python3 sync.py --add-file N001\n\n")
            f.write("# Apply an update\n")
            f.write("python3 sync.py --apply-update U001\n\n")
            f.write("# View all changes\n")
            f.write("python3 sync.py --list-all\n")
            f.write("```\n")
        
        print(f"\n✅ Summary saved to: {summary_file}")
    
    def apply_change(self, label: str, change_type: str):
        """Apply a specific change to the project"""
        # Ensure tracking file path exists
        if not hasattr(self, 'tracking_file'):
            self.tracking_file = self.reports_dir / "sync_tracking.json"
        
        if not self.tracking_file.exists():
            print(f"❌ Tracking file not found: {self.tracking_file}")
            return False
        
        with open(self.tracking_file, 'r') as f:
            tracking = json.load(f)
        
        if change_type == 'folder':
            if label not in tracking['labels']['folders']:
                print(f"❌ Invalid folder label: {label}")
                return False
            
            folder_path = tracking['labels']['folders'][label]
            src = self.new_figma / folder_path
            dest = self.old_project / folder_path
            
            if dest.exists():
                print(f"⚠️  Folder already exists: {dest}")
                response = input("Overwrite? (y/n): ")
                if response.lower() != 'y':
                    return False
                shutil.rmtree(dest)
            
            shutil.copytree(src, dest)
            print(f"✅ Added folder: {folder_path}")
            return True
            
        elif change_type == 'file':
            if label not in tracking['labels']['files']:
                print(f"❌ Invalid file label: {label}")
                return False
            
            file_path = tracking['labels']['files'][label]
            src = self.new_figma / file_path
            dest = self.old_project / file_path
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"✅ Added file: {file_path}")
            return True
            
        elif change_type == 'update':
            if label not in tracking['labels']['updates']:
                print(f"❌ Invalid update label: {label}")
                return False
            
            file_path = tracking['labels']['updates'][label]
            src = self.new_figma / file_path
            dest = self.old_project / file_path
            
            # Backup original
            backup = dest.with_suffix(dest.suffix + '.backup')
            shutil.copy2(dest, backup)
            
            # Apply update
            shutil.copy2(src, dest)
            print(f"✅ Updated file: {file_path}")
            print(f"   Backup saved: {backup}")
            return True
    
    def run_analysis(self):
        """Run complete analysis"""
        print("🚀 Starting Figma Sync Analysis\n")
        print(f"Old Project: {self.old_project}")
        print(f"New Figma:   {self.new_figma}")
        print(f"Output Dir:  {self.output_dir}\n")
        
        self.initialize_structure()
        self.scan_projects()
        self.process_new_folders()
        self.process_new_files()
        self.process_updated_files()
        self.process_deleted_items()
        self.generate_summary_report()
        
        print("\n" + "="*60)
        print("✨ Analysis Complete!")
        print("="*60)
        print(f"\n📁 Check the '{self.output_dir}' folder for:")
        print("  - 00_REPORTS: Summary and tracking files")
        print("  - 01_NEW_FOLDERS: New folders with labels")
        print("  - 02_NEW_FILES: New files with labels")
        print("  - 03_UPDATED_FILES: File diffs with labels")
        print("  - 04_DELETED_ITEMS: Items removed in Figma")
        
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Figma Project Sync Manager')
    
    # Main analysis command
    parser.add_argument('--analyze', nargs=2, metavar=('OLD', 'NEW'),
                       help='Analyze differences between projects')
    parser.add_argument('--output', default='./figma-sync',
                       help='Output directory (default: ./figma-sync)')
    
    # Action commands
    parser.add_argument('--add-folder', metavar='LABEL',
                       help='Add a new folder by label (e.g., F001)')
    parser.add_argument('--add-file', metavar='LABEL',
                       help='Add a new file by label (e.g., N001)')
    parser.add_argument('--apply-update', metavar='LABEL',
                       help='Apply an update by label (e.g., U001)')
    parser.add_argument('--view-diff', metavar='LABEL',
                       help='View diff for an update label')
    parser.add_argument('--list-all', action='store_true',
                       help='List all available labels')
    
    # Batch operations
    parser.add_argument('--add-all-folders', action='store_true',
                       help='Add all new folders')
    parser.add_argument('--add-all-files', action='store_true',
                       help='Add all new files')
    parser.add_argument('--apply-all-updates', action='store_true',
                       help='Apply all updates (careful!)')
    
    args = parser.parse_args()
    
    # Run analysis
    if args.analyze:
        old_project, new_figma = args.analyze
        
        if not Path(old_project).exists():
            print(f"❌ Old project not found: {old_project}")
            sys.exit(1)
        if not Path(new_figma).exists():
            print(f"❌ New Figma project not found: {new_figma}")
            sys.exit(1)
        
        manager = FigmaSyncManager(old_project, new_figma, args.output)
        manager.run_analysis()
        
        print("\n📌 Next Steps:")
        print("1. Review the changes in the figma-sync folder")
        print("2. Use labels to apply specific changes:")
        print(f"   python3 {sys.argv[0]} --add-file N001")
        print(f"   python3 {sys.argv[0]} --apply-update U001")
        
    # Apply specific changes
    elif args.add_folder or args.add_file or args.apply_update:
        # Load existing tracking - check current directory first
        output_path = Path(args.output)
        
        # If we're inside the sync folder, adjust path
        if Path("00_REPORTS/sync_tracking.json").exists():
            tracking_file = Path("00_REPORTS/sync_tracking.json")
            output_path = Path(".")
        else:
            tracking_file = output_path / "00_REPORTS" / "sync_tracking.json"
        
        if not tracking_file.exists():
            print(f"❌ No sync data found at: {tracking_file}")
            print("Run --analyze first or check you're in the right directory.")
            sys.exit(1)
        
        with open(tracking_file) as f:
            tracking = json.load(f)
        
        # Recreate manager with original paths
        manager = FigmaSyncManager(
            tracking['old_project'],
            tracking['new_figma'],
            str(output_path)  # Use the adjusted output path
        )
        
        if args.add_folder:
            manager.apply_change(args.add_folder, 'folder')
        elif args.add_file:
            manager.apply_change(args.add_file, 'file')
        elif args.apply_update:
            manager.apply_change(args.apply_update, 'update')
    
    # View diff
    elif args.view_diff:
        # Check if we're inside the sync folder
        if Path("03_UPDATED_FILES").exists():
            diff_file = Path("03_UPDATED_FILES") / args.view_diff
        else:
            diff_file = Path(args.output) / "03_UPDATED_FILES" / args.view_diff
        
        if not diff_file.exists():
            print(f"❌ Invalid label: {args.view_diff}")
            sys.exit(1)
        
        # Find the diff file
        diff_files = list(diff_file.glob("*.diff"))
        if diff_files:
            with open(diff_files[0]) as f:
                print(f.read())
        else:
            print("❌ No diff file found")
    
    # List all labels
    elif args.list_all:
        # Check if we're inside the sync folder
        if Path("00_REPORTS/sync_tracking.json").exists():
            tracking_file = Path("00_REPORTS/sync_tracking.json")
        else:
            tracking_file = Path(args.output) / "00_REPORTS" / "sync_tracking.json"
        
        if not tracking_file.exists():
            print(f"❌ No sync data found at: {tracking_file}")
            print("Run --analyze first or check you're in the right directory.")
            sys.exit(1)
        
        with open(tracking_file) as f:
            tracking = json.load(f)
        
        print("\n📂 NEW FOLDERS:")
        for label, path in tracking['labels']['folders'].items():
            print(f"  {label}: {path}")
        
        print("\n📄 NEW FILES:")
        for label, path in tracking['labels']['files'].items():
            print(f"  {label}: {path}")
        
        print("\n📝 UPDATED FILES:")
        for label, path in tracking['labels']['updates'].items():
            print(f"  {label}: {path}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()