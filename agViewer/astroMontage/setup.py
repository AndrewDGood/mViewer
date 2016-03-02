#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'agMontage',
    version = '1.0',
    author = 'Andrew Good',
    author_email = 'andrew.daniel.good@gmail.com',
    description = 'Wrapper around Montage toolkit for displaying astronomical image/overlay data with advanced controls.',
    license = 'BSD',
    keywords = 'astronomy astronomical image display',
    url = 'https://github.com/AndrewDGood/mViewer',
    
    packages = ['agMontage'],
    install_requires = ['tornado'],
    package_data = { 'agMontage': ['web/*'] }
)
