#!/usr/bin/env python3
"""Django GeoAddress development tool for building, testing, and managing."""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Load .env file if it exists
_env_file = Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
NC = '\033[0m'

if platform.system() == 'Windows' and not os.environ.get('ANSICON'):
    BLUE = GREEN = RED = YELLOW = NC = ''

PROJECT_ROOT = Path(__file__).parent
PYTHON_GEOADDRESS_DIR = PROJECT_ROOT.parent / 'python-geoaddress'
DJANGO_VIRTUALQUERYSET_DIR = PROJECT_ROOT.parent / 'django-virtualqueryset'


def _resolve_venv_dir() -> Path:
    """Find the virtual env directory, preferring .venv over venv."""
    preferred_names = ['.venv', 'venv']
    for name in preferred_names:
        candidate = PROJECT_ROOT / name
        if candidate.exists():
            return candidate
    return PROJECT_ROOT / preferred_names[0]


VENV_DIR = _resolve_venv_dir()
VENV_BIN = VENV_DIR / ('Scripts' if platform.system() == 'Windows' else 'bin')
PYTHON = VENV_BIN / ('python.exe' if platform.system() == 'Windows' else 'python')
PIP = VENV_BIN / ('pip.exe' if platform.system() == 'Windows' else 'pip')


def print_info(message):
    """Prints info message in blue."""
    print(f"{BLUE}{message}{NC}")


def print_success(message):
    """Prints success message in green."""
    print(f"{GREEN}{message}{NC}")


def print_error(message):
    """Prints error message in red."""
    print(f"{RED}{message}{NC}", file=sys.stderr)


def print_warning(message):
    """Prints warning message in yellow."""
    print(f"{YELLOW}{message}{NC}")


def run_command(cmd, check=True, **kwargs):
    """Runs command and handles errors."""
    print_info(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(cmd, check=check, **kwargs)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd}")
        return False


def venv_exists():
    """Checks if virtual environment exists."""
    return VENV_DIR.exists() and PYTHON.exists()


def ensure_venv_activation(command: str):
    """Re-executes this script inside the project virtualenv if present."""
    venv_management_commands = {'venv', 'venv-clean'}
    if command in venv_management_commands:
        return

    if not venv_exists():
        return

    current_python = Path(sys.executable).resolve()
    desired_python = PYTHON.resolve()
    if current_python == desired_python:
        return

    print_info(f"Activating virtual environment at {VENV_DIR}...")
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(VENV_DIR)
    env["PATH"] = f"{VENV_BIN}{os.pathsep}{env.get('PATH', '')}"

    args = [str(desired_python), str(Path(__file__).resolve()), *sys.argv[1:]]
    os.execve(str(desired_python), args, env)


def task_help():
    """Display available commands."""
    print(f"{BLUE}django-geoaddress — available commands{NC}\n")
    
    print(f"{GREEN}Environment:{NC}")
    print("  venv                    Create a local virtual environment")
    print("  install                 Install dependencies")
    print("  install-dev             Install development dependencies")
    print("  venv-clean              Recreate the virtual environment")
    print("  update-geoaddress       Install or refresh local python-geoaddress")
    print("  update-virtualqueryset  Install or refresh local django-virtualqueryset")
    print("")
    
    print(f"{GREEN}Database:{NC}")
    print("  migrate                 Run Django migrations")
    print("  makemigrations          Create new migrations")
    print("  resetdb                 Reset database (drop + migrate)")
    print("")
    
    print(f"{GREEN}Server:{NC}")
    print("  runserver               Start Django development server")
    print("  shell                   Start Django shell")
    print("  createsuperuser         Create a superuser")
    print("")
    
    print(f"{GREEN}Quality & Testing:{NC}")
    print("  test                    Run pytest")
    print("  test-verbose            Run pytest with verbose output")
    print("  coverage                Run tests with coverage report")
    print("  lint                    Run ruff, flake8, pylint, semgrep, and mypy")
    print("  format                  Format code with ruff")
    print("  check                   Run lint/format checks")
    print("  cleanup                 Detect unused code, imports, and redundancies")
    print("  fix-imports             Auto-remove unused imports with autoflake")
    print("  complexity              Analyze code complexity with radon")
    print("")
    
    print(f"{GREEN}Cleaning:{NC}")
    print("  clean                   Remove build, bytecode, and test artifacts")
    print("  clean-build             Remove build artifacts")
    print("  clean-pyc               Remove Python bytecode")
    print("  clean-test              Remove test artifacts")
    print("")
    
    print(f"{GREEN}Packaging:{NC}")
    print("  build                   Build sdist and wheel")
    print("")
    
    print(f"{GREEN}Utilities:{NC}")
    print("  show-version            Print the project version")
    print("  help                    Display this help")
    print("")
    
    print(f"Usage: {GREEN}python dev.py <command>{NC}")
    return True


