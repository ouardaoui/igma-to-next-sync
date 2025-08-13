# sync.py - Figma Sync Manager 🔄

Intelligent sync manager that compares your existing project with Figma exports, organizing all changes into labeled categories for selective application.

## 🎯 Purpose

Instead of blindly overwriting your project with Figma exports, this tool:
- Identifies what's new, updated, or deleted
- Organizes changes with labels (F001, N001, U001)
- Lets you selectively apply changes
- Creates diffs for all modified files
- Maintains full control over your codebase

## 📋 Commands

### Initial Analysis
```bash
# Analyze differences between old and new projects
python3 sync.py --analyze ~/Desktop/labgenz.ai/frontend ~/Desktop/frontend

# Specify custom output directory
python3 sync.py --analyze ~/Desktop/old ~/Desktop/new --output ./my-sync
```

### Working with Changes
```bash
# List all changes with labels
python3 sync.py --list-all

# Add specific new folder
python3 sync.py --add-folder F001

# Add specific new file
python3 sync.py --add-file N003

# Apply specific update
python3 sync.py --apply-update U005

# View diff before applying
python3 sync.py --view-diff U005
```

### Batch Operations
```bash
# Add ALL new folders at once
python3 sync.py --add-all-folders

# Add ALL new files at once
python3 sync.py --add-all-files

# Apply ALL updates (creates backups)
python3 sync.py --apply-all-updates
```

## 📁 Output Structure

After analysis, creates organized structure:

```
figma-sync/
├── 00_REPORTS/
│   ├── SUMMARY.md           # Human-readable summary
│   └── sync_tracking.json   # Machine-readable tracking
│
├── 01_NEW_FOLDERS/
│   ├── README.md            # List of all new folders
│   ├── F001/                # Label F001
│   │   └── components/...   # Actual folder contents
│   ├── F002/
│   └── F003/
│
├── 02_NEW_FILES/
│   ├── README.md            # List of all new files
│   ├── N001/
│   │   ├── NewComponent.tsx # The actual file
│   │   └── INFO.txt        # Where it will be placed
│   └── N002/
│
├── 03_UPDATED_FILES/
│   ├── README.md            # List of all updates
│   ├── U001/
│   │   ├── App.tsx.OLD     # Your current version
│   │   ├── App.tsx.NEW     # Figma's version
│   │   ├── App.tsx.diff    # The differences
│   │   └── SUMMARY.txt     # Quick stats
│   └── U002/
│
└── 04_DELETED_ITEMS/
    └── DELETED_ITEMS.md    # Items removed in Figma
```

## 🏷️ Label System

### Folder Labels (F###)
- **F001, F002, F003...** - New folders from Figma
- Each contains the full folder structure
- Apply with: `python3 sync.py --add-folder F001`

### File Labels (N###)
- **N001, N002, N003...** - New files from Figma
- Each contains the file and its metadata
- Apply with: `python3 sync.py --add-file N001`

### Update Labels (U###)
- **U001, U002, U003...** - Modified files
- Each contains OLD, NEW, and DIFF versions
- Apply with: `python3 sync.py --apply-update U001`

## 📊 Reports

### SUMMARY.md Example
```markdown
# Figma Sync Summary Report

Generated: 2024-01-15 10:30:00

## Statistics
- 📂 **New Folders:** 3
- 📄 **New Files:** 12
- 📝 **Updated Files:** 25
- ❌ **Deleted Folders:** 0
- ❌ **Deleted Files:** 2
- ✅ **Unchanged Files:** 150

## Quick Commands
- Add a new folder: `python3 sync.py --add-folder F001`
- Add a new file: `python3 sync.py --add-file N001`
- Apply an update: `python3 sync.py --apply-update U001`
```

### Label Tables
Each section has a README with tables:

```markdown
| Label | File Path | Added | Removed | Status |
|-------|-----------|-------|---------|--------|
| U001  | App.tsx   | +45   | -12     | Minor  |
| U002  | Button.tsx| +120  | -89     | ⚠️ Major |
```

## 💡 Workflows

### Workflow 1: Careful Review
```bash
# 1. Analyze
python3 sync.py --analyze ~/old ~/new

# 2. Review changes
cd figma-sync
cat 00_REPORTS/SUMMARY.md

# 3. Check specific updates
cat 03_UPDATED_FILES/U001/SUMMARY.txt
cat 03_UPDATED_FILES/U001/App.tsx.diff

# 4. Apply selected changes
python3 ../sync.py --apply-update U001
python3 ../sync.py --add-file N003
```

### Workflow 2: Quick Integration
```bash
# 1. Analyze and list
python3 sync.py --analyze ~/old ~/new
python3 sync.py --list-all

# 2. Add all new components
python3 sync.py --add-folder F001  # components folder

# 3. Skip updates to critical files
# Only apply updates to UI components
python3 sync.py --apply-update U012  # Button.tsx
python3 sync.py --apply-update U013  # Card.tsx
```

### Workflow 3: From Inside figma-sync
```bash
cd figma-sync

# All commands work from inside
python3 ../sync.py --list-all
python3 ../sync.py --add-file N001
python3 ../sync.py --view-diff U003
```

## 🔒 Safety Features

1. **Never overwrites blindly** - Everything is labeled and optional
2. **Backup creation** - Updates create .backup files
3. **Confirmation prompts** - Asks before overwriting existing files
4. **Detailed diffs** - See exactly what changes
5. **Rollback capable** - Keep backups of replaced files

## ⚙️ Advanced Usage

### Custom Ignore Patterns
Automatically ignores:
- node_modules
- .next
- dist
- .git
- build

### File Hash Comparison
Uses MD5 hashing to detect even tiny changes.

### Smart Categorization
- Groups new files by directory
- Sorts updates by impact (lines changed)
- Tracks deletions for awareness

## 📝 Real-World Example

```bash
# Monday: Receive Figma export
python3 sync.py --analyze ~/my-app ~/figma-export

# Review summary
cd figma-sync
cat 00_REPORTS/SUMMARY.md
# Shows: 2 new folders, 8 new files, 15 updates

# Tuesday: Selectively integrate
# Add new UI components folder
python3 ../sync.py --add-folder F001

# Add specific new hooks
python3 ../sync.py --add-file N002  # useAnimation.ts
python3 ../sync.py --add-file N003  # useTheme.ts

# Wednesday: Apply safe updates
# Check Button.tsx changes
python3 ../sync.py --view-diff U008
# Looks good, apply it
python3 ../sync.py --apply-update U008

# Skip App.tsx update (too many conflicts)
# Skip U001

# Thursday: Final integration
npm install
npm run build
npm test
```

## 🚨 Important Notes

1. **Always analyze first** - Don't skip the analysis step
2. **Review major updates** - Check U### folders marked "⚠️ Major"
3. **Test after applying** - Run your test suite after changes
4. **Keep the figma-sync folder** - It's your change history

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No sync data found" | Run `--analyze` first |
| "Label not found" | Check with `--list-all` |
| "File exists" | Either skip or confirm overwrite |
| Permission denied | Check file permissions |

## 📊 Typical Statistics

For a medium Next.js project:
- Analysis time: 5-15 seconds
- New folders: 0-5
- New files: 5-50
- Updated files: 20-100
- Unchanged files: 100-500

---
*Script Version: 1.0*