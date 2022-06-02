
from setuptools import setup, find_packages


def install_requires():
    req = []
    with open('requirements.txt') as f:
        for line in f.readlines():
            req.append(line)

    return req

setup(
    name='ZK Yaml',
    version='0.1',
    packages=find_packages(exclude=('test.*')),
    url='',
    author='Avi Peretz',
    author_email='',
    description='',
    test_suite='test',
    install_requires=install_requires(),
)
