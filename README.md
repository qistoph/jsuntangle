[![Build Status](https://travis-ci.org/qistoph/jsuntangle.svg?branch=master)](https://travis-ci.org/qistoph/jsuntangle)

jsuntangle
==========

Untangle obfuscated javascript, e.g:
- `a=1; b=2; c=3; d=Math.random()*(a+b+c)` :arrow_right: `d=Math.random()*(6)`
- `a="some"; b="text"; c=a+b;` :arrow_right: `c="sometext";`
- `eval("callFunc()")` :arrow_right: `callFunc();`
- `a="shorttext"; b=a.length();` :arrow_right: `a="shorttext"; b=9;`
- `arr=[2,4,6,8]; val=arr[2];` :arrow_right: `arr=[2,4,6,8]; val=4;`
- ...

Requirements
------------
Tested with Debian 8 (jessie) and python 2.7

**PIP**
- `apt-get install python-pip`
- `pip install -r requirements.txt`


**PyV8**
- https://github.com/qistoph/pyv8

Get & Run
---------
```
git clone https://github.com/qistoph/jsuntangle.git
cd jsuntangle
./bin/jsuntangle
```

System Wide Installation
------------------------
```
git clone https://github.com/qistoph/jsuntangle.git
cd jsuntangle
sudo python setup.py install
jsuntangle
```
Development tips
----------------
Run tests:
```
./checks/run.sh
```

Check differences:
```
./checks/compare.sh
```

Check Travis-CS config:
```
travis lint .travis.yml
```

Preview README.md
```
grip README.md 0.0.0.0
```
