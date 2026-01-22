"""Setup configuration for Anchor."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(
    encoding="utf-8") if readme_file.exists() else ""

setup(
    name="anchor-audit",
    version="0.1.0",
    description="Deterministic intent auditor for codebases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Anchor Contributors",
    url="https://github.com/yourusername/anchor",
    packages=find_packages(),
    install_requires=[
        "gitpython>=3.1.0",
        "sentence-transformers>=2.2.0",
        "scikit-learn>=1.3.0",
        "click>=8.1.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "anchor=anchor.cli:cli",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
