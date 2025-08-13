#!/usr/bin/env python3
"""
Interactive Diff Reviewer
Makes reviewing and applying changes from Figma exports super easy!
"""

import os
import sys
import json
import difflib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import shutil
import re
from datetime import datetime

# ANSI color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

class InteractiveDiffReviewer:
    def __init__(self, sync_dir: str = "./figma-sync"):
        self.sync_dir = Path(sync_dir)
        self.updates_dir = self.sync_dir / "03_UPDATED_FILES"
        self.tracking_file = self.sync_dir / "00_REPORTS" / "sync_tracking.json"
        self.decisions_file = self.sync_dir / "00_REPORTS" / "review_decisions.json"
        
        # Load tracking data
        self.tracking_data = self._load_tracking()
        self.decisions = self._load_decisions()
        
    def _load_tracking(self) -> Dict:
        """Load tracking data"""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_decisions(self) -> Dict:
        """Load previous decisions"""
        if self.decisions_file.exists():
            with open(self.decisions_file, 'r') as f:
                return json.load(f)
        return {
            'approved': {},
            'rejected': {},
            'partial': {}
        }
    
    def _save_decisions(self):
        """Save review decisions"""
        with open(self.decisions_file, 'w') as f:
            json.dump(self.decisions, f, indent=2)
    
    def _parse_diff_file(self, diff_file: Path) -> List[Dict]:
        """Parse diff file into hunks for easy review"""
        with open(diff_file, 'r') as f:
            lines = f.readlines()
        
        hunks = []
        current_hunk = None
        
        for line in lines:
            if line.startswith('@@'):
                # New hunk
                if current_hunk:
                    hunks.append(current_hunk)
                
                # Parse hunk header
                match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@(.*)', line)
                if match:
                    current_hunk = {
                        'header': line.strip(),
                        'old_start': int(match.group(1)),
                        'old_count': int(match.group(2)),
                        'new_start': int(match.group(3)),
                        'new_count': int(match.group(4)),
                        'context': match.group(5).strip(),
                        'lines': [],
                        'changes': {'added': 0, 'removed': 0}
                    }
            elif current_hunk is not None:
                current_hunk['lines'].append(line)
                if line.startswith('+') and not line.startswith('+++'):
                    current_hunk['changes']['added'] += 1
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk['changes']['removed'] += 1
        
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    def _display_hunk(self, hunk: Dict, index: int, total: int):
        """Display a single hunk with colors"""
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}Change Block {index}/{total}{Colors.ENDC}")
        print(f"{Colors.CYAN}Location: Line {hunk['new_start']}{Colors.ENDC}")
        if hunk['context']:
            print(f"{Colors.BLUE}Context: {hunk['context']}{Colors.ENDC}")
        print(f"Changes: {Colors.GREEN}+{hunk['changes']['added']}{Colors.ENDC} / {Colors.RED}-{hunk['changes']['removed']}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
        
        # Display the actual changes with syntax highlighting
        for line in hunk['lines']:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"{Colors.GREEN}{line.rstrip()}{Colors.ENDC}")
            elif line.startswith('-') and not line.startswith('---'):
                print(f"{Colors.RED}{line.rstrip()}{Colors.ENDC}")
            else:
                print(line.rstrip())
    
    def _apply_hunk(self, file_path: Path, hunk: Dict, original_lines: List[str]) -> List[str]:
        """Apply a single hunk to the file"""
        result = original_lines.copy()
        
        # Build the new content for this hunk
        new_content = []
        for line in hunk['lines']:
            if not line.startswith('-'):  # Keep everything except removed lines
                if line.startswith('+'):
                    new_content.append(line[1:])  # Remove the + prefix
                else:
                    new_content.append(line[1:] if line.startswith(' ') else line)
        
        # Apply the changes (simplified - in production, use proper patch library)
        # This is a basic implementation
        start = hunk['old_start'] - 1
        end = start + hunk['old_count']
        
        # Replace the old lines with new ones
        result[start:end] = new_content
        
        return result
    
    def review_file(self, label: str) -> Dict:
        """Interactive review of a single file"""
        if label not in self.tracking_data.get('labels', {}).get('updates', {}):
            print(f"{Colors.RED}❌ Invalid label: {label}{Colors.ENDC}")
            return {'status': 'error'}
        
        file_path = self.tracking_data['labels']['updates'][label]
        update_dir = self.updates_dir / label
        
        # Get file paths
        diff_file = list(update_dir.glob("*.diff"))[0]
        old_file = list(update_dir.glob("*.OLD"))[0]
        new_file = list(update_dir.glob("*.NEW"))[0]
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📝 Reviewing: {file_path}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*70}{Colors.ENDC}")
        
        # Parse diff into hunks
        hunks = self._parse_diff_file(diff_file)
        
        if not hunks:
            print(f"{Colors.YELLOW}No changes found in diff{Colors.ENDC}")
            return {'status': 'no_changes'}
        
        # Review each hunk
        approved_hunks = []
        rejected_hunks = []
        
        for i, hunk in enumerate(hunks, 1):
            self._display_hunk(hunk, i, len(hunks))
            
            while True:
                print(f"\n{Colors.BOLD}What would you like to do?{Colors.ENDC}")
                print(f"  {Colors.GREEN}[a]{Colors.ENDC} Accept this change")
                print(f"  {Colors.RED}[r]{Colors.ENDC} Reject this change")
                print(f"  {Colors.YELLOW}[s]{Colors.ENDC} Skip (decide later)")
                print(f"  {Colors.CYAN}[v]{Colors.ENDC} View full context")
                print(f"  {Colors.BLUE}[q]{Colors.ENDC} Quit review")
                
                choice = input(f"\n{Colors.BOLD}Choice: {Colors.ENDC}").lower().strip()
                
                if choice == 'a':
                    approved_hunks.append(hunk)
                    print(f"{Colors.GREEN}✅ Change accepted{Colors.ENDC}")
                    break
                elif choice == 'r':
                    rejected_hunks.append(hunk)
                    print(f"{Colors.RED}❌ Change rejected{Colors.ENDC}")
                    break
                elif choice == 's':
                    print(f"{Colors.YELLOW}⏩ Skipped{Colors.ENDC}")
                    break
                elif choice == 'v':
                    print(f"\n{Colors.CYAN}Full diff context:{Colors.ENDC}")
                    with open(diff_file, 'r') as f:
                        print(f.read())
                elif choice == 'q':
                    return {'status': 'quit'}
                else:
                    print(f"{Colors.RED}Invalid choice{Colors.ENDC}")
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Review Summary:{Colors.ENDC}")
        print(f"  {Colors.GREEN}Approved: {len(approved_hunks)} changes{Colors.ENDC}")
        print(f"  {Colors.RED}Rejected: {len(rejected_hunks)} changes{Colors.ENDC}")
        print(f"  {Colors.YELLOW}Skipped: {len(hunks) - len(approved_hunks) - len(rejected_hunks)} changes{Colors.ENDC}")
        
        # SMART DECISION: If ALL hunks approved -> move to approved
        # If ALL hunks rejected -> move to rejected  
        # Otherwise -> stays in partial
        if len(approved_hunks) == len(hunks):
            # All approved - move to approved section
            self.decisions['approved'][label] = file_path
            # Remove from partial if exists
            if label in self.decisions['partial']:
                del self.decisions['partial'][label]
            print(f"\n{Colors.GREEN}✅ File fully approved and ready to apply!{Colors.ENDC}")
        elif len(rejected_hunks) == len(hunks):
            # All rejected - move to rejected section
            self.decisions['rejected'][label] = file_path
            # Remove from partial if exists
            if label in self.decisions['partial']:
                del self.decisions['partial'][label]
            print(f"\n{Colors.RED}❌ File fully rejected.{Colors.ENDC}")
        else:
            # Mixed or skipped - save in partial
            self.decisions['partial'][label] = {
                'file': file_path,
                'approved': len(approved_hunks),
                'rejected': len(rejected_hunks),
                'total': len(hunks),
                'timestamp': datetime.now().isoformat()
            }
            print(f"\n{Colors.YELLOW}⚠️  Partial review saved. File has mixed decisions.{Colors.ENDC}")
        
        self._save_decisions()
        
        return {
            'status': 'reviewed',
            'approved': approved_hunks,
            'rejected': rejected_hunks,
            'total': hunks
        }
    
    def quick_review_all(self):
        """Quick review mode for all files"""
        updates = self.tracking_data.get('labels', {}).get('updates', {})
        
        if not updates:
            print(f"{Colors.YELLOW}No updates to review{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 Quick Review Mode{Colors.ENDC}")
        print(f"Found {len(updates)} files to review\n")
        
        for label, file_path in updates.items():
            update_dir = self.updates_dir / label
            summary_file = update_dir / "SUMMARY.txt"
            
            # Read summary
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary = f.read()
                
                # Parse summary
                added = 0
                removed = 0
                for line in summary.split('\n'):
                    if 'Lines Added:' in line:
                        added = int(line.split(':')[1].strip())
                    elif 'Lines Removed:' in line:
                        removed = int(line.split(':')[1].strip())
                
                # Display quick summary
                print(f"{Colors.BOLD}[{label}] {Path(file_path).name}{Colors.ENDC}")
                print(f"  Changes: {Colors.GREEN}+{added}{Colors.ENDC} / {Colors.RED}-{removed}{Colors.ENDC}")
                
                # Quick decision
                print(f"  {Colors.GREEN}[a]{Colors.ENDC}ccept  {Colors.RED}[r]{Colors.ENDC}eject  {Colors.YELLOW}[v]{Colors.ENDC}iew  {Colors.CYAN}[s]{Colors.ENDC}kip  {Colors.BLUE}[q]{Colors.ENDC}uit")
                choice = input(f"  Choice: ").lower().strip()
                
                if choice == 'a':
                    self.decisions['approved'][label] = file_path
                    print(f"  {Colors.GREEN}✅ Approved{Colors.ENDC}\n")
                elif choice == 'r':
                    self.decisions['rejected'][label] = file_path
                    print(f"  {Colors.RED}❌ Rejected{Colors.ENDC}\n")
                elif choice == 'v':
                    self.review_file(label)
                elif choice == 'q':
                    print(f"\n{Colors.YELLOW}⚠️  Review stopped. Changes saved but NOT applied.{Colors.ENDC}")
                    print(f"{Colors.CYAN}ℹ️  To apply approved changes later, run:{Colors.ENDC}")
                    print(f"    {Colors.BOLD}python3 review.py --apply{Colors.ENDC}\n")
                    self._save_decisions()
                    self._show_final_summary()
                    return  # Exit the function early
                else:
                    print(f"  {Colors.YELLOW}⏩ Skipped{Colors.ENDC}\n")
        
        self._save_decisions()
        self._show_final_summary()
    
    def _show_final_summary(self, ask_to_apply=True):
        """Show final summary of decisions"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Final Review Summary{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*50}{Colors.ENDC}")
        print(f"{Colors.GREEN}Approved: {len(self.decisions['approved'])} files{Colors.ENDC}")
        print(f"{Colors.RED}Rejected: {len(self.decisions['rejected'])} files{Colors.ENDC}")
        print(f"{Colors.YELLOW}Partial: {len(self.decisions['partial'])} files{Colors.ENDC}")
        
        # Generate apply script if there are approved changes
        if self.decisions['approved']:
            self._generate_apply_script()
            
            # Ask if user wants to apply now (only if ask_to_apply is True)
            if ask_to_apply:
                print(f"\n{Colors.BOLD}{Colors.CYAN}Would you like to apply the approved changes now?{Colors.ENDC}")
                print(f"  {Colors.GREEN}[y]{Colors.ENDC}es  {Colors.RED}[n]{Colors.ENDC}o")
                apply_now = input(f"  Choice: ").lower().strip()
                
                if apply_now == 'y':
                    self.apply_decisions()
                else:
                    print(f"\n{Colors.YELLOW}ℹ️  Changes saved but not applied.{Colors.ENDC}")
                    print(f"{Colors.CYAN}To apply later, run:{Colors.ENDC}")
                    print(f"    {Colors.BOLD}python3 review.py --apply{Colors.ENDC}")
                    print(f"    {Colors.BOLD}./figma-sync/apply_approved.sh{Colors.ENDC}")
        else:
            print(f"\n{Colors.YELLOW}No approved changes to apply.{Colors.ENDC}")
    
    def _generate_apply_script(self):
        """Generate a script to apply approved changes"""
        script_path = self.sync_dir / "apply_approved.sh"
        
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated script to apply approved changes\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            
            f.write("echo '🚀 Applying approved changes...'\n\n")
            
            for label in self.decisions['approved']:
                f.write(f"echo '  Applying {label}...'\n")
                f.write(f"python3 sync.py --apply-update {label}\n")
            
            f.write("\necho '✅ All approved changes applied!'\n")
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        print(f"\n{Colors.GREEN}✅ Apply script generated: {script_path}{Colors.ENDC}")
        print(f"Run: {Colors.BOLD}./figma-sync/apply_approved.sh{Colors.ENDC}")
    
    def apply_decisions(self):
        """Apply all approved changes (including fully approved partials)"""
        # Check for fully approved files in partial section
        for label, details in self.decisions.get('partial', {}).items():
            if isinstance(details, dict) and details.get('approved', 0) == details.get('total', 0):
                # This file was fully approved, move it to approved
                self.decisions['approved'][label] = details['file']
                print(f"{Colors.CYAN}ℹ️  {label} was fully approved in detailed review{Colors.ENDC}")
        
        if not self.decisions['approved']:
            print(f"{Colors.YELLOW}No approved changes to apply{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BOLD}Applying {len(self.decisions['approved'])} approved changes...{Colors.ENDC}")
        
        for label, file_path in self.decisions['approved'].items():
            print(f"  Applying {label}: {file_path}")
            
            # Get paths
            update_dir = self.updates_dir / label
            new_file = list(update_dir.glob("*.NEW"))[0]
            
            # Apply the change
            target_path = Path(self.tracking_data['old_project']) / file_path
            
            # Backup original
            backup_path = target_path.with_suffix(target_path.suffix + '.backup')
            shutil.copy2(target_path, backup_path)
            
            # Apply new version
            shutil.copy2(new_file, target_path)
            
            print(f"  {Colors.GREEN}✅ Applied{Colors.ENDC}")
        
        print(f"\n{Colors.GREEN}✨ All approved changes applied successfully!{Colors.ENDC}")

class SmartDiffViewer:
    """Enhanced diff viewer with smart features"""
    
    @staticmethod
    def create_side_by_side_view(old_file: Path, new_file: Path) -> str:
        """Create a side-by-side comparison"""
        with open(old_file, 'r') as f:
            old_lines = f.readlines()
        with open(new_file, 'r') as f:
            new_lines = f.readlines()
        
        output = []
        output.append(f"{Colors.BOLD}{'OLD':<40} | {'NEW':<40}{Colors.ENDC}")
        output.append("=" * 81)
        
        differ = difflib.unified_diff(old_lines, new_lines, lineterm='')
        
        for line in differ:
            if line.startswith('+'):
                output.append(f"{' '*40} | {Colors.GREEN}{line[1:].rstrip():<40}{Colors.ENDC}")
            elif line.startswith('-'):
                output.append(f"{Colors.RED}{line[1:].rstrip():<40}{Colors.ENDC} | {' '*40}")
            elif not line.startswith('@'):
                output.append(f"{line.rstrip():<40} | {line.rstrip():<40}")
        
        return '\n'.join(output)
    
    @staticmethod
    def show_smart_diff(label: str, sync_dir: str = "./figma-sync"):
        """Show an intelligent diff with context"""
        sync_path = Path(sync_dir)
        update_dir = sync_path / "03_UPDATED_FILES" / label
        
        if not update_dir.exists():
            print(f"{Colors.RED}Label {label} not found{Colors.ENDC}")
            return
        
        # Get files
        diff_file = list(update_dir.glob("*.diff"))[0]
        
        # Parse and display smartly
        with open(diff_file, 'r') as f:
            content = f.read()
        
        # Identify what type of changes
        imports_changed = 'import' in content
        functions_changed = 'function' in content or '=>' in content
        styles_changed = 'className' in content or 'style' in content
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Smart Diff Analysis for {label}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*50}{Colors.ENDC}")
        
        if imports_changed:
            print(f"📦 {Colors.YELLOW}Import changes detected{Colors.ENDC}")
        if functions_changed:
            print(f"⚡ {Colors.YELLOW}Function changes detected{Colors.ENDC}")
        if styles_changed:
            print(f"🎨 {Colors.YELLOW}Style changes detected{Colors.ENDC}")
        
        print(f"\n{content}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Interactive Diff Reviewer')
    
    parser.add_argument('--review', metavar='LABEL',
                       help='Review a specific file interactively')
    parser.add_argument('--quick', action='store_true',
                       help='Quick review all files')
    parser.add_argument('--apply', action='store_true',
                       help='Apply all approved changes')
    parser.add_argument('--smart-diff', metavar='LABEL',
                       help='Show smart diff analysis')
    parser.add_argument('--side-by-side', metavar='LABEL',
                       help='Show side-by-side comparison')
    parser.add_argument('--sync-dir', default='./figma-sync',
                       help='Sync directory location')
    parser.add_argument('--fix-decisions', action='store_true',
                       help='Fix decisions file (move fully approved partials)')
    parser.add_argument('--show-decisions', action='store_true',
                       help='Show current decisions')
    
    args = parser.parse_args()
    
    reviewer = InteractiveDiffReviewer(args.sync_dir)
    
    if args.fix_decisions:
        # Fix existing decisions file
        fixed = False
        for label, details in list(reviewer.decisions.get('partial', {}).items()):
            if isinstance(details, dict):
                if details.get('approved', 0) == details.get('total', 0) and details.get('total', 0) > 0:
                    # Fully approved - move to approved
                    reviewer.decisions['approved'][label] = details['file']
                    del reviewer.decisions['partial'][label]
                    print(f"{Colors.GREEN}✅ Moved {label} to approved (all {details['total']} changes approved){Colors.ENDC}")
                    fixed = True
                elif details.get('rejected', 0) == details.get('total', 0) and details.get('total', 0) > 0:
                    # Fully rejected - move to rejected
                    reviewer.decisions['rejected'][label] = details['file']
                    del reviewer.decisions['partial'][label]
                    print(f"{Colors.RED}❌ Moved {label} to rejected (all {details['total']} changes rejected){Colors.ENDC}")
                    fixed = True
        
        if fixed:
            reviewer._save_decisions()
            print(f"\n{Colors.GREEN}✅ Decisions file fixed and saved!{Colors.ENDC}")
            print(f"{Colors.CYAN}Now you can run: python3 review.py --apply{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}No fixes needed. Partial reviews have mixed decisions.{Colors.ENDC}")
    
    elif args.show_decisions:
        # Show current decisions
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Current Decisions:{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*50}{Colors.ENDC}")
        
        if reviewer.decisions['approved']:
            print(f"\n{Colors.GREEN}✅ APPROVED ({len(reviewer.decisions['approved'])}):{Colors.ENDC}")
            for label, file in reviewer.decisions['approved'].items():
                print(f"  {label}: {file}")
        
        if reviewer.decisions['rejected']:
            print(f"\n{Colors.RED}❌ REJECTED ({len(reviewer.decisions['rejected'])}):{Colors.ENDC}")
            for label, file in reviewer.decisions['rejected'].items():
                print(f"  {label}: {file}")
        
        if reviewer.decisions['partial']:
            print(f"\n{Colors.YELLOW}⚠️  PARTIAL ({len(reviewer.decisions['partial'])}):{Colors.ENDC}")
            for label, details in reviewer.decisions['partial'].items():
                if isinstance(details, dict):
                    print(f"  {label}: {details['file']}")
                    print(f"    Approved: {details['approved']}/{details['total']}, Rejected: {details['rejected']}/{details['total']}")
    
    elif args.review:
        result = reviewer.review_file(args.review)
        if result['status'] == 'reviewed':
            print(f"\n{Colors.GREEN}Review complete!{Colors.ENDC}")
    
    elif args.quick:
        reviewer.quick_review_all()
    
    elif args.apply:
        reviewer.apply_decisions()
    
    elif args.smart_diff:
        SmartDiffViewer.show_smart_diff(args.smart_diff, args.sync_dir)
    
    elif args.side_by_side:
        # Show side-by-side view
        update_dir = Path(args.sync_dir) / "03_UPDATED_FILES" / args.side_by_side
        if update_dir.exists():
            old_file = list(update_dir.glob("*.OLD"))[0]
            new_file = list(update_dir.glob("*.NEW"))[0]
            print(SmartDiffViewer.create_side_by_side_view(old_file, new_file))
    
    else:
        print(f"{Colors.BOLD}{Colors.CYAN}Interactive Diff Reviewer{Colors.ENDC}")
        print("\nUsage:")
        print("  python3 review.py --quick           # Quick review all files")
        print("  python3 review.py --review U001     # Detailed review of one file")
        print("  python3 review.py --apply           # Apply approved changes")
        print("  python3 review.py --smart-diff U001 # Smart diff analysis")
        print("  python3 review.py --fix-decisions   # Fix decisions file")
        print("  python3 review.py --show-decisions  # Show current decisions")
        print("\nQuick Start:")
        print("  1. Run: python3 review.py --quick")
        print("  2. Press 'a' to accept, 'r' to reject, 'v' to view details")
        print("  3. Run: python3 review.py --apply")

if __name__ == "__main__":
    main()