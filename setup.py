# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='githack',
    author='Owen Chia',
    packages=['githack'],
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
)
