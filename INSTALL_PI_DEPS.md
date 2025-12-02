# Installing Dependencies on Raspberry Pi

If you're getting `ModuleNotFoundError: No module named 'yaml'` or similar errors, install the missing dependencies:

## Option 1: Install all dependencies from requirements.txt

```bash
cd /path/to/rasberry-pi-2-project

# If using a virtual environment (recommended)
source venv/bin/activate  # or whatever your venv path is

# Install all dependencies
pip install -r requirements.txt
```

## Option 2: Install just the missing modules

```bash
# If using a virtual environment
source venv/bin/activate

# Install pyyaml (provides yaml module)
pip install pyyaml

# Install requests (needed for laptop_client and serper_client)
pip install requests
```

## Option 3: If you don't have a virtual environment

```bash
cd /path/to/rasberry-pi-2-project

# Install using pip3 (system-wide, not recommended but works)
pip3 install pyyaml requests

# OR install all dependencies
pip3 install -r requirements.txt
```

## Verify installation

After installing, verify the modules are available:

```bash
python3 -c "import yaml; import requests; print('✓ All modules installed successfully')"
```

## Troubleshooting

If you get permission errors:
- Use `pip3 install --user pyyaml requests` to install in user directory
- Or use a virtual environment: `python3 -m venv venv && source venv/bin/activate`

If you get "externally-managed environment" error (common on newer Linux):
- Use a virtual environment (recommended)
- Or use `pip3 install --break-system-packages pyyaml requests` (not recommended)

