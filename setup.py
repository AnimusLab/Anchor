from setuptools import setup, find_packages
import pathlib

# The directory containing this file
here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="anchor-audit",
    version="2.4.14",  # Dynamic Messaging Release - v2.4 Architecture
    description="The Federated Governance Engine for AI (Universal Multi-Language)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tanishq1030/anchor",
    author="Tanishq",
    author_email="tanishqdasari2004@gmail.com",
    packages=find_packages(),
    install_requires=[
        "click",
        "pyyaml",
        "tree-sitter>=0.22.0",
        "tree-sitter-python",
        "tree-sitter-typescript"
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
