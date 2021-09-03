#!/usr/bin/env python3
import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='pifan',
    version='0.1',
    description='Dell PowerEdge fan speed controller for Raspberry Pi',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Shawn Poulson',
    author_email='shawn@explodingcoder.com',
    url='https://github.com/spoulson/pifan',
    packages=setuptools.find_packages(where="src"),
    package_dir={'': 'src'},
    scripts=[
        'bin/pifan'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: Other/Proprietary License',
        'Intended Audience :: System Administrators',
        'Operating System :: POSIX',
        'Programming Language :: Python 3',
        'Topic :: System',
    ],
    python_requires='>=3.7'
)
