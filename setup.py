# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from ocrd_utils import VERSION

install_requires = open('requirements.txt').read().split('\n')
install_requires.append('ocrd_utils == %s' % VERSION)

setup(
    name='ocrd_kwalitee',
    version=VERSION,
    description='OCR-D framework MP kwalitee check',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Konstantin Baierer',
    author_email='unixprog@gmail.com',
    url='https://github.com/OCR-D/kwalitee',
    license='Apache License 2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    install_requires=install_requires,
    package_data={
        '': ['*.json', '*.yml', '*.yaml', '*.list', '*.xml'],
    },
    entry_points={
        'console_scripts': [
            'ocrd-kwalitee=kwalitee.cli:cli',
        ]
    },
)
