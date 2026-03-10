# Configuration Files Location

Configuration files have been moved to `/config` folder for better organization.

## Quick Access

For convenience, create symlinks in the root:

```bash
# From backend/ directory
ln -s config/.env.example .env.example
ln -s config/config.py config.py
```

## File Locations

- **Environment Template:** `config/.env.example`
- **Configuration Module:** `config/config.py`
- **Production Requirements:** `config/requirements-prod.txt`
- **Pipfile:** `config/Pipfile`

## Creating .env File

```bash
# Copy from config folder to root
cp config/.env.example .env

# Edit with your credentials
nano .env
```

#
```
