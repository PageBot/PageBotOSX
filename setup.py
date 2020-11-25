# -----------------------------------------------------------------------------
#     Copyright (c) 2016+ Buro Petr van Blokland + Claudia Mens
#     www.pagebot.io
#
#     P A G E B O T
#
#     Licensed under MIT conditions
#
#     Supporting usage of DrawBot, www.drawbot.com
# -----------------------------------------------------------------------------
#
#     setup.py

from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pagebotosx',
    #use_scm_version=True,
    version='1.0.1.2',
    description='Mac OS X context for PageBot based on DrawBot.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/PageBot/PageBotOSX",
    author = 'Petr van Blokland, Michiel Kauw-A-Tjoe',
    author_email = 'r@petr.com',
    package_dir={'': 'Lib'},
    packages=find_packages('Lib'),
    include_package_data=True,
    setup_requires=[''],
    license = 'MIT',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3.6',
        'Topic :: Artistic Software',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Graphics :: Editors',
        'Topic :: Multimedia :: Graphics :: Editors :: Raster-Based',
        'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Fonts'],
    install_requires=[
        'pyobjc',
        'pagebot',
        'drawbot @ git+https://github.com/typemytype/drawbot.git ',
        'pysketch @ git+https://github.com/PageBot/PySketch.git'
        ],
)
