import sys
from setuptools import setup, find_packages

kwargs = {
    'packages': find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*']),
    'include_package_data': True,
    'install_requires': [
        'django>=1.4,<1.7',
    ],
    'name': 'django-tracking2',
    'version': __import__('tracking').get_version(),
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'django-tracking2 tracks the length of time visitors '\
        'and registered users spend on your site',
    'license': 'BSD',
    'keywords': 'visitor tracking time analytics',
    'url': 'https://github.com/bruth/django-tracking2',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
}

setup(**kwargs)
