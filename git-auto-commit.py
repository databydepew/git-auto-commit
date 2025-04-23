#!/usr/bin/env python3
"""
Git Auto Commit Message Generator
A Git plugin that automatically generates meaningful commit messages based on your changes.
Supports both rule-based and AI-powered commit message generation.
"""

import os
import sys
import subprocess
import configparser
from git import Repo
import re
import argparse
import json

# Optional import for OpenAI integration
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def get_git_root():
    """Get the root directory of the Git repository."""
    try:
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                          stderr=subprocess.STDOUT).decode('utf-8').strip()
        return git_root
    except subprocess.CalledProcessError:
        print("Error: Not a git repository (or any of the parent directories)")
        sys.exit(1)

def get_config(git_root):
    """Read configuration from .git-autocommit file if it exists."""
    config = {
        'prefix': '',
        'prefixes': [],
        'max_length': 72,
        'use_ai': False,
        'openai_api_key': '',
        'openai_model': 'gpt-3.5-turbo',
        'conventional_commits': False
    }
    
    config_file = os.path.join(git_root, '.git-autocommit')
    if os.path.exists(config_file):
        parser = configparser.ConfigParser()
        parser.read(config_file)
        if 'autocommit' in parser:
            if 'prefix' in parser['autocommit']:
                config['prefix'] = parser['autocommit']['prefix']
            if 'prefixes' in parser['autocommit']:
                # Parse the comma-separated list of prefixes
                prefixes_str = parser['autocommit']['prefixes']
                if prefixes_str:
                    config['prefixes'] = [p.strip() for p in prefixes_str.split(',')]
            if 'max_length' in parser['autocommit']:
                config['max_length'] = int(parser['autocommit']['max_length'])
            if 'use_ai' in parser['autocommit']:
                config['use_ai'] = parser['autocommit'].getboolean('use_ai')
            if 'openai_api_key' in parser['autocommit']:
                config['openai_api_key'] = parser['autocommit']['openai_api_key']
            if 'openai_model' in parser['autocommit']:
                config['openai_model'] = parser['autocommit']['openai_model']
            if 'conventional_commits' in parser['autocommit']:
                config['conventional_commits'] = parser['autocommit'].getboolean('conventional_commits')
    
    # Check for environment variable override for API key
    if 'OPENAI_API_KEY' in os.environ:
        config['openai_api_key'] = os.environ['OPENAI_API_KEY']
    
    return config

def get_staged_files(repo):
    """Get list of staged files with their status."""
    staged_files = []
    staged_diff = repo.git.diff('--cached', '--name-status')
    
    if not staged_diff:
        print("No changes staged for commit.")
        sys.exit(1)
    
    for line in staged_diff.split('\n'):
        if not line:
            continue
        status, file_path = re.match(r'(\w)\s+(.*)', line).groups()
        staged_files.append((status, file_path))
    
    return staged_files

def categorize_changes(staged_files):
    """Categorize changes by type and file extension."""
    categories = {
        'A': {'count': 0, 'files': []},  # Added
        'M': {'count': 0, 'files': []},  # Modified
        'D': {'count': 0, 'files': []},  # Deleted
        'R': {'count': 0, 'files': []},  # Renamed
        'C': {'count': 0, 'files': []}   # Copied
    }
    
    extensions = {}
    
    for status, file_path in staged_files:
        # Categorize by status
        if status in categories:
            categories[status]['count'] += 1
            categories[status]['files'].append(file_path)
        
        # Categorize by extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lstrip('.')
        if ext:
            extensions[ext] = extensions.get(ext, 0) + 1
    
    return categories, extensions

def get_file_changes(repo, file_path, status):
    """Get specific changes in a file."""
    if status == 'D':
        return "File deleted"
    
    try:
        diff = repo.git.diff('--cached', '--', file_path)
        
        # Extract the most significant changes
        added_lines = []
        removed_lines = []
        
        for line in diff.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:].strip())
        
        return {
            'added': added_lines,
            'removed': removed_lines
        }
    except:
        return "Unable to get diff"

