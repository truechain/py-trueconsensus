#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


deps = {
    'snailchain': [
    ],
    'fastchain': [
    ],
    'minerva': [
    ],
    # 'vendor': [
    #     "py-evm>=0.2.0-alpha.14",
    # ],
    'test': [
        "hypothesis==3.44.26",
        "pytest~=3.2",
        "pytest-asyncio==0.8.0",
        "pytest-cov==2.5.1",
        "pytest-logging>=2015.11.4",
        "pytest-xdist==1.18.1",
        "pytest-watch>=4.1.0,<5",
    ],
    'lint': [
        "flake8==3.5.0",
        "mypy<0.600",
    ],
    'doc': [
        #"py-evm>=0.2.0-alpha.14",
        "pytest~=3.2",
        "Sphinx>=1.5.5,<2.0.0",
        "sphinx_rtd_theme>=0.1.9",
        "sphinxcontrib-asyncio>=0.2.0",
    ],
    'dev': [
        "bumpversion>=0.5.3,<1",
        "wheel",
        "tox==2.7.0",
    ],
}

deps['dev'] = (
    deps['snailchain'] +
    deps['fastchain'] +
    deps['test'] +
    deps['doc'] +
    deps['minerva'] +
    deps['dev'] +
    deps['lint']
)

# As long as evm, p2p and trinity are managed together in the py-evm
# package, someone running a `pip install py-evm` should expect all
# dependencies for evm, p2p and trinity to get installed.
install_requires = deps['snailchain'] + deps['fastchain'] + deps['minerva']

setup(
    name='py-trueconsensus',
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version='0.1.0-alpha.1',
    description="Python implementation of the Truechain's Hybrid Consensus",
    long_description_markdown_filename='README.md',
    author='Archit Sharma',
    author_email='archit@pm.me',
    url='https://github.com/truechain/py-trueconsensus',
    include_package_data=True,
    py_modules=['snailchain', 'fastchain', 'minerva'],
    install_requires=install_requires,
    extras_require=deps,
    setup_requires=['setuptools-markdown'],
    license='Apache License 2.0',
    zip_safe=False,
    keywords='truechain blockchain hybrid consensus',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License 2.0',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Networking'
    ],
    # minerva
    entry_points={
        'console_scripts': ['minerva=minerva:main'],
    },
)
