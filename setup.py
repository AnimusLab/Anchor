from setuptools import setup, find_packages
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="anchor-audit",
    version="2.0.0",  # <--- MAJOR VERSION BUMP
    description="The Semantic Firewall for AI Code Generation",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Tanishq1030/anchor",
    author="Tanishq Dasari",
    author_email="tanishqdasari2004@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Quality Assurance",
        "Intended Audience :: Developers",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "GitPython>=3.1.0",           # Keep for v1 (Architecture Drift)
        "tree-sitter>=0.25.0",        # NEW for v2 (AST Parsing)
        "tree-sitter-python>=0.25.0",  # NEW for v2 (Python Grammar)
        "PyYAML",                     # NEW for v2 (Config Parsing)
    ],
    entry_points={
        "console_scripts": [
            # Keeps 'anchor' command working (v1)
            "anchor=anchor.cli:main",
            "anchor-v2=anchor.cli_v2:main",  # Adds 'anchor-v2' command (v2)
        ],
    },
    python_requires=">=3.8",
)