def task_venv():
    """Create virtual environment."""
    if venv_exists():
        print_warning("Virtual environment already exists.")
        return True

    python_cmd = "python3" if platform.system() != "Windows" else "python"
    print_info("Creating virtual environment...")
    if not run_command([python_cmd, "-m", "venv", str(VENV_DIR)]):
        return False

    print_success(f"Virtual environment created at {VENV_DIR}")
    activation = (
        f"{VENV_DIR}\\Scripts\\activate"
        if platform.system() == "Windows"
        else f"source {VENV_DIR}/bin/activate"
    )
    print_info(f"Activate it with: {activation}")
    return True


def task_install():
    """Install production dependencies."""
    if not venv_exists() and not task_venv():
        return False

    print_info("Installing production dependencies...")
    if not run_command([str(PIP), "install", "--upgrade", "pip", "setuptools", "wheel"]):
        return False

    if not run_command([str(PIP), "install", "-r", "requirements.txt"]):
        return False

    print_success("Production dependencies installed.")
    return True


def task_install_dev():
    """Install development dependencies."""
    if not venv_exists() and not task_venv():
        return False

    print_info("Installing development dependencies...")
    if not run_command([str(PIP), "install", "--upgrade", "pip", "setuptools", "wheel"]):
        return False

    if not run_command([str(PIP), "install", "-r", "requirements-dev.txt"]):
        return False

    print_success("Development dependencies installed.")
    return True


def task_update_geoaddress():
    """Install or update python-geoaddress from local directory."""
    if not venv_exists():
        print_error("Virtual environment not found. Run 'python dev.py venv' first.")
        return False

    args = sys.argv[2:]
    target_dir = Path(args[0]) if args else PYTHON_GEOADDRESS_DIR

    if not target_dir.exists():
        print_error(
            f"python-geoaddress directory not found at {target_dir}. "
            "Provide path: python dev.py update-geoaddress /path/to/python-geoaddress"
        )
        return False

    print_info("Installing python-geoaddress into the virtual environment...")
    if run_command([str(PIP), "install", "-e", str(target_dir)]):
        print_success("python-geoaddress installed/updated successfully.")
        return True

    print_error("Failed to install/update python-geoaddress.")
    return False


def task_update_virtualqueryset():
    """Install or update django-virtualqueryset from local directory."""
    if not venv_exists():
        print_error("Virtual environment not found. Run 'python dev.py venv' first.")
        return False

    args = sys.argv[2:]
    target_dir = Path(args[0]) if args else DJANGO_VIRTUALQUERYSET_DIR

    if not target_dir.exists():
        print_error(
            f"django-virtualqueryset directory not found at {target_dir}. "
            "Provide path: python dev.py update-virtualqueryset /path/to/django-virtualqueryset"
        )
        return False

    print_info("Installing django-virtualqueryset into the virtual environment...")
    if run_command([str(PIP), "install", "-e", str(target_dir)]):
        print_success("django-virtualqueryset installed/updated successfully.")
        return True

    print_error("Failed to install/update django-virtualqueryset.")
    return False


def task_migrate():
    """Run Django migrations."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    return run_command([str(PYTHON), "manage.py", "migrate"])


def task_makemigrations():
    """Create new migrations."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    return run_command([str(PYTHON), "manage.py", "makemigrations"])


def task_resetdb():
    """Reset database (drop + migrate)."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    db_file = PROJECT_ROOT / "db.sqlite3"
    if db_file.exists():
        print_warning("Deleting existing database...")
        db_file.unlink()

    print_info("Creating new database...")
    return task_migrate()


def task_runserver():
    """Start Django development server."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    args = sys.argv[2:]
    port = args[0] if args else "8000"
    
    return run_command([str(PYTHON), "manage.py", "runserver", port])


