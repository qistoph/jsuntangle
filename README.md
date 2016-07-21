jsuntangle
==========

Untangle obfuscated javascript, e.g:
- `a=1; b=2; c=3; d=Math.random()*(a+b+c)` :arrow_right: `d=Math.random()*(6)`
- `a="some"; b="text"; c=a+b;` :arrow_right: `c="sometext";`
- `eval("callFunc()")` :arrow_right: `callFunc();`
- `a="shorttext"; b=a.length();` :arrow_right: `a="shorttext"; b=9;`
- `arr=[2,4,6,8]; val=arr[2];` :arrow_right: `arr=[2,4,6,8]; val=4;`
- ...

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
