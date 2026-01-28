#!/usr/bin/env python3
"""
Helper function to gather project context for CrewAI agents
This reads project files to understand tech stack, structure, and conventions
"""

import os
from pathlib import Path
import json
import subprocess

def get_project_context(work_dir: Path) -> str:
    """Gather project context from repository files"""
    context_parts = []
    
    # 1. Read README if exists
    readme_path = work_dir / "README.md"
    if readme_path.exists():
        try:
            readme_content = readme_path.read_text(encoding='utf-8')[:2000]  # First 2000 chars
            context_parts.append(f"## Project README\n{readme_content}\n")
        except:
            pass
    
    # 2. Check for package.json (Node.js/JavaScript projects)
    package_json = work_dir / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text())
            context_parts.append("## Tech Stack (from package.json)\n")
            context_parts.append(f"- **Project Name**: {pkg.get('name', 'Unknown')}\n")
            context_parts.append(f"- **Description**: {pkg.get('description', 'N/A')}\n")
            if pkg.get('dependencies'):
                deps = list(pkg['dependencies'].keys())[:10]  # Top 10
                context_parts.append(f"- **Dependencies**: {', '.join(deps)}\n")
            if pkg.get('devDependencies'):
                dev_deps = list(pkg['devDependencies'].keys())[:10]
                context_parts.append(f"- **Dev Dependencies**: {', '.join(dev_deps)}\n")
            context_parts.append("\n")
        except:
            pass
    
    # 3. Check for requirements.txt (Python projects)
    requirements = work_dir / "requirements.txt"
    if requirements.exists():
        try:
            reqs = requirements.read_text(encoding='utf-8')[:1000]
            context_parts.append("## Python Dependencies\n")
            context_parts.append(f"```\n{reqs}\n```\n\n")
        except:
            pass
    
    # 4. Check project structure
    try:
        files = list(work_dir.iterdir())
        file_types = {}
        for f in files:
            if f.is_file():
                ext = f.suffix
                file_types[ext] = file_types.get(ext, 0) + 1
        
        if file_types:
            context_parts.append("## Project Structure\n")
            context_parts.append(f"- **File types found**: {', '.join(sorted(file_types.keys()))}\n")
            
            # Check for common directories
            common_dirs = ['src', 'lib', 'app', 'components', 'public', 'static', 'templates', 'tests', 'test']
            found_dirs = [d for d in common_dirs if (work_dir / d).exists()]
            if found_dirs:
                context_parts.append(f"- **Key directories**: {', '.join(found_dirs)}\n")
            context_parts.append("\n")
    except:
        pass
    
    # 5. Check git branches (might indicate project structure)
    try:
        result = subprocess.run(['git', 'branch', '-a'], cwd=work_dir, 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            branches = [b.strip() for b in result.stdout.split('\n') if b.strip()][:5]
            if len(branches) > 1:
                context_parts.append("## Git Branches\n")
                context_parts.append(f"- Active branches: {', '.join(branches[:5])}\n\n")
    except:
        pass
    
    # 6. Look for config files that indicate tech stack
    config_files = {
        'tsconfig.json': 'TypeScript',
        'webpack.config.js': 'Webpack',
        'vite.config.js': 'Vite',
        'next.config.js': 'Next.js',
        'vue.config.js': 'Vue.js',
        'angular.json': 'Angular',
        'Cargo.toml': 'Rust',
        'go.mod': 'Go',
        'pom.xml': 'Java/Maven',
        'build.gradle': 'Java/Gradle',
        'composer.json': 'PHP',
        'Gemfile': 'Ruby',
    }
    
    found_tech = []
    for config_file, tech in config_files.items():
        if (work_dir / config_file).exists():
            found_tech.append(tech)
    
    if found_tech:
        context_parts.append("## Detected Technologies\n")
        context_parts.append(f"- {', '.join(found_tech)}\n\n")
    
    # Combine all context
    if context_parts:
        return "\n".join(context_parts)
    else:
        return "## Project Context\nNo specific project context detected. Assume standard project layout.\n\n"
