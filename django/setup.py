"""Setup script of loyalty-core"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from setuptools import find_packages

import loyalty_core_models

setup(
    name='package-name',
    version='1.0',

    description='package',
    long_description='package',
    keywords='',

    author='',
    author_email='',
    url='',

    packages=find_packages(exclude=[]),
    classifiers=[
        'Framework :: Django',
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: Non-Free',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    license='',
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django==2.1.11',
        'mysqlclient==1.3.13',
        'django-parler==1.9.2',
        'djangorestframework==3.10.2',
        'django-extensions==2.1.4',
        'python-dateutil==2.5.3',
        'django-environ==0.4.4',
        'django-admin-multiple-choice-list-filter==0.1.1',
        'django-admin-rangefilter==0.3.10',
        'django-import-export==2.0.1',
        'django-admin-numeric-filter==0.1.3'
    ]
)
