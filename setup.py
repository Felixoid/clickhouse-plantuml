#!/usr/bin/env python

from setuptools import setup, find_packages  # type: ignore

pkg_name = "clickhouse_plantuml"

with open("{}/version.py".format(pkg_name)) as f:
    for line in f:
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            __version__ = line.split(delim)[1]
            break

with open("README.md") as f:
    long_description = f.read()

setup(
    name=pkg_name,
    version=__version__,
    description="Generates PlantUML diagrams for clickhouse databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/Felixoid/clickhouse-plantuml",
    author="Mikhail f. Shiryaev",
    author_email="mr.felixoid@gmail.com",
    license="License :: OSI Approved :: Apache Software License",
    install_requires=["clickhouse-driver"],
    extras_require={
        "tests": ["pytest", "pytest-docker", "flake8"],
        "black": ["black", "pytest-black"],
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires="~=3.5",
    data_files=[("", ["LICENSE", "docs/example.png"])],
    entry_points={
        "console_scripts": [
            "clickhouse-plantuml = clickhouse_plantuml.__main__:main"
        ]
    },
)
