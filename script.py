#!/usr/bin/env python3
"""
Figma Project Analyzer & Automation Tool
Analyzes Next.js/TypeScript projects exported from Figma and helps with:
- File structure analysis
- Identifying issues
- Creating diffs
- Generating migration scripts
"""

import os
import json
import shutil
import hashlib
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
import subprocess
import re

class FigmaProjectAnalyzer:
    def __init__(self, project_path: str, backup_dir: str = "./backups"):
        self.project_path = Path(project_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.issues = []
        self.file_hashes = {}
        self.component_map = {}
        
    def create_backup(self) -> str:
        """Create a timestamped backup of the project"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        print(f"📦 Creating backup at {backup_path}")
        shutil.copytree(self.project_path, backup_path, 
                       ignore=shutil.ignore_patterns('node_modules', '.next', 'dist'))
        return str(backup_path)
    
    def analyze_structure(self) -> Dict:
        """Analyze project structure and identify patterns"""
        analysis = {
            "total_files": 0,
            "components": [],
            "pages": [],
            "api_routes": [],
            "styles": [],
            "types": [],
            "imports": [],
            "issues": []
        }
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip node_modules and build directories
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.next', 'dist']]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.project_path)
                
                if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                    analysis["total_files"] += 1
                    
                    # Categorize files
                    if 'components' in str(rel_path):
                        analysis["components"].append(str(rel_path))
                        self._analyze_component(file_path)
                    elif 'pages' in str(rel_path) or 'app' in str(rel_path):
                        analysis["pages"].append(str(rel_path))
                    elif 'api' in str(rel_path):
                        analysis["api_routes"].append(str(rel_path))
                    elif 'types' in str(rel_path):
                        analysis["types"].append(str(rel_path))
                    elif 'imports' in str(rel_path):
                        analysis["imports"].append(str(rel_path))
                        
                elif file.endswith(('.css', '.scss', '.sass')):
                    analysis["styles"].append(str(rel_path))
                
                # Calculate file hash for diff tracking
                self.file_hashes[str(rel_path)] = self._get_file_hash(file_path)
        
        return analysis
    
    def _analyze_component(self, file_path: Path):
        """Analyze individual component for issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for common Figma export issues
            issues = []
            
            # Check for hardcoded values
            if re.search(r'(width|height):\s*["\']?\d+px', content):
                issues.append(f"Hardcoded dimensions in {file_path.name}")
            
            # Check for missing TypeScript types
            if file_path.suffix == '.tsx' and 'any' in content:
                issues.append(f"Using 'any' type in {file_path.name}")
            
            # Check for unused imports
            imports = re.findall(r'import\s+(?:{[^}]+}|\w+)\s+from\s+["\']([^"\']+)["\']', content)
            for imp in imports:
                if imp.startswith('./svg-') or imp.startswith('../svg-'):
                    issues.append(f"SVG import in {file_path.name}: {imp}")
            
            # Check for missing error handling
            if 'try' not in content and ('fetch' in content or 'async' in content):
                issues.append(f"Missing error handling in async code: {file_path.name}")
            
            if issues:
                self.issues.extend(issues)
                
        except Exception as e:
            self.issues.append(f"Error analyzing {file_path}: {e}")
    
    def identify_issues(self) -> List[Dict]:
        """Identify common issues in Figma-exported code"""
        issues_found = []
        
        # Check package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                
            # Check for missing dependencies
            required_deps = ['axios', 'swr', 'react-query']  # Common API deps
            for dep in required_deps:
                if dep not in package_data.get('dependencies', {}):
                    issues_found.append({
                        "type": "missing_dependency",
                        "description": f"Missing {dep} for API integration",
                        "fix": f"npm install {dep}"
                    })
        
        # Check for API configuration
        env_file = self.project_path / ".env.local"
        if not env_file.exists():
            issues_found.append({
                "type": "missing_config",
                "description": "No .env.local file for API configuration",
                "fix": "Create .env.local with API_URL and other configs"
            })
        
        # Add component-specific issues
        for issue in self.issues:
            issues_found.append({
                "type": "code_quality",
                "description": issue,
                "fix": "Manual review required"
            })
        
        return issues_found
    
    def generate_api_layer(self) -> Dict[str, str]:
        """Generate API integration layer"""
        api_files = {}
        
        # Base API configuration
        api_files['lib/api/config.ts'] = """
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle authentication error
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
"""
        
        # API hooks
        api_files['lib/api/hooks.ts'] = """
import { useState, useEffect } from 'react';
import { apiClient } from './config';

export function useApi<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get(endpoint);
        setData(response.data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint]);

  return { data, loading, error };
}

export function useMutation<T, P>(endpoint: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = async (payload: P): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.post(endpoint, payload);
      return response.data;
    } catch (err) {
      setError(err as Error);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { mutate, loading, error };
}
"""
        
        # API types
        api_files['lib/api/types.ts'] = """
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'completed' | 'archived';
  createdAt: string;
  updatedAt: string;
}

export interface Task {
  id: string;
  projectId: string;
  title: string;
  description: string;
  status: 'todo' | 'in-progress' | 'done';
  assignee?: User;
  priority: 'low' | 'medium' | 'high';
  dueDate?: string;
}
"""
        
        return api_files
    
    def optimize_performance(self) -> List[Dict]:
        """Generate performance optimization suggestions"""
        optimizations = []
        
        # Check for dynamic imports
        for comp in self.component_map.keys():
            optimizations.append({
                "file": comp,
                "suggestion": "Use dynamic imports for heavy components",
                "code": f"const {Path(comp).stem} = dynamic(() => import('{comp}'), {{ ssr: false }})"
            })
        
        # Image optimization
        optimizations.append({
            "file": "next.config.js",
            "suggestion": "Configure image optimization",
            "code": """
module.exports = {
  images: {
    domains: ['your-api-domain.com'],
    formats: ['image/avif', 'image/webp'],
  },
  compress: true,
  poweredByHeader: false,
}
"""
        })
        
        # Bundle optimization
        optimizations.append({
            "file": "package.json",
            "suggestion": "Add bundle analyzer",
            "code": "npm install --save-dev @next/bundle-analyzer"
        })
        
        return optimizations
    
    def create_diff_report(self, original_path: str, modified_path: str) -> str:
        """Create a diff report between two versions"""
        diff_report = []
        
        original = Path(original_path)
        modified = Path(modified_path)
        
        for root, dirs, files in os.walk(modified):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.next', 'dist']]
            
            for file in files:
                if not file.endswith(('.tsx', '.ts', '.jsx', '.js', '.css')):
                    continue
                    
                mod_file = Path(root) / file
                rel_path = mod_file.relative_to(modified)
                orig_file = original / rel_path
                
                if orig_file.exists():
                    with open(orig_file, 'r', encoding='utf-8') as f1:
                        orig_lines = f1.readlines()
                    with open(mod_file, 'r', encoding='utf-8') as f2:
                        mod_lines = f2.readlines()
                    
                    diff = list(difflib.unified_diff(
                        orig_lines, mod_lines,
                        fromfile=str(rel_path),
                        tofile=str(rel_path),
                        n=3
                    ))
                    
                    if diff:
                        diff_report.append(''.join(diff))
                else:
                    diff_report.append(f"NEW FILE: {rel_path}\n")
        
        return '\n'.join(diff_report)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for tracking changes"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 60)
        report.append("FIGMA PROJECT ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Project Path: {self.project_path}")
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Structure analysis
        structure = self.analyze_structure()
        report.append("PROJECT STRUCTURE:")
        report.append(f"  Total Files: {structure['total_files']}")
        report.append(f"  Components: {len(structure['components'])}")
        report.append(f"  Pages: {len(structure['pages'])}")
        report.append(f"  API Routes: {len(structure['api_routes'])}")
        report.append(f"  Styles: {len(structure['styles'])}")
        report.append(f"  Types: {len(structure['types'])}")
        report.append(f"  Figma Imports: {len(structure['imports'])}")
        report.append("")
        
        # Issues
        issues = self.identify_issues()
        report.append(f"ISSUES FOUND: {len(issues)}")
        for i, issue in enumerate(issues, 1):
            report.append(f"  {i}. [{issue['type']}] {issue['description']}")
            report.append(f"     Fix: {issue['fix']}")
        report.append("")
        
        # Performance optimizations
        optimizations = self.optimize_performance()
        report.append(f"PERFORMANCE OPTIMIZATIONS: {len(optimizations)}")
        for opt in optimizations[:5]:  # Show first 5
            report.append(f"  - {opt['suggestion']}")
        report.append("")
        
        # API Integration
        report.append("API INTEGRATION:")
        api_files = self.generate_api_layer()
        for file_path in api_files.keys():
            report.append(f"  - Generate: {file_path}")
        report.append("")
        
        report.append("=" * 60)
        
        return '\n'.join(report)
    
    def apply_fixes(self, auto_fix: bool = False):
        """Apply automatic fixes to the project"""
        if not auto_fix:
            print("⚠️  Auto-fix disabled. Run with --auto-fix to apply changes.")
            return
        
        print("🔧 Applying automatic fixes...")
        
        # Create API layer
        api_files = self.generate_api_layer()
        for file_path, content in api_files.items():
            full_path = self.project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"  ✅ Created {file_path}")
        
        # Create .env.local template
        env_template = """
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_APP_NAME=MyApp

# Authentication
JWT_SECRET=your-secret-key-here

# Database (if needed)
DATABASE_URL=postgresql://user:password@localhost:5432/myapp
"""
        env_file = self.project_path / ".env.local.example"
        with open(env_file, 'w') as f:
            f.write(env_template)
        print(f"  ✅ Created .env.local.example")
        
        # Update package.json scripts
        package_json = self.project_path / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            package_data['scripts']['analyze'] = "ANALYZE=true next build"
            package_data['scripts']['lint:fix'] = "next lint --fix"
            
            with open(package_json, 'w') as f:
                json.dump(package_data, f, indent=2)
            print(f"  ✅ Updated package.json scripts")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze and optimize Figma-exported Next.js project')
    parser.add_argument('project_path', nargs='?', help='Path to the project directory')
    parser.add_argument('--backup', action='store_true', help='Create backup before analysis')
    parser.add_argument('--auto-fix', action='store_true', help='Apply automatic fixes')
    parser.add_argument('--diff', nargs=2, metavar=('ORIGINAL', 'MODIFIED'), 
                       help='Generate diff report between two versions')
    parser.add_argument('--output', help='Output report to file')
    
    args = parser.parse_args()
    
    # Generate diff if requested (doesn't need project_path)
    if args.diff:
        # Use the first path as the project path for the analyzer
        analyzer = FigmaProjectAnalyzer(args.diff[1])  # Use modified path as base
        diff_report = analyzer.create_diff_report(args.diff[0], args.diff[1])
        if args.output:
            with open(args.output, 'w') as f:
                f.write(diff_report)
            print(f"📄 Diff report saved to {args.output}")
        else:
            print(diff_report)
        return
    
    # For non-diff operations, project_path is required
    if not args.project_path:
        parser.error("project_path is required unless using --diff")
        return
    
    analyzer = FigmaProjectAnalyzer(args.project_path)
    
    # Create backup if requested
    if args.backup:
        backup_path = analyzer.create_backup()
        print(f"✅ Backup created: {backup_path}")
    
    # Run analysis
    print("🔍 Analyzing project...")
    report = analyzer.generate_report()
    
    # Apply fixes if requested
    if args.auto_fix:
        analyzer.apply_fixes(auto_fix=True)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to {args.output}")
    else:
        print(report)
    
    print("\n✨ Analysis complete!")

if __name__ == "__main__":
    main()