def analyze_changes(repo, staged_files):
    """Analyze the changes to generate a meaningful commit message."""
    categories, extensions = categorize_changes(staged_files)
    
    # Get the most changed file for detailed analysis
    most_changed_category = max(categories.items(), key=lambda x: x[1]['count'])
    
    # Simple heuristic-based message generation
    if len(staged_files) == 1:
        status, file_path = staged_files[0]
        file_name = os.path.basename(file_path)
        
        if status == 'A':
            return f"Add {file_name}"
        elif status == 'M':
            return f"Update {file_name}"
        elif status == 'D':
            return f"Delete {file_name}"
        elif status == 'R':
            return f"Rename file to {file_name}"
    
    # Multiple files changed
    primary_action = None
    if categories['A']['count'] > 0 and categories['A']['count'] >= sum(c['count'] for s, c in categories.items() if s != 'A'):
        primary_action = "Add"
    elif categories['M']['count'] > 0 and categories['M']['count'] >= sum(c['count'] for s, c in categories.items() if s != 'M'):
        primary_action = "Update"
    elif categories['D']['count'] > 0 and categories['D']['count'] >= sum(c['count'] for s, c in categories.items() if s != 'D'):
        primary_action = "Remove"
    
    # Determine the scope of changes
    scope = None
    if len(extensions) == 1:
        ext = next(iter(extensions))
        if ext in ['js', 'ts']:
            scope = "JavaScript"
        elif ext in ['py']:
            scope = "Python"
        elif ext in ['css', 'scss']:
            scope = "styles"
        elif ext in ['html']:
            scope = "HTML"
        elif ext in ['md', 'txt']:
            scope = "documentation"
        elif ext in ['json', 'yaml', 'yml', 'toml']:
            scope = "configuration"
    
    # Generate message based on analysis
    if primary_action and scope:
        return f"{primary_action} {scope} files"
    elif primary_action:
        file_count = sum(c['count'] for c in categories.values())
        return f"{primary_action} {file_count} files"
    else:
        # Fallback to generic message
        file_count = sum(c['count'] for c in categories.values())
        return f"Update {file_count} files"

def get_full_diff(repo):
    """Get the full diff of staged changes."""
    return repo.git.diff('--cached')

