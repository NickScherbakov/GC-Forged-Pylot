from setuptools import setup, find_packages

setup(
    name="gc-forged-pylot",
    version="0.1.0",
    description="Autonomous 24/7 coding system built on llama.cpp with GitHub Copilot capabilities",
    author="Nick Scherbakov et al.",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "numpy>=1.22.0",
        "torch>=1.12.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)