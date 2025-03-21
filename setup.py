from setuptools import setup, find_packages

setup(
    name="snowfall-alert-system",
    version="1.0.0",
    description="A serverless system for monitoring snowfall at ski resorts",
    author="Dr. Jody-Ann S. Jones",
    author_email="jody@datasensei.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.15.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-mock>=3.5.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "flake8>=3.9.0",
            "pylint>=2.8.0",
            "mypy>=0.812",
            "pdoc3>=0.9.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
