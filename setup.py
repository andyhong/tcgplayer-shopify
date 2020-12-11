from setuptools import setup

setup(
    name="tcgify",
    version="1.0",
    install_requires=[
        "pyinquirer",
        "requests",
        "pandas",
        "pyfiglet"
    ],
    entry_points={
        'console_scripts': [
            'tcgify=main:main'
        ]
    }
)
