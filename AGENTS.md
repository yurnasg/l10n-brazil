# Agent Runbook: Execution, Testing & Debugging (`l10n-brazil`)

This document contains operational instructions, CLI commands, and debugging procedures for development on this repository.

---

## 1. Quality & Linting Commands (Fast Execution with `uv`)

### A. Python Linter (Ruff / PEP 8 / Flake8 / Pylint rules)
```bash
# Check code for syntax errors, PEP 8, and OCA rules with Ruff (Fast)
uvx ruff check <module_name>

# Auto-fix linting issues where possible
uvx ruff check --fix <module_name>

# Run Pylint with the official OCA pylint-odoo plugin
uvx --with pylint-odoo pylint --load-plugins=pylint_odoo <module_name>
```

### B. Code Formatter (Black / isort standard - 88 chars)
```bash
# Check formatting without modifying files
uvx ruff format --check <module_name>

# Apply formatting to module
uvx ruff format <module_name>
```

### C. Pre-commit Hooks (OCA Standard Suite)
```bash
# Run pre-commit hooks on specific files
uvx pre-commit run --files <file_paths>

# Run pre-commit on all files in a module
uvx pre-commit run --files <module_name>/**/*
```

---

## 2. Docker Execution & Unit Testing

### A. Run Automated Unit Tests (Headless / Isolated)
```bash
# Run unit tests for a specific module against an isolated test database
docker compose run --rm web odoo -i <module_name> --test-tags=<module_name> -d test_<module_name>_db --test-enable --stop-after-init
```

*Examples:*
```bash
# Test l10n_br_hr
docker compose run --rm web odoo -i l10n_br_hr --test-tags=l10n_br_hr -d test_l10n_br_hr_db --test-enable --stop-after-init

# Test l10n_br_base
docker compose run --rm web odoo -i l10n_br_base --test-tags=l10n_br_base -d test_l10n_br_base_db --test-enable --stop-after-init
```

### B. Build / Rebuild Docker Environment
```bash
# Rebuild the Odoo 18 image when Dockerfile or dependencies change
docker compose build

# Rebuild without cache
docker compose build --no-cache
```

### C. Web Server Execution (Interactive / UI)
```bash
# Start Odoo web server and PostgreSQL
docker compose up

# Start in background (detached mode)
docker compose up -d

# Stop and remove running containers
docker compose down

# Stop containers and remove database volume (clean reset)
docker compose down -v
```
- **Web UI**: `http://localhost:8069`
- **Default Database Credentials**: Host `db`, User `odoo`, Password `odoo`

---

## 3. Container Debugging & Inspection

### A. Access Container Shell
```bash
# Open bash shell inside Odoo web container
docker compose run --rm web /bin/bash

# Open bash shell inside a running web container
docker compose exec web /bin/bash
```

### B. Odoo Interactive Shell (REPL)
```bash
# Open Odoo Python shell for interactive debugging with ORM
docker compose run --rm web odoo shell -d <database_name>
```

### C. Container Logs
```bash
# Follow logs in real-time
docker compose logs -f web

# View database logs
docker compose logs -f db
```

### D. Direct PostgreSQL Access
```bash
# Open psql terminal on PostgreSQL container
docker compose exec db psql -U odoo -d postgres
```

---

## 4. OCA Maintainer Tools & Multi-Version Workflow

### A. Porting Modules & Commits Across Odoo Versions (`oca-port`)
```bash
# Port an addon from an older branch (e.g. 16.0/17.0) to a target branch (18.0)
uvx oca-port origin/16.0 origin/18.0 <module_name>

# Port with specific destination branch and run pre-commit automatically
uvx oca-port origin/16.0 origin/18.0 <module_name> --destination origin/18.0-<module_name>-port --pre-commit
```

### B. OCA Documentation Generator (`oca-gen-addon-readme`)
```bash
# Generate/update README.rst from fragments in readme/ directory for a module
uvx --from git+https://github.com/OCA/maintainer-tools oca-gen-addon-readme --org-name OCA --repo-name l10n-brazil --branch 18.0 --addon-dir <module_name>

# Generate README.rst for all addons in the repository
uvx --from git+https://github.com/OCA/maintainer-tools oca-gen-addon-readme --org-name OCA --repo-name l10n-brazil --branch 18.0 --addons-dir .

# Update main repository README table with all modules
uvx --from git+https://github.com/OCA/maintainer-tools oca-gen-addons-table --org-name OCA --repo-name l10n-brazil --branch 18.0 --addons-dir .
```

### C. Multi-Version Git Aggregator (`git-aggregator`)
```bash
# Aggregate and sync branches from multiple repositories defined in repos.yaml
uvx git-aggregator -c repos.yaml
```

### D. Git Worktrees (Simultaneous Multi-Version Development)
```bash
# Create a parallel working directory for Odoo 16.0 or 17.0 without re-cloning
git worktree add ../l10n-brazil-16.0 16.0
git worktree add ../l10n-brazil-17.0 17.0

# List active worktrees
git worktree list

# Remove worktree when done
git worktree remove ../l10n-brazil-16.0
```
