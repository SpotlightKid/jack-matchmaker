#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='jack-matchmaker',
    version="1.0",
    description="Auto-connect new JACK ports.",
    #long_description='',
    author="Christopher Arndt",
    author_email="info@chrisarndt.de",
    url="https://github.com/SpotlightKid/jack-matchmaker",
    license="MIT License",
    packages=["jackmatchmaker"],
    entry_points={
        "console_scripts": [
            "jack-matchmaker = jackmatchmaker:main"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
    ]
)
