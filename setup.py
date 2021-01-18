from setuptools import setup, find_packages
import platform
import os
from glob import glob


def data_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths


setup(
    name='robot-listener-service',
    version='0.1',
    description='Robot listener service',
    url='https://github.com/rhinst/robot-listener-service',
    author='Rob Hinst',
    author_email='rob@hinst.net',
    license='MIT',
    packages=find_packages(),
    data_files=[
        ('config', data_files('config')),
        ('model', data_files('model')),
    ],
    install_requires=[
        'redis==3.5.3',
        'himl==0.7.0',
        'pocketsphinx==0.1.15',
        'pyaudio==0.2.11'
    ],
    test_suite='tests',
    tests_require=['pytest==6.2.1'],
    entry_points={
        'console_scripts': ['listener=listener.__main__:main']
    }
)
