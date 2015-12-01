from setuptools import setup, find_packages

setup(
    name = "canmatrix",
    version = "0.1",
    packages = find_packages(),
    entry_points={'console_scripts': ['compare = compare:main',
                                      'convert = convert:main']}
)
