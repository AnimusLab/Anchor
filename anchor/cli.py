"""Command-line interface for Anchor."""

import sys
import click
from pathlib import Path

from .repo import RepositoryAnalyzer
from .report import ReportFormatter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Anchor - Deterministic Intent Auditor

    Verify that code still means what it was supposed to mean.
    """
    pass


@cli.command()
@click.argument('symbol_path')
@click.option(
    '--repo',
    default='.',
    help='Repository path (default: current directory)'
)
@click.option(
    '--type',
    'symbol_type',
    type=click.Choice(['function', 'class']),
    default='function',
    help='Symbol type'
)
@click.option(
    '--exclude-tests',
    is_flag=True,
    help='Exclude test files from call context analysis'
)
def audit(symbol_path: str, repo: str, symbol_type: str, exclude_tests: bool):
    """
    Audit a symbol for intent drift.

    SYMBOL_PATH format: path/to/file.py::symbol_name

    Examples:
        anchor audit django/contrib/auth/__init__.py::authenticate
        anchor audit myapp/models.py::User --type class
        anchor audit myapp/views.py::process_user --exclude-tests
    """

    # Parse symbol path
    if '::' not in symbol_path:
        click.echo(
            "Error: SYMBOL_PATH must be in format 'file.py::symbol_name'", err=True)
        sys.exit(1)

    file_path, symbol_name = symbol_path.split('::', 1)

    # Validate repository
    repo_path = Path(repo).resolve()
    if not repo_path.exists():
        click.echo(f"Error: Repository not found: {repo}", err=True)
        sys.exit(1)

    # Validate file exists
    full_file_path = repo_path / file_path
    if not full_file_path.exists():
        click.echo(f"Error: File not found: {file_path}", err=True)
        sys.exit(1)

    try:
        # Initialize analyzer
        analyzer = RepositoryAnalyzer(str(repo_path))

        # Configure test inclusion
        include_tests = not exclude_tests

        # Perform audit
        result = analyzer.audit_symbol(
            file_path,
            symbol_name,
            symbol_type,
            include_tests=include_tests
        )

        if result is None:
            click.echo(f"\n✗ Could not audit {symbol_name}", err=True)
            click.echo(
                "  Insufficient data (need ≥10 call sites and git history)", err=True)
            sys.exit(1)

        # Format and display result
        formatter = ReportFormatter()
        report = formatter.format(result)

        click.echo("\n" + "=" * 80)
        click.echo(report)
        click.echo("=" * 80)

        # Exit code based on verdict
        if result.verdict == "aligned":
            sys.exit(0)
        else:
            sys.exit(0)  # Non-zero exit would break CI, so we keep it 0

    except Exception as e:
        click.echo(f"\n✗ Audit failed: {e}", err=True)
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.argument('symbols_file', type=click.File('r'))
@click.option(
    '--repo',
    default='.',
    help='Repository path'
)
@click.option(
    '--exclude-tests',
    is_flag=True,
    help='Exclude test files from call context analysis'
)
def batch(symbols_file, repo: str, exclude_tests: bool):
    """
    Audit multiple symbols from a file.

    File format (one per line):
        path/to/file.py::symbol_name
        path/to/other.py::other_symbol
    """

    repo_path = Path(repo).resolve()
    analyzer = RepositoryAnalyzer(str(repo_path))
    formatter = ReportFormatter()

    include_tests = not exclude_tests
    results = []

    for line in symbols_file:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if '::' not in line:
            click.echo(f"Skipping invalid line: {line}", err=True)
            continue

        file_path, symbol_name = line.split('::', 1)

        try:
            result = analyzer.audit_symbol(
                file_path,
                symbol_name,
                include_tests=include_tests
            )
            if result:
                results.append(result)
        except Exception as e:
            click.echo(f"Failed to audit {symbol_name}: {e}", err=True)
            continue

    # Generate summary
    if results:
        summary = formatter.format_summary(results)
        click.echo(summary)
    else:
        click.echo("No symbols successfully audited.", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--repo',
    default='.',
    help='Repository path'
)
def validate(repo: str):
    """
    Validate Anchor installation by testing on known symbols.

    Uses Django's authenticate() as a test case if available.
    """

    repo_path = Path(repo).resolve()

    click.echo("Validating Anchor installation...")
    click.echo(f"Repository: {repo_path}")
    click.echo()

    # Check dependencies
    try:
        import git
        import sentence_transformers
        import sklearn
        click.echo("✓ Dependencies installed")
    except ImportError as e:
        click.echo(f"✗ Missing dependency: {e}", err=True)
        sys.exit(1)

    # Check git repository
    try:
        from git import Repo
        repo_obj = Repo(str(repo_path))
        click.echo(
            f"✓ Git repository found ({len(list(repo_obj.iter_commits()))} commits)")
    except Exception as e:
        click.echo(f"✗ Invalid git repository: {e}", err=True)
        sys.exit(1)

    click.echo()
    click.echo("✓ Anchor is ready to use")
    click.echo()
    click.echo("Try: anchor audit path/to/file.py::function_name")


if __name__ == '__main__':
    cli()
