from distutils.core import setup

import backbone


setup(
    name='django-backbone',
    packages=['backbone', 'backbone.tests'],
    version=backbone.__version__,
    description=backbone.__doc__,
    long_description=open('README.rst').read(),
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
    author='Zach Mathew',
    url='http://github.com/zmathew/django-backbone',
    license='BSD',
)
