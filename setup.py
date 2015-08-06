from setuptools import setup, find_packages
from io import open

setup(
    name='DeclRY',
    version='0.0.01',
    author='Jorge Alpedrinha Ramos',
    author_email='jalpedrinharamos@gmail.com',
    packages=find_packages(),
    license='LICENSE.txt',
    description='DeclRY is inspired by Django-admin, made for user facing webapps instead of backend',
    long_description=open('README.rst').read(),
    install_requires=[
        "Django == 1.5.1",
    ],
)
