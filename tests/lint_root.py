import os
import sys

# Whitelist of allowed files in the project root
ALLOWED_FILES = {
    'BUILD_ALL',
    'CHANGES',
    'CONTRIBUTORS',
    'LICENSE',
    'Makefile',
    'README.md',
    'TODO.md',
    'NOTES.md',
    'AGENTS.md',
    'RULES.md',
    'run_stack.sh',
    '.gitignore',
    '.git',
    '.agent',
    '__pycache__',
    'backend',
    'bin',
    'client',
    'data',
    'debug',
    'docs',
    'logs',
    'proxy',
    'skills',
    'tests',
}

# Whitelist of allowed extensions (if not in ALLOWED_FILES)
# We generally want NO loose files, but maybe some are okay?
# For now, let's be strict: if it's not in ALLOWED_FILES, it's a violation
# unless it's a directory (which we might want to restrict too, but let's focus on files first)

# Actually, let's just flag widely known "bad" patterns
BAD_EXTENSIONS = {'.py', '.log', '.txt', '.sh'}
IMPORTANT_EXCEPTIONS = {'run_stack.sh'}

def check_root_cleanliness(root_dir='.'):
    violations = []
    print(f"Scanning project root: {os.path.abspath(root_dir)}")

    for item in os.listdir(root_dir):
        if item in ALLOWED_FILES:
            continue
        
        full_path = os.path.join(root_dir, item)
        if os.path.isdir(full_path):
            # Unknown directory - warn but maybe don't fail yet?
            # actually, let's just stick to files for now
            continue

        _, ext = os.path.splitext(item)
        if item not in IMPORTANT_EXCEPTIONS:
            if ext in BAD_EXTENSIONS or item.startswith('test_') or item.startswith('verify_'):
                violations.append(item)

    if violations:
        print("\n[FAIL] Found misplaced files in project root:")
        for v in violations:
            print(f"  - {v}")
        print("\nPlease move these to 'tests/', 'debug/', or 'logs/'.")
        return False
    else:
        print("\n[PASS] Project root is clean.")
        return True

if __name__ == "__main__":
    success = check_root_cleanliness()
    sys.exit(0 if success else 1)