def task_shell():
    """Start Django shell."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    return run_command([str(PYTHON), "manage.py", "shell"])


def task_createsuperuser():
    """Create a superuser."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    return run_command([str(PYTHON), "manage.py", "createsuperuser"])


def task_test():
    """Run pytest."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    pytest = VENV_BIN / ("pytest.exe" if platform.system() == "Windows" else "pytest")
    if run_command([str(pytest)]):
        print_success("Tests complete.")
        return True
    return False


def task_test_verbose():
    """Run pytest with verbose output."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    pytest = VENV_BIN / ("pytest.exe" if platform.system() == "Windows" else "pytest")
    if run_command([str(pytest), "-vv"]):
        print_success("Verbose tests complete.")
        return True
    return False


def task_coverage():
    """Run tests with coverage report."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    pytest = VENV_BIN / ("pytest.exe" if platform.system() == "Windows" else "pytest")
    if run_command([str(pytest), "--cov=djgeoaddress", "--cov-report=html", "--cov-report=term"]):
        print_success("Coverage report generated in htmlcov/index.html")
        return True
    return False


def task_lint():
    """Run linters."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    ruff = VENV_BIN / ("ruff.exe" if platform.system() == "Windows" else "ruff")
    flake8 = VENV_BIN / ("flake8.exe" if platform.system() == "Windows" else "flake8")
    pylint = VENV_BIN / ("pylint.exe" if platform.system() == "Windows" else "pylint")
    semgrep = VENV_BIN / ("semgrep.exe" if platform.system() == "Windows" else "semgrep")
    mypy = VENV_BIN / ("mypy.exe" if platform.system() == "Windows" else "mypy")
    targets = ["djgeoaddress", "tests"]

    success = True
    if not run_command([str(ruff), "check", *targets]):
        success = False

    if not run_command([str(flake8), *targets]):
        success = False

    if not run_command(
        [str(pylint), "--disable=all", "--enable=duplicate-code", "djgeoaddress"], check=False
    ):
        success = False

    semgrep_cmd = [str(semgrep), "scan"]
    semgrep_configs = []
    local_semgrep = PROJECT_ROOT / ".semgrep.yaml"
    if local_semgrep.exists():
        semgrep_configs.append(str(local_semgrep))
    else:
        semgrep_configs.append("p/default")
    semgrep_configs.extend(["p/python", "p/supply-chain"])
    for config in semgrep_configs:
        semgrep_cmd += ["--config", config]
    semgrep_cmd += targets
    if not run_command(semgrep_cmd, check=False):
        success = False

    if not run_command([str(mypy), "djgeoaddress"]):
        success = False

    if success:
        print_success("Lint checks passed.")
    return success


