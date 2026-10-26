"""Check the Git index without displaying possible secret values."""
import argparse
from pathlib import PurePosixPath
import re
import subprocess
import sys


ROOT_FILES = {
    '.gitignore', '.gitattributes', '.editorconfig', 'README.md',
    'CONTRIBUTING.md', 'SECURITY.md', 'NOTICE.md', 'AGENTS.md',
}
DOCS = {
    'README.md', 'architecture.md', 'development.md', 'roadmap.md',
    'repository-policy.md', 'publication-audit.md',
}
CONFIGS = {'DefaultEngine.ini', 'DefaultGame.ini', 'DefaultInput.ini'}
BLOCKED_PARTS = {
    'output', 'tmp', 'inputs', 'research', 'content', 'media', 'saved',
    'intermediate', 'binaries', 'deriveddatacache', 'node_modules',
    '__pycache__', '.venv', '.ssh', '.aws', '.azure',
}
PATTERNS = {
    'private key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'GitHub token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'cloud access key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'model access token': re.compile(rb'\bhf_[A-Za-z0-9]{30,}\b'),
    'credential in URL': re.compile(rb'https?://[^\s/@:]+:[^\s/@]+@'),
}
TEXT_SUFFIXES = {'.py', '.sh', '.md', '.txt', '.yml', '.yaml', '.json',
                 '.cpp', '.h', '.cs', '.ini', '.uproject'}


def git(*args):
    return subprocess.check_output(['git', *args])


def allowed(path):
    p = PurePosixPath(path)
    if any(part.lower() in BLOCKED_PARTS for part in p.parts):
        return False
    name = p.name.lower()
    if (name.startswith('.env') or '.local.' in name
            or 'credentials' in name or 'secrets' in name):
        return False
    if path in ROOT_FILES or path == '.github/CODEOWNERS':
        return True
    if len(p.parts) == 2 and p.parts[0] == 'docs':
        return p.name in DOCS
    if path == 'ue5/GSVSLAM/GSVSLAM.uproject':
        return True
    if len(p.parts) == 4 and p.parts[:3] == ('ue5', 'GSVSLAM', 'Config'):
        return p.name in CONFIGS
    prefixes = ('controller/', 'tests/', 'scripts/', 'requirements/',
                '.github/', 'ue5/tools/', 'ue5/GSVSLAM/Source/')
    return path.startswith(prefixes) and p.suffix in TEXT_SUFFIXES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged-only', action='store_true')
    args = parser.parse_args()
    root = git('rev-parse', '--show-toplevel').decode().strip()
    import os
    os.chdir(root)
    command = ('diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z') if args.staged_only else ('ls-files', '--cached', '-z')
    paths = sorted(set(git(*command).decode('utf-8').strip('\0').split('\0')) - {''})
    problems = []
    for path in paths:
        if not allowed(path):
            problems.append((path, 'path is outside publication policy'))
        record = git('ls-files', '--stage', '--', path).decode()
        if not record.startswith(('100644 ', '100755 ')):
            problems.append((path, 'only regular files may be published'))
            continue
        data = git('show', ':' + path)
        if len(data) > 1024 * 1024:
            problems.append((path, 'file exceeds 1 MiB source-only limit'))
        if b'\0' in data:
            problems.append((path, 'binary content is not allowed'))
        for label, pattern in PATTERNS.items():
            if pattern.search(data):
                problems.append((path, 'possible ' + label))
    for path, reason in problems:
        print(f'BLOCKED: {path}: {reason}', file=sys.stderr)
    print(f'Checked {len(paths)} indexed files; {len(problems)} problem(s).')
    return bool(problems)


if __name__ == '__main__':
    raise SystemExit(main())
