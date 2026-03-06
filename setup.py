from setuptools import setup, find_packages
import pathlib

# The directory containing this file
here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="anchor-audit",
    version="3.0.0-alpha",  # V3: Interceptor SDK + Diamond Cage Behavioral Verification
    description="The Federated Governance Engine for AI (Universal Multi-Language)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tanishq1030/anchor",
    author="Tanishq",
    author_email="tanishqdasari2004@gmail.com",
    packages=find_packages(),
    package_data={
        "anchor": [
            "core/resources/*.example",
            "core/resources/*.png",
        ],
    },
    install_requires=[
        "click",
        "pyyaml",
        "tree-sitter>=0.22.0",
        "tree-sitter-python",
        "tree-sitter-typescript",
        "tree-sitter-go",
        "tree-sitter-java",
        "tree-sitter-rust",
        "pydantic-settings>=2.0.0",
        "wrapt",           # SDK-level interceptor patches (Layer 1)
        "requests",        # HTTP backstop (Layer 2)
    ],
    extras_require={
        "dev": ["pytest", "black", "mypy"],
        "all": ["openai", "anthropic", "google-generativeai", "langchain",
                "ollama", "groq", "cohere", "mistralai", "transformers", "httpx"],
    },
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
