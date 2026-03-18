from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="anchor-audit",
    version="4.0.0",
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
    data_files=[
        ("governance/domains",    ["governance/domains/security.anchor",
                                   "governance/domains/ethics.anchor",
                                   "governance/domains/privacy.anchor",
                                   "governance/domains/alignment.anchor",
                                   "governance/domains/legal.anchor",
                                   "governance/domains/operational.anchor",
                                   "governance/domains/supply_chain.anchor",
                                   "governance/domains/agentic.anchor",
                                   "governance/domains/shared.anchor"]),
        ("governance/frameworks", ["governance/frameworks/FINOS_Framework.anchor",
                                   "governance/frameworks/OWASP_LLM.anchor",
                                   "governance/frameworks/NIST_AI_RMF.anchor",
                                   "governance/frameworks/RBI_Regulations.anchor",
                                   "governance/frameworks/EU_AI_Act.anchor",
                                   "governance/frameworks/SEBI_Regulations.anchor",
                                   "governance/frameworks/CFPB_Regulations.anchor",
                                   "governance/frameworks/FCA_Regulations.anchor",
                                   "governance/frameworks/SEC_Regulations.anchor"]),
        ("governance/examples",   ["governance/examples/constitution.anchor.example",
                                   "governance/examples/policy.anchor.example"]),
    ],
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
        "wrapt",
        "requests",
        "GitPython",
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