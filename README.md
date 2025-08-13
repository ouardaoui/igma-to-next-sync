# Figma Project Management Suite 🚀

A comprehensive toolkit for managing Figma exports and integrating them with your existing Next.js/TypeScript projects.

## 📦 Suite Components

1. **`analyze_project.py`** - Project Analysis & Optimization Tool
2. **`clean_imports.py`** - Import Version Cleaner
3. **`sync.py`** - Figma Sync Manager

## 🎯 Quick Start

```bash
# 1. First, analyze your new Figma export
python3 analyze_project.py ~/Desktop/frontend --backup

# 2. Clean version numbers from imports
python3 clean_imports.py ~/Desktop/frontend --update-package-json

# 3. Sync changes between old and new versions
python3 sync.py --analyze ~/Desktop/labgenz.ai/frontend ~/Desktop/frontend
```

## 📋 Workflow Overview

### Step 1: Receive Figma Export
When you receive a new Figma export, you'll typically have:
- Your current project: `~/Desktop/labgenz.ai/frontend`
- New Figma export: `~/Desktop/frontend`

### Step 2: Initial Analysis
```bash
# Analyze the new Figma export for issues
python3 analyze_project.py ~/Desktop/frontend --backup --output analysis.txt
```

### Step 3: Clean Imports
```bash
# Remove version numbers from imports (Figma issue)
python3 clean_imports.py ~/Desktop/frontend --update-package-json
```

### Step 4: Compare & Sync
```bash
# Compare old vs new and organize changes
python3 sync.py --analyze ~/Desktop/labgenz.ai/frontend ~/Desktop/frontend

# Review and apply specific changes
python3 sync.py --list-all
python3 sync.py --add-file N001
python3 sync.py --apply-update U003
```

## 🛠️ Installation

### Prerequisites
```bash
# Python 3.6+ required
python3 --version

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Setup
```bash
# Clone or download the scripts
git clone <your-repo>
cd figma-project-tools

# No additional dependencies required - uses Python stdlib only!
```

## 📚 Individual Script Documentation

- [analyze_project.py README](./README_analyze_project.md)
- [clean_imports.py README](./README_clean_imports.md)
- [sync.py README](./README_sync.md)

## 💡 Common Use Cases

### Case 1: First Time Figma Import
```bash
python3 analyze_project.py ~/Desktop/frontend --backup
python3 clean_imports.py ~/Desktop/frontend
cd ~/Desktop/frontend && npm install
```

### Case 2: Updating Existing Project
```bash
python3 sync.py --analyze ~/Desktop/my-project ~/Desktop/figma-export
cd figma-sync
python3 ../sync.py --list-all
# Selectively apply changes
```

### Case 3: Quick Diff Check
```bash
python3 analyze_project.py --diff ~/Desktop/old ~/Desktop/new --output changes.diff
```

## 🔧 Configuration

Create a `config.json` file for default settings (optional):
```json
{
  "backup_dir": "./backups",
  "output_dir": "./figma-sync",
  "auto_backup": true,
  "skip_dirs": ["node_modules", ".next", "dist", ".git"]
}
```


## 📝 License

These scripts are provided as-is for managing Figma exports. Use at your own discretion.

## 🆘 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x *.py
   ```

2. **Module Not Found**
   - Scripts use only Python standard library
   - Ensure Python 3.6+ is installed

3. **Path Not Found**
   - Use absolute paths or ensure you're in the correct directory
   - Check paths with `pwd` command

## 📞 Support

For issues or questions:
1. Check individual script READMEs
2. Run scripts with `--help` flag
3. Review error messages - they're designed to be helpful!

---
*Last Updated: 2025*