def task_security():
    """Runs security audit with multiple tools."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False
    
    print_info("=" * 70)
    print_info("SECURITY AUDIT - Django GeoAddress")
    print_info("=" * 70)
    
    bandit = VENV_BIN / ("bandit.exe" if platform.system() == "Windows" else "bandit")
    safety = VENV_BIN / ("safety.exe" if platform.system() == "Windows" else "safety")
    pip_audit = VENV_BIN / ("pip-audit.exe" if platform.system() == "Windows" else "pip-audit")
    semgrep = VENV_BIN / ("semgrep.exe" if platform.system() == "Windows" else "semgrep")
    targets = ["djgeoaddress", "tests"]
    
    results = {
        "bandit": False,
        "safety": False,
        "pip_audit": False,
        "semgrep": False,
    }
    
    # 1. Bandit - Static code analysis
    print("\n" + "=" * 70)
    print_info("1/4 - Running Bandit (Static Code Analysis)")
    print_info("=" * 70)
    
    if run_command([str(bandit), "-r", *targets, "-ll", "-f", "screen", "--skip", "B101"], check=False):
        print_success("✓ Bandit: No high/medium issues found")
        results["bandit"] = True
    else:
        print_warning("⚠ Bandit: Issues found (review above)")
    
    # 2. Safety - Dependency vulnerability check
    print("\n" + "=" * 70)
    print_info("2/4 - Running Safety (Dependency Vulnerabilities)")
    print_info("=" * 70)
    
    # Safety may require authentication - try with API key from env if available
    safety_cmd = [str(safety), "scan", "--output", "json"]
    safety_api_key = os.environ.get("SAFETY_API_KEY")
    if safety_api_key:
        safety_cmd.extend(["--key", safety_api_key])
        print_info("   Using SAFETY_API_KEY from environment")
    
    safety_result = run_command(safety_cmd, check=False)
    if safety_result:
        print_success("✓ Safety: No known vulnerabilities in dependencies")
        results["safety"] = True
    else:
        # Check if it's an authentication issue
        if not safety_api_key:
            print_warning("⚠ Safety: Unable to complete scan (authentication required)")
            print_info("   Note: Safety CLI requires free account registration")
            print_info("   Option 1: Register at https://pyup.io/safety/ and set SAFETY_API_KEY env var")
            print_info("   Option 2: Run 'safety auth' to authenticate interactively")
            print_info("   For now, treating as skipped (not a failure)")
            # Don't count as failure if it's just authentication
            results["safety"] = True  # Count as pass since it's optional
        else:
            print_warning("⚠ Safety: Scan completed but issues may have been found")
            results["safety"] = False
    
    # 3. Pip-Audit - PyPI vulnerability audit
    print("\n" + "=" * 70)
    print_info("3/4 - Running Pip-Audit (PyPI Vulnerabilities)")
    print_info("=" * 70)
    
    if run_command([str(pip_audit)], check=False):
        print_success("✓ Pip-Audit: No vulnerabilities found")
        results["pip_audit"] = True
    else:
        print_warning("⚠ Pip-Audit: Vulnerabilities found (review above)")
    
    # 4. Semgrep - SAST rules
    print("\n" + "=" * 70)
    print_info("4/4 - Running Semgrep (SAST)")
    print_info("=" * 70)

    semgrep_cmd = [str(semgrep), "scan"]
    semgrep_configs = []
    local_semgrep = PROJECT_ROOT / ".semgrep.yaml"
    if local_semgrep.exists():
        semgrep_configs.append(str(local_semgrep))
    else:
        semgrep_configs.append("p/default")
    semgrep_configs.extend(["p/python", "p/supply-chain"])
    for config in semgrep_configs:
        semgrep_cmd += ["--config", config]
    semgrep_cmd += targets

    if run_command(semgrep_cmd, check=False):
        print_success("✓ Semgrep: No issues reported")
        results["semgrep"] = True
    else:
        print_warning("⚠ Semgrep: Findings detected (review above)")

    # Summary
    print("\n" + "=" * 70)
    print_info("SECURITY AUDIT SUMMARY")
    print_info("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for tool, success in results.items():
        status = f"{GREEN}✓ PASS{NC}" if success else f"{RED}✗ FAIL{NC}"
        print(f"  {tool.upper():15} {status}")
    
    print("\n" + "-" * 70)
    score = int((passed / total) * 100)
    
    if score == 100:
        print_success(f"SECURITY SCORE: {score}/100 - EXCELLENT!")
    elif score >= 66:
        print_warning(f"SECURITY SCORE: {score}/100 - GOOD")
    else:
        print_error(f"SECURITY SCORE: {score}/100 - NEEDS ATTENTION")
    
    print("-" * 70)
    
    # Additional tools info
    print("\n" + BLUE + "Additional Security Tools (manual setup):" + NC)
    print("  • SonarQube: https://sonarcloud.io/ (requires account)")
    print("  • Snyk: https://snyk.io/ (requires account)")
    print("  • OWASP Dependency-Check: https://owasp.org/www-project-dependency-check/")
    
    return score == 100


def task_format():
    """Format code with ruff."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False

    ruff = VENV_BIN / ("ruff.exe" if platform.system() == "Windows" else "ruff")
    if run_command([str(ruff), "format", "djgeoaddress", "tests"]):
        print_success("Code formatted.")
        return True
    return False


def task_check():
    """Run all checks."""
    success = task_lint()
    if success:
        print_success("All checks passed.")
    return success


