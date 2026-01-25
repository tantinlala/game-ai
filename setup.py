"""Setup script for game-ai package."""

from setuptools import setup, find_packages

setup(
    name="game-ai",
    version="0.1.0",
    description="AI-powered game theory builder with Nash equilibrium solver",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/tantinlala/game-ai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pygambit>=16.1.0",
        "google-genai>=1.60.0",
        "textual>=0.50.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-asyncio>=0.21.0",
    ],
    entry_points={
        "console_scripts": [
            "game-ai=game_ai.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
