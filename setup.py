from setuptools import setup, find_packages
import platform
import os
from glob import glob


def data_files(directory):
    return directory, [file for file in glob(f"directory/**/*", recursive=True) if os.path.isfile(file)]


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
        data_files('config'),
        data_files('model')
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
