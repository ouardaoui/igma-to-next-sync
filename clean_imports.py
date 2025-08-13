#!/usr/bin/env python3
"""
Remove Version Numbers from Imports
Cleans up Figma-exported code by removing @version from import statements
"""

import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import json

class ImportVersionCleaner:
    def __init__(self, project_path: str, backup: bool = True):
        self.project_path = Path(project_path)
        self.backup_enabled = backup
        self.files_processed = 0
        self.imports_cleaned = 0
        self.changes = []
        self.package_versions = {}
        
    def create_backup(self) -> str:
        """Create a backup of the project before making changes"""
        if not self.backup_enabled:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_path.parent / f"backup_imports_{timestamp}"
        
        print(f"📦 Creating backup at {backup_dir}")
        shutil.copytree(
            self.project_path, 
            backup_dir,
            ignore=shutil.ignore_patterns('node_modules', '.next', 'dist', '.git')
        )
        return str(backup_dir)
    
    def extract_package_versions(self) -> Dict[str, str]:
        """Extract all unique package@version combinations found"""
        versions = {}
        
        for file_path in self._get_target_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all imports with versions
                pattern = r'from\s+["\']([^"\']+@[\d.]+)["\']'
                matches = re.findall(pattern, content)
                
                for match in matches:
                    if '@' in match:
                        package, version = match.rsplit('@', 1)
                        if package not in versions:
                            versions[package] = version
                        elif versions[package] != version:
                            # Multiple versions found for same package
                            if not isinstance(versions[package], list):
                                versions[package] = [versions[package]]
                            if version not in versions[package]:
                                versions[package].append(version)
                                
            except Exception as e:
                print(f"  ⚠️  Error reading {file_path}: {e}")
                
        return versions
    
    def clean_import_statement(self, line: str) -> Tuple[str, bool]:
        """Clean a single import statement"""
        # Pattern to match imports with version numbers
        patterns = [
            # ES6 imports: import { Something } from "package@version"
            (r'(from\s+["\'])([^"\']+)(@[\d.]+)(["\'])', r'\1\2\4'),
            # require statements: require("package@version")
            (r'(require\s*\(\s*["\'])([^"\']+)(@[\d.]+)(["\'])', r'\1\2\4'),
            # Dynamic imports: import("package@version")
            (r'(import\s*\(\s*["\'])([^"\']+)(@[\d.]+)(["\'])', r'\1\2\4'),
        ]
        
        cleaned_line = line
        was_cleaned = False
        
        for pattern, replacement in patterns:
            if re.search(pattern, line):
                cleaned_line = re.sub(pattern, replacement, line)
                was_cleaned = True
                break
                
        return cleaned_line, was_cleaned
    
    def process_file(self, file_path: Path) -> int:
        """Process a single file and remove version numbers from imports"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            cleaned_lines = []
            imports_cleaned_in_file = 0
            
            for line_num, line in enumerate(lines, 1):
                cleaned_line, was_cleaned = self.clean_import_statement(line)
                
                if was_cleaned:
                    modified = True
                    imports_cleaned_in_file += 1
                    
                    # Extract what was changed for reporting
                    original_import = re.search(r'["\']([^"\']+@[\d.]+)["\']', line)
                    cleaned_import = re.search(r'["\']([^"\']+)["\']', cleaned_line)
                    
                    if original_import and cleaned_import:
                        self.changes.append({
                            'file': str(file_path.relative_to(self.project_path)),
                            'line': line_num,
                            'original': original_import.group(1),
                            'cleaned': cleaned_import.group(1)
                        })
                
                cleaned_lines.append(cleaned_line)
            
            # Write back only if file was modified
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(cleaned_lines)
                    
                print(f"  ✅ Cleaned {imports_cleaned_in_file} imports in {file_path.name}")
                
            return imports_cleaned_in_file
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")
            return 0
    
    def _get_target_files(self) -> List[Path]:
        """Get all JS/TS files that need processing"""
        target_extensions = {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}
        target_files = []
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip node_modules and build directories
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.next', 'dist', '.git', 'build']]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in target_extensions:
                    target_files.append(file_path)
                    
        return target_files
    
    def generate_package_json_updates(self) -> Dict:
        """Generate package.json dependency updates based on found versions"""
        package_json_path = self.project_path / "package.json"
        
        if not package_json_path.exists():
            return {}
            
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        updates = {
            'dependencies': {},
            'devDependencies': {}
        }
        
        # Check which packages need to be added/updated
        for package, version in self.package_versions.items():
            # Skip relative imports
            if package.startswith('.') or package.startswith('/'):
                continue
                
            # Determine version to use (if multiple found, use latest)
            if isinstance(version, list):
                version = max(version)  # Simple approach - take highest version
            
            # Check if package exists in dependencies
            current_deps = package_data.get('dependencies', {})
            current_dev_deps = package_data.get('devDependencies', {})
            
            if package not in current_deps and package not in current_dev_deps:
                updates['dependencies'][package] = version
            elif package in current_deps and current_deps[package] != version:
                updates['dependencies'][package] = version
                
        return updates
    
    def clean_project(self) -> Dict:
        """Main method to clean the entire project"""
        print(f"🔍 Scanning project: {self.project_path}")
        
        # Create backup if enabled
        backup_path = None
        if self.backup_enabled:
            backup_path = self.create_backup()
        
        # Extract all package versions first
        print("📋 Extracting package versions...")
        self.package_versions = self.extract_package_versions()
        
        # Get all target files
        target_files = self._get_target_files()
        print(f"📁 Found {len(target_files)} files to process")
        
        # Process each file
        print("🧹 Cleaning imports...")
        for file_path in target_files:
            imports_cleaned = self.process_file(file_path)
            if imports_cleaned > 0:
                self.files_processed += 1
                self.imports_cleaned += imports_cleaned
        
        # Generate summary
        summary = {
            'files_processed': self.files_processed,
            'imports_cleaned': self.imports_cleaned,
            'backup_path': backup_path,
            'package_versions': self.package_versions,
            'changes': self.changes[:10],  # First 10 changes for preview
            'total_changes': len(self.changes)
        }
        
        return summary
    
    def generate_report(self, summary: Dict) -> str:
        """Generate a detailed report of changes"""
        report = []
        report.append("=" * 60)
        report.append("IMPORT VERSION CLEANUP REPORT")
        report.append("=" * 60)
        report.append(f"Project: {self.project_path}")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY:")
        report.append(f"  Files processed: {summary['files_processed']}")
        report.append(f"  Imports cleaned: {summary['imports_cleaned']}")
        report.append(f"  Total changes: {summary['total_changes']}")
        
        if summary['backup_path']:
            report.append(f"  Backup location: {summary['backup_path']}")
        report.append("")
        
        # Package versions found
        if summary['package_versions']:
            report.append("PACKAGE VERSIONS FOUND:")
            for package, version in sorted(summary['package_versions'].items()):
                if not package.startswith('.'):  # Skip relative imports
                    if isinstance(version, list):
                        report.append(f"  {package}: {', '.join(version)} (multiple versions!)")
                    else:
                        report.append(f"  {package}: {version}")
            report.append("")
        
        # Sample of changes
        if summary['changes']:
            report.append("SAMPLE CHANGES (first 10):")
            for change in summary['changes']:
                report.append(f"  File: {change['file']}, Line {change['line']}")
                report.append(f"    From: {change['original']}")
                report.append(f"    To:   {change['cleaned']}")
            report.append("")
        
        # Package.json recommendations
        package_updates = self.generate_package_json_updates()
        if package_updates['dependencies']:
            report.append("RECOMMENDED PACKAGE.JSON UPDATES:")
            report.append("  Add to dependencies:")
            for pkg, ver in package_updates['dependencies'].items():
                report.append(f"    \"{pkg}\": \"^{ver}\"")
            report.append("")
        
        report.append("=" * 60)
        
        return '\n'.join(report)
    
    def update_package_json(self, auto_update: bool = False):
        """Update package.json with found dependencies"""
        if not auto_update:
            print("ℹ️  Run with --update-package-json to add missing dependencies")
            return
            
        package_json_path = self.project_path / "package.json"
        if not package_json_path.exists():
            print("⚠️  No package.json found")
            return
        
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        updates = self.generate_package_json_updates()
        
        if updates['dependencies']:
            if 'dependencies' not in package_data:
                package_data['dependencies'] = {}
                
            for pkg, ver in updates['dependencies'].items():
                package_data['dependencies'][pkg] = f"^{ver}"
                print(f"  ➕ Added {pkg}@{ver} to dependencies")
            
            # Sort dependencies
            package_data['dependencies'] = dict(sorted(package_data['dependencies'].items()))
            
            # Write back
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
                f.write('\n')  # Add trailing newline
                
            print(f"✅ Updated package.json with {len(updates['dependencies'])} packages")
            print("📦 Run 'npm install' to install the new dependencies")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Remove version numbers from imports in Figma-exported code'
    )
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('--no-backup', action='store_true', 
                       help='Skip creating backup')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without modifying files')
    parser.add_argument('--update-package-json', action='store_true',
                       help='Update package.json with found dependencies')
    parser.add_argument('--output', help='Save report to file')
    parser.add_argument('--verbose', action='store_true',
                       help='Show all changes, not just first 10')
    
    args = parser.parse_args()
    
    # Validate project path
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"❌ Error: Project path does not exist: {project_path}")
        sys.exit(1)
    
    if not project_path.is_dir():
        print(f"❌ Error: Project path is not a directory: {project_path}")
        sys.exit(1)
    
    # Dry run mode
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        cleaner = ImportVersionCleaner(args.project_path, backup=False)
        versions = cleaner.extract_package_versions()
        
        print("\n📋 Found imports with versions:")
        for package, version in sorted(versions.items()):
            if not package.startswith('.'):
                if isinstance(version, list):
                    print(f"  {package}: {', '.join(version)}")
                else:
                    print(f"  {package}@{version}")
        
        files = cleaner._get_target_files()
        print(f"\n📁 Would process {len(files)} files")
        
        # Show sample of what would be changed
        print("\n🔄 Sample of changes that would be made:")
        sample_count = 0
        for file_path in files[:5]:  # Check first 5 files
            with open(file_path, 'r') as f:
                lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                if '@' in line and ('import' in line or 'require' in line):
                    cleaned, was_cleaned = cleaner.clean_import_statement(line)
                    if was_cleaned:
                        print(f"\n  File: {file_path.name}, Line {line_num}")
                        print(f"    Before: {line.strip()}")
                        print(f"    After:  {cleaned.strip()}")
                        sample_count += 1
                        if sample_count >= 5:
                            break
            if sample_count >= 5:
                break
        
        sys.exit(0)
    
    # Run the cleaner
    cleaner = ImportVersionCleaner(args.project_path, backup=not args.no_backup)
    
    print("🚀 Starting import version cleanup...")
    summary = cleaner.clean_project()
    
    # Generate and display report
    report = cleaner.generate_report(summary)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to {args.output}")
    else:
        print("\n" + report)
    
    # Update package.json if requested
    if args.update_package_json:
        cleaner.update_package_json(auto_update=True)
    
    # Final summary
    print(f"\n✨ Cleanup complete!")
    print(f"   Files modified: {summary['files_processed']}")
    print(f"   Imports cleaned: {summary['imports_cleaned']}")
    
    if summary['backup_path']:
        print(f"   Backup saved to: {summary['backup_path']}")
    
    if summary['imports_cleaned'] > 0:
        print("\n📦 Next steps:")
        print("   1. Review the changes")
        print("   2. Run 'npm install' to ensure all dependencies are installed")
        print("   3. Run 'npm run build' to verify everything compiles")

if __name__ == "__main__":
    main()