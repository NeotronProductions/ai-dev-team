#!/usr/bin/env python3
"""Check and setup Ollama with qwen2.5-coder:3b"""

import subprocess
import sys

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        result = subprocess.run(['curl', '-sSf', 'http://localhost:11434/api/tags'], 
                              capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False

def check_model_available(model_name="qwen2.5-coder:3b"):
    """Check if model is available"""
    try:
        result = subprocess.run(['curl', '-sSf', 'http://localhost:11434/api/tags'], 
                              capture_output=True, timeout=2, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            models = [m['name'] for m in data.get('models', [])]
            return any(model_name in m for m in models)
        return False
    except:
        return False

def pull_model(model_name="qwen2.5-coder:3b"):
    """Pull the model"""
    print(f"📥 Pulling {model_name}...")
    try:
        result = subprocess.run(['ollama', 'pull', model_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {model_name} pulled successfully")
            return True
        else:
            print(f"❌ Error pulling model: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Ollama command not found. Is Ollama installed?")
        return False

if __name__ == "__main__":
    model = "qwen2.5-coder:3b"
    
    print("🔍 Checking Ollama setup...")
    print("")
    
    if not check_ollama_running():
        print("❌ Ollama is not running")
        print("")
        print("To start Ollama:")
        print("  1. Install Ollama: https://ollama.ai")
        print("  2. Start it: ollama serve")
        print("  3. Or run as service: systemctl start ollama")
        sys.exit(1)
    
    print("✓ Ollama is running")
    
    if not check_model_available(model):
        print(f"⚠ {model} not found")
        print("")
        pull = input(f"Pull {model} now? (y/n): ").strip().lower()
        if pull == 'y':
            if pull_model(model):
                print(f"✓ {model} is now available")
            else:
                sys.exit(1)
        else:
            print(f"⚠ {model} is required for github_simple.py")
            sys.exit(1)
    else:
        print(f"✓ {model} is available")
    
    print("")
    print("✅ Ollama is ready to use!")
