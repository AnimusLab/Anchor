from setuptools import setup, find_packages
import pathlib

# The directory containing this file
here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="anchor-audit",
    version="2.1.1",  # <--- BUMPED VERSION (PyPI rejects re-uploads of 2.1.0)
    description="The Federated Governance Engine for AI (FINOS/OSFF Compliant)",
    long_description=long_description,  # <--- This fixes the empty description
    long_description_content_type="text/markdown",
    url="https://github.com/Tanishq1030/anchor",  # <--- Link to your Repo
    author="Tanishq",  # <--- Fixed Name
    author_email="your.email@example.com",  # <--- Add your email if you want
    packages=find_packages(),
    install_requires=[
        "click",
        "pyyaml",
        "tree-sitter>=0.22.0",
        "tree-sitter-python",
        "requests"
    ],
    entry_points={
        'console_scripts': [
            'anchor=anchor.cli:cli',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
