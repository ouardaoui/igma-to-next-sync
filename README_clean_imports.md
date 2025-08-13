# clean_imports.py - Import Version Cleaner 🧹

Removes version numbers from imports in Figma-exported code. Figma exports often include version numbers in imports like `@1.1.2`, which breaks normal npm/yarn workflows.

## 🎯 Purpose

Fixes imports from:
```javascript
import { Button } from "@radix-ui/react-button@1.0.4";
```

To:
```javascript
import { Button } from "@radix-ui/react-button";
```

## 📋 Commands

### Basic Cleaning
```bash
# Clean imports with automatic backup
python3 clean_imports.py ~/Desktop/frontend/

# Clean without backup (faster but risky)
python3 clean_imports.py ~/Desktop/frontend/ --no-backup
```

### Preview Mode
```bash
# See what would change WITHOUT modifying files
python3 clean_imports.py ~/Desktop/frontend/ --dry-run
```

### Package.json Updates
```bash
# Clean imports AND update package.json with found versions
python3 clean_imports.py ~/Desktop/frontend/ --update-package-json
```

### Reporting
```bash
# Generate detailed report
python3 clean_imports.py ~/Desktop/frontend/ --output cleanup_report.txt

# Verbose mode (show all changes, not just first 10)
python3 clean_imports.py ~/Desktop/frontend/ --verbose
```

### Combined Commands
```bash
# Full cleanup with package.json update and report
python3 clean_imports.py ~/Desktop/frontend/ --update-package-json --output report.txt
```

## 📊 What It Does

### 1. **Scans Files**
Processes all JavaScript/TypeScript files:
- `.js`, `.jsx`
- `.ts`, `.tsx`
- `.mjs`, `.cjs`

### 2. **Identifies Versioned Imports**
Finds patterns like:
- ES6: `import ... from "package@version"`
- CommonJS: `require("package@version")`
- Dynamic: `import("package@version")`

### 3. **Extracts Package Versions**
Records all found versions for package.json updates:
```
@radix-ui/react-slot: 1.1.2
class-variance-authority: 0.7.1
framer-motion: 10.16.4
```

### 4. **Creates Backups**
Default backup location with timestamp:
```
backup_imports_20240115_103000/
```

## 📁 Output Structure

### Dry Run Output
```
🔍 DRY RUN MODE - No files will be modified

📋 Found imports with versions:
  @radix-ui/react-slot@1.1.2
  class-variance-authority@0.7.1
  framer-motion@10.16.4

📁 Would process 45 files

🔄 Sample of changes that would be made:
  File: Button.tsx, Line 2
    Before: import { Slot } from "@radix-ui/react-slot@1.1.2";
    After:  import { Slot } from "@radix-ui/react-slot";
```

### Cleanup Report
```
============================
IMPORT VERSION CLEANUP REPORT
============================
Project: /home/user/Desktop/frontend
Date: 2024-01-15 10:30:00

SUMMARY:
  Files processed: 45
  Imports cleaned: 127
  Total changes: 127
  Backup location: ../backup_imports_20240115_103000

PACKAGE VERSIONS FOUND:
  @radix-ui/react-accordion: 1.2.1
  @radix-ui/react-slot: 1.1.2
  class-variance-authority: 0.7.1
  framer-motion: 10.16.4

SAMPLE CHANGES (first 10):
  File: components/ui/button.tsx, Line 3
    From: @radix-ui/react-slot@1.1.2
    To:   @radix-ui/react-slot

RECOMMENDED PACKAGE.JSON UPDATES:
  Add to dependencies:
    "@radix-ui/react-slot": "^1.1.2"
    "class-variance-authority": "^0.7.1"
============================
```

## 💡 Use Cases

### Case 1: Fresh Figma Export
```bash
# 1. Preview changes
python3 clean_imports.py ~/Desktop/figma-export --dry-run

# 2. Clean and update package.json
python3 clean_imports.py ~/Desktop/figma-export --update-package-json

# 3. Install dependencies
cd ~/Desktop/figma-export
npm install
```

### Case 2: Quick Fix
```bash
# One command to fix everything
python3 clean_imports.py ~/Desktop/project --update-package-json && \
cd ~/Desktop/project && \
npm install && \
npm run build
```

### Case 3: Safe Approach
```bash
# 1. Dry run first
python3 clean_imports.py ~/Desktop/project --dry-run > preview.txt

# 2. Review changes
cat preview.txt

# 3. Apply if looks good
python3 clean_imports.py ~/Desktop/project --output report.txt

# 4. Verify
npm run build
```

## 🔒 Safety Features

1. **Automatic Backups** - Creates timestamped backup by default
2. **Dry Run Mode** - Preview without modifying
3. **Detailed Reporting** - Know exactly what changed
4. **Smart Detection** - Only modifies import statements
5. **Preserves Code** - Only removes versions, nothing else

## 📦 Package.json Integration

When using `--update-package-json`:

### Before
```json
{
  "dependencies": {
    "react": "^18.2.0"
  }
}
```

### After
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "@radix-ui/react-slot": "^1.1.2",
    "class-variance-authority": "^0.7.1",
    "framer-motion": "^10.16.4"
  }
}
```

## ⚙️ Advanced Features

### Version Conflict Detection
If multiple versions of the same package are found:
```
Warning: Multiple versions found for 'react':
  - 18.2.0
  - 18.3.0
Using latest: 18.3.0
```

### Ignored Directories
Automatically skips:
- node_modules
- .next
- dist
- .git
- build

### File Encoding
Handles UTF-8 encoded files properly.

## 🚨 Important Notes

1. **Always in Figma exports** - This issue is specific to Figma code exports
2. **Run before npm install** - Clean imports before installing packages
3. **Check git diff** - Review changes if project is in git

## 📝 Examples

### Complete Workflow
```bash
# 1. Check what needs cleaning
python3 clean_imports.py ~/Desktop/app --dry-run

# 2. Clean with backup
python3 clean_imports.py ~/Desktop/app

# 3. Update package.json
python3 clean_imports.py ~/Desktop/app --update-package-json

# 4. Install and build
cd ~/Desktop/app
npm install
npm run build
```

### CI/CD Integration
```bash
#!/bin/bash
# cleanup.sh
python3 clean_imports.py . --no-backup --update-package-json
npm ci
npm run build
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| No changes detected | Check if versions already removed |
| Encoding error | Ensure files are UTF-8 |
| Permission denied | `chmod +x clean_imports.py` |
| Backup failed | Check disk space |

## 📊 Statistics

Typical Figma export cleaning:
- Files processed: 50-200
- Imports cleaned: 100-500
- Time taken: 2-10 seconds
- Backup size: 1-50 MB

---
*Script Version: 1.0*