# -*- coding: utf-8 -*-
from setuptools import setup
from pathlib import Path

here = Path(__file__).parent
long_description = here / 'README'

setup(
    name='githack',
    version='0.0.3',
    author='Owen Chia',
    url='https://github.com/OwenChia/githack',
    packages=['githack', 'githack/parse'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    entry_points={
        'console_scripts': [
            'githack=githack.__main__:main',
        ],
    },
    long_description=long_description.read_text(),
    long_description_content_type='text/plain',
    keywords='git web-security leakage',
    python_requires='>=3.6',
)
