"""Setup script of velib-irc-bot"""
from setuptools import setup
from setuptools import find_packages

setup(
    name='velib-irc-bot',
    version='0.1.dev0',

    description='IRC bot for velib',
    keywords='velib, irc',

    author='Fantomas42',
    author_email='fantomas42@gmail.com',
    url='https://github.com/Fantomas42/velib-irc-bot',

    packages=find_packages(),
    install_requires=['irc==12.1.1',
                      'veliberator==0.3.3']
)
