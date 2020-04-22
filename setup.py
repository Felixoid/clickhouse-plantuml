from setuptools import setup, find_packages  # type: ignore

try:
    from clickhouse_plantuml import VERSION
except ModuleNotFoundError:
    # Dirty hack to allow `pip install .` in virtualenv
    VERSION = (0, 1)


with open('README.md') as f:
    long_description = f.read()

setup(
    name='clickhouse-plantuml',
    version='.'.join(str(d) for d in VERSION),
    description='Generates PlantUML diagrams for clickhouse databases',
    url='http://github.com/Felixoid/clickhouse-plantuml',
    author='Mikhail f. Shiryaev',
    author_email='mr.felixoid@gmail.com',
    license='License :: OSI Approved :: Apache Software License',
    install_requires=['clickhouse-driver'],
    packages=find_packages(),
    classifiers=[
        'Database',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Visualisatino',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Libraries',
    ],
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'clickhouse-plantuml = clickhouse_plantuml.__main__:main'
        ]
    }
)
