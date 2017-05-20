from setuptools import setup, Extension
import glob, numpy
import os.path as op
from os import listdir
from pyuvdata import version
import json

data = [version.git_origin, version.git_hash, version.git_description, version.git_branch]
with open(op.join('pyuvdata', 'GIT_INFO'), 'w') as outfile:
    json.dump(data, outfile)

def indir(path, files):
    return [op.join(path, f) for f in files]

setup_args = {
    'name': 'pyuvdata',
    'author': 'HERA Team',
    'url': 'https://github.com/HERA-Team/pyuvdata',
    'license': 'BSD',
    'description': 'an interface for astronomical interferometeric datasets in python',
    'package_dir': {'pyuvdata': 'pyuvdata', 'uvdata': 'uvdata'},
    'packages': ['pyuvdata', 'uvdata'],
    'scripts': glob.glob('scripts/*'),
    'version': version.version,
    'include_package_data': True,
    'install_requires': ['numpy>=1.10', 'scipy', 'astropy>=1.2', 'pyephem', 'aipy'],
    'classifiers': ['Development Status :: 5 - Production/Stable',
                    'Intended Audience :: Science/Research',
                    'License :: OSI Approved :: BSD License',
                    'Programming Language :: Python :: 2.7',
                    'Topic :: Scientific/Engineering :: Astronomy'],
    'keywords': 'radio astronomy interferometry',
    'ext_modules' : [
            Extension('pyuvdata._miriad', ['pyuvdata/_miriad/miriad_wrap.cpp'] + \
            indir('pyuvdata/_miriad/mir', ['uvio.c','hio.c','pack.c','bug.c',
                'dio.c','headio.c','maskio.c']),
            include_dirs = [numpy.get_include(), 'pyuvdata/_miriad',
                'pyuvdata/_miriad/mir'])  ]
}

if __name__ == '__main__':
    apply(setup, (), setup_args)
