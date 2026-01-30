from setuptools import setup, find_packages

setup(
    name="anchor-audit",
    version="2.1.0",
    description="The Federated Governance Engine for AI (FINOS/OSFF Compliant)",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "click",                # CLI Framework
        "pyyaml",               # Policy Parsing
        "tree-sitter>=0.22.0",  # AST Parsing Engine
        "tree-sitter-python",   # Python Grammar
        "requests"              # Cloud Fetch for Constitution
    ],
    entry_points={
        'console_scripts': [
            # This maps the command 'anchor' to the function 'cli' in 'anchor/cli.py'
            'anchor=anchor.cli:cli',
        ],
    },
    python_requires='>=3.8',
)