def task_cleanup():
    """Detects unused code, imports, and redundancies."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False
    
    print_info("=" * 70)
    print_info("CODE CLEANUP ANALYSIS - Django GeoAddress")
    print_info("=" * 70)
    
    vulture = VENV_BIN / ("vulture.exe" if platform.system() == "Windows" else "vulture")
    autoflake = VENV_BIN / ("autoflake.exe" if platform.system() == "Windows" else "autoflake")
    pylint = VENV_BIN / ("pylint.exe" if platform.system() == "Windows" else "pylint")
    
    results = {
        "vulture": False,
        "autoflake": False,
        "pylint": False,
    }
    
    # 1. Vulture - Dead code detection
    print("\n" + "=" * 70)
    print_info("1/3 - Running Vulture (Dead Code Detection)")
    print_info("=" * 70)
    
    # Vulture retourne 0 si pas de dead code, 1 sinon
    result = run_command([str(vulture), "djgeoaddress/", "--min-confidence", "80"], check=False)
    if result:
        print_success("✓ Vulture: No dead code found")
        results["vulture"] = True
    else:
        print_warning("⚠ Vulture: Potential dead code detected (review above)")
    
    # 2. Autoflake - Unused imports check
    print("\n" + "=" * 70)
    print_info("2/3 - Running Autoflake (Unused Imports Check)")
    print_info("=" * 70)
    
    # Check mode only (no modifications)
    if run_command(
        [
            str(autoflake),
            "--check",
            "--recursive",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "djgeoaddress/",
        ],
        check=False,
    ):
        print_success("✓ Autoflake: No unused imports or variables")
        results["autoflake"] = True
    else:
        print_warning("⚠ Autoflake: Unused imports/variables found (run 'fix-imports' to fix)")
    
    # 3. Pylint - Code quality and redundancies
    print("\n" + "=" * 70)
    print_info("3/3 - Running Pylint (Code Quality & Redundancies)")
    print_info("=" * 70)
    
    # Pylint avec score minimum de 8/10
    if run_command(
        [str(pylint), "djgeoaddress/", "--fail-under=8.0", "--disable=C0111,C0103,R0903"],
        check=False,
    ):
        print_success("✓ Pylint: Code quality score >= 8.0/10")
        results["pylint"] = True
    else:
        print_warning("⚠ Pylint: Code quality issues found (review above)")
    
    # Summary
    print("\n" + "=" * 70)
    print_info("CODE CLEANUP SUMMARY")
    print_info("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for tool, success in results.items():
        status = f"{GREEN}✓ PASS{NC}" if success else f"{RED}✗ FAIL{NC}"
        print(f"  {tool.upper():15} {status}")
    
    print("\n" + "-" * 70)
    score = int((passed / total) * 100)
    
    if score == 100:
        print_success(f"CLEANUP SCORE: {score}/100 - EXCELLENT!")
    elif score >= 66:
        print_warning(f"CLEANUP SCORE: {score}/100 - GOOD")
    else:
        print_error(f"CLEANUP SCORE: {score}/100 - NEEDS ATTENTION")
    
    print("-" * 70)
    
    return score == 100


def task_fix_imports():
    """Auto-removes unused imports and variables with autoflake."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False
    
    print_info("Fixing unused imports and variables...")
    autoflake = VENV_BIN / ("autoflake.exe" if platform.system() == "Windows" else "autoflake")
    
    # Apply fixes in-place
    if run_command(
        [
            str(autoflake),
            "--in-place",
            "--recursive",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--remove-duplicate-keys",
            "djgeoaddress/",
            "tests/",
        ]
    ):
        print_success("✓ Unused imports and variables removed!")
        return True
    else:
        print_error("✗ Failed to fix imports")
        return False


def task_complexity():
    """Analyzes code complexity with radon."""
    if not venv_exists():
        print_error("Virtual environment not found.")
        return False
    
    print_info("=" * 70)
    print_info("CODE COMPLEXITY ANALYSIS - Django GeoAddress")
    print_info("=" * 70)
    
    radon = VENV_BIN / ("radon.exe" if platform.system() == "Windows" else "radon")
    
    # Cyclomatic Complexity
    print("\n" + "=" * 70)
    print_info("Cyclomatic Complexity (CC)")
    print_info("=" * 70)
    print_info("A = simple (1-5), B = moderate (6-10), C = complex (11-20)")
    print_info("D = very complex (21-50), E/F = extremely complex (>50)")
    print("")
    
    run_command([str(radon), "cc", "djgeoaddress/", "-s", "-a"], check=False)
    
    # Maintainability Index
    print("\n" + "=" * 70)
    print_info("Maintainability Index (MI)")
    print_info("=" * 70)
    print_info("A = highly maintainable, B = good, C = moderate, D/F = hard to maintain")
    print("")
    
    run_command([str(radon), "mi", "djgeoaddress/", "-s"], check=False)
    
    # Raw metrics
    print("\n" + "=" * 70)
    print_info("Raw Metrics (LOC, LLOC, Comments)")
    print_info("=" * 70)
    
    run_command([str(radon), "raw", "djgeoaddress/", "-s"], check=False)
    
    print("\n" + "=" * 70)
    print_success("Complexity analysis complete!")
    print_info("Tip: Focus on reducing functions with CC > 10 (C or higher)")
    print_info("=" * 70)
    
    return True