def generate_ai_commit_message(repo, staged_files, config):
    """Generate a commit message using AI."""
    if not OPENAI_AVAILABLE:
        print("OpenAI package not installed. Run 'pip install openai' to use AI-powered commit messages.")
        return None
    
    if not config['openai_api_key']:
        print("OpenAI API key not configured. Set it in .git-autocommit file or OPENAI_API_KEY environment variable.")
        return None
    
    # Get the full diff
    diff = get_full_diff(repo)
    if not diff:
        return None
    
    # Truncate diff if it's too large
    if len(diff) > 4000:  # Keeping some room for the prompt
        diff = diff[:4000] + "\n...\n(diff truncated due to size)"
    
    # Configure OpenAI client
    client = openai.OpenAI(api_key=config['openai_api_key'])
    
    # Prepare the prompt
    if config['conventional_commits']:
        system_prompt = """Generate a concise, meaningful git commit message based on the provided diff. 
        Follow the Conventional Commits format: <type>[(scope)]: <description>
        
        Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
        
        Keep the message under 72 characters. Focus on WHAT changed and WHY, not HOW.
        Don't include obvious things like 'Update file.txt'.
        """
    else:
        system_prompt = """Generate a concise, meaningful git commit message based on the provided diff.
        Keep the message under 72 characters. Focus on WHAT changed and WHY, not HOW.
        Don't include obvious things like 'Update file.txt'.
        """
    
    try:
        response = client.chat.completions.create(
            model=config['openai_model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here's the git diff:\n\n{diff}"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        message = response.choices[0].message.content.strip()
        
        # Apply prefix if configured and not using conventional commits
        if config['prefix'] and not config['conventional_commits']:
            message = f"{config['prefix']} {message}"
        
        # Truncate if needed
        if len(message) > config['max_length']:
            message = message[:config['max_length'] - 3] + "..."
        
        return message
    except Exception as e:
        print(f"Error generating AI commit message: {str(e)}")
        return None

def generate_commit_message(repo, staged_files, config):
    """Generate a commit message based on the staged changes."""
    # Try AI-powered message generation first if enabled
    if config['use_ai']:
        ai_message = generate_ai_commit_message(repo, staged_files, config)
        if ai_message:
            return ai_message
        print("Falling back to rule-based commit message generation...")
    
    # Fallback to rule-based message generation
    message = analyze_changes(repo, staged_files)
    
    # Apply prefix if configured
    if config['prefix']:
        message = f"{config['prefix']} {message}"
    
    # Truncate if needed
    if len(message) > config['max_length']:
        message = message[:config['max_length'] - 3] + "..."
    
    return message

def setup_config():
    """Setup initial configuration file."""
    git_root = get_git_root()
    config_file = os.path.join(git_root, '.git-autocommit')
    
    if os.path.exists(config_file):
        print(f"Configuration file already exists at {config_file}")
        return
    
    config = configparser.ConfigParser()
    config['autocommit'] = {
        'prefix': '',
        'prefixes': 'feat:, fix:, docs:, style:, refactor:, perf:, test:, build:, ci:, chore:',
        'max_length': '72',
        'use_ai': 'false',
        'openai_api_key': '',
        'openai_model': 'gpt-3.5-turbo',
        'conventional_commits': 'false'
    }
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print(f"Created configuration file at {config_file}")
    print("Edit this file to customize the behavior of git-autocommit.")

def select_prefix(config):
    """Allow the user to select a prefix from the configured list."""
    if not config['prefixes']:
        return config['prefix']
    
    print("\nSelect a prefix for your commit message:")
    for i, prefix in enumerate(config['prefixes'], 1):
        print(f"{i}. {prefix}")
    print(f"{len(config['prefixes']) + 1}. No prefix")
    print(f"{len(config['prefixes']) + 2}. Custom prefix")
    
    while True:
        try:
            choice = int(input("Enter your choice (number): ").strip())
            if 1 <= choice <= len(config['prefixes']):
                return config['prefixes'][choice - 1]
            elif choice == len(config['prefixes']) + 1:
                return ''
            elif choice == len(config['prefixes']) + 2:
                return input("Enter custom prefix: ").strip()
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Git Auto Commit Message Generator')
    parser.add_argument('--setup', action='store_true', help='Setup initial configuration')
    parser.add_argument('--use-ai', action='store_true', help='Use AI to generate commit message')
    parser.add_argument('--conventional', action='store_true', help='Use Conventional Commits format')
    parser.add_argument('--no-prefix-selection', action='store_true', help='Skip prefix selection')
    args = parser.parse_args()
    
    if args.setup:
        setup_config()
        return
    
    # Get git repository
    git_root = get_git_root()
    repo = Repo(git_root)
    
    # Get configuration
    config = get_config(git_root)
    
    # Override config with command line arguments
    if args.use_ai:
        config['use_ai'] = True
    if args.conventional:
        config['conventional_commits'] = True
    
    # Get staged files
    staged_files = get_staged_files(repo)
    
    # Allow user to select a prefix if there are prefixes configured and not skipped
    if config['prefixes'] and not args.no_prefix_selection:
        selected_prefix = select_prefix(config)
        config['prefix'] = selected_prefix
    
    # Generate commit message
    commit_message = generate_commit_message(repo, staged_files, config)
    
    # Perform the commit
    print(f"\nGenerated commit message: {commit_message}")
    confirm = input("Proceed with this commit message? (y/n/edit): ").strip().lower()
    
    if confirm == 'y':
        repo.git.commit('-m', commit_message)
        print("Changes committed successfully!")
    elif confirm == 'edit':
        edited_message = input("Enter your commit message: ").strip()
        repo.git.commit('-m', edited_message)
        print("Changes committed with edited message!")
    else:
        print("Commit aborted.")

if __name__ == "__main__":
    main()
