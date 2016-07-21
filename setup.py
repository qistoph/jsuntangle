from distutils.core import setup

setup(
    name='jsuntangle',
    version='0.1dev',
    packages=['jsuntangler'],
    scripts=['bin/jsuntangle'],
    author='Chris van Marle',
    author_email='qistoph@gmail.com',
    url='https://www.github.com/qistoph/jsuntangle',
    license='GPLv3',
    long_description=open('README.md').read()
)
