# Git Auto Commit Message Generator

A Git plugin that automatically generates meaningful commit messages based on your changes. It supports both rule-based and AI-powered commit message generation.

## Features

- Analyzes git diffs to understand what changed
- Generates concise, descriptive commit messages
- AI-powered commit message generation using OpenAI
- Support for Conventional Commits format
- Command-line arguments for flexible usage
- Easy to install and use
- Highly customizable

## Installation

### Automatic Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/git-auto-commit.git
   ```

2. Run the installation script:
   ```
   cd git-auto-commit
   ./install.sh
   ```
   You may need to use `sudo` if you don't have write permissions to `/usr/local/bin`.

### Manual Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/git-auto-commit.git
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make the script executable:
   ```
   chmod +x git-auto-commit.py
   ```

4. Create a symbolic link to make it available as a git command:
   ```
   ln -s /path/to/git-auto-commit.py /usr/local/bin/git-autocommit
   ```

## Usage

Instead of using `git commit -m "your message"`, simply run:

```
git autocommit
```

This will:
1. Analyze your staged changes
2. Generate an appropriate commit message
3. Prompt you to accept, edit, or reject the message
4. Commit the changes with the chosen message

### Command-line Options

```
git autocommit --setup     # Create a configuration file in your repository
git autocommit --use-ai    # Use AI to generate the commit message
git autocommit --conventional  # Use Conventional Commits format
```

### AI-Powered Commit Messages

To use AI-powered commit message generation, you need an OpenAI API key. You can set it in the configuration file or as an environment variable:

```
export OPENAI_API_KEY=your_api_key_here
git autocommit --use-ai
```

## Configuration

You can customize the behavior by creating a `.git-autocommit` file in your repository. To create a default configuration file, run:

```
git autocommit --setup
```

This will create a configuration file with the following options:

```ini
[autocommit]
# Prefix for commit messages (e.g., "feat:", "fix:", etc.)
prefix = 

# Maximum length of commit messages
max_length = 72

# Whether to use AI for generating commit messages
use_ai = false

# OpenAI API key for AI-powered commit messages
# You can also set this via the OPENAI_API_KEY environment variable
openai_api_key = 

# OpenAI model to use for generating commit messages
openai_model = gpt-3.5-turbo

# Whether to use Conventional Commits format
conventional_commits = false
```

### Conventional Commits

When `conventional_commits` is set to `true`, the plugin will generate commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>
```

Types include: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

## Requirements

- Python 3.6+
- Git
- OpenAI Python package (optional, for AI-powered commit messages)

## License

MIT
