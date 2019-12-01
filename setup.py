#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


exec(open('jackmatchmaker/version.py').read())

setup(
    name='jack-matchmaker',
    version=__version__,  # noqa
    description="Auto-connect new JACK ports.",
    long_description=open('README.rst').read(),
    author="Christopher Arndt",
    author_email="info@chrisarndt.de",
    url="https://github.com/SpotlightKid/jack-matchmaker",
    license="GPL2",
    packages=["jackmatchmaker"],
    entry_points={
        "console_scripts": [
            "jack-matchmaker = jackmatchmaker:main"
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: MIDI',
        'Topic :: Utilities',
    ]
)