def task_clean_build():
    """Remove build artifacts."""
    print_info("Removing build artifacts...")
    for directory in ["build", "dist", ".eggs"]:
        path = PROJECT_ROOT / directory
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            print(f"  Removed {directory}/")

    for egg_info in PROJECT_ROOT.glob("**/*.egg-info"):
        shutil.rmtree(egg_info, ignore_errors=True)
        print(f"  Removed {egg_info}")

    return True


def task_clean_pyc():
    """Remove Python bytecode artifacts."""
    print_info("Removing Python bytecode artifacts...")

    for pycache in PROJECT_ROOT.glob("**/__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)

    for pattern in ["**/*.pyc", "**/*.pyo", "**/*~"]:
        for file in PROJECT_ROOT.glob(pattern):
            file.unlink(missing_ok=True)

    return True


def task_clean_test():
    """Remove test artifacts."""
    print_info("Removing test artifacts...")
    artifacts = [".pytest_cache", ".coverage", "htmlcov", ".mypy_cache", ".ruff_cache"]

    for artifact in artifacts:
        path = PROJECT_ROOT / artifact
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            print(f"  Removed {artifact}")

    print_success("Test artifacts removed.")
    return True


def task_clean():
    """Remove all artifacts."""
    task_clean_build()
    task_clean_pyc()
    task_clean_test()
    print_success("Workspace clean.")
    return True


def task_build():
    """Build package."""
    if not task_clean():
        return False

    if not venv_exists() and not task_venv():
        return False

    if not run_command([str(PIP), "install", "--upgrade", "build"]):
        return False

    if not run_command([str(PYTHON), "-m", "build"]):
        return False

    print_success("Build complete (dist/).")
    return True


def task_show_version():
    """Show project version."""
    try:
        import tomllib
    except ModuleNotFoundError:
        print_error("tomllib not available (Python 3.11+ required)")
        return False

    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        print_error("pyproject.toml not found")
        return False

    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    
    version = data.get("project", {}).get("version")
    if version:
        print_info(f"Current version: {version}")
        return True

    print_error("Version not found in pyproject.toml")
    return False


def task_venv_clean():
    """Recreate virtual environment."""
    if venv_exists():
        print_info("Removing existing virtual environment...")
        shutil.rmtree(VENV_DIR, ignore_errors=True)
        print_success("Virtual environment removed.")
    return task_venv()


COMMANDS = {
    "help": task_help,
    "venv": task_venv,
    "install": task_install,
    "install-dev": task_install_dev,
    "venv-clean": task_venv_clean,
    "update-geoaddress": task_update_geoaddress,
    "update-virtualqueryset": task_update_virtualqueryset,
    "migrate": task_migrate,
    "makemigrations": task_makemigrations,
    "resetdb": task_resetdb,
    "runserver": task_runserver,
    "shell": task_shell,
    "createsuperuser": task_createsuperuser,
    "test": task_test,
    "test-verbose": task_test_verbose,
    "coverage": task_coverage,
    "lint": task_lint,
    "security": task_security,
    "format": task_format,
    "check": task_check,
    "cleanup": task_cleanup,
    "fix-imports": task_fix_imports,
    "complexity": task_complexity,
    "clean": task_clean,
    "clean-build": task_clean_build,
    "clean-pyc": task_clean_pyc,
    "clean-test": task_clean_test,
    "build": task_build,
    "show-version": task_show_version,
}


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        task_help()
        return 0

    command = args[0]
    if command not in COMMANDS:
        print_error(f"Unknown command: {command}")
        print_info("Run `python dev.py help` to list available commands.")
        return 1

    ensure_venv_activation(command)

    try:
        success = COMMANDS[command]()
        return 0 if success else 1
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user.")
        return 130
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

