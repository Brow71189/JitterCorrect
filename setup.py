# -*- coding: utf-8 -*-

"""
To upload to PyPI, PyPI test, or a local server:
python setup.py bdist_wheel upload -r <server_identifier>
"""

import setuptools

setuptools.setup(
    name='JitterWizard',
    version='0.1.0',
    author='Andreas Mittelberger',
    author_email='Brow71189@gmail.com',
    description='Correct beam jitter in STEM images',
    packages=['nionswift_plugin.jitter_wizard', 'jitter_utils'],
    install_requires=['AnalyzeMaxima'],
    license='MIT',
    include_package_data=True,
    python_requires='~=3.5',
    zip_safe=False,
    dependency_links=['https://github.com/Brow71189/AnalyzeMaxima/tarball/master#egg=AnalyzeMaxima']
)