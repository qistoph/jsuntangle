var a1 = "literal";
var b1 = "-first";
var c1 = "-second";
var d1 = a1 + b1 + c1;
// will be "literal-first-second"

var a2 = somefunc();
var b2 = "-first";
var c2 = "-second";
var d2 = a2 + b2 + c2;
// will be somefunc() + "-first-second"

var a3 = somefunc();
var b3 = "-first";
var c3 = "-second";
var d3 = "-third";
var e3 = a3 + b3 + c3 + d3;
// will be somefunc() + "-first-second-third"
