function shouldBeKept(a) {
	return a + "-" + Math.random();
}

function replaceThis() {
	var data = ["not", "not", "not", "keep", "not", "not"];
	var n = 3;
	return data[n];
}

function replaceToo() {
	var data = ["not", "not", "not", "keep", "not", "not"][3];
	return data;
}

function replaceThree() {
	return "keep";
}

function replaceFour(data) {
	return data;
}

function tooComplex() {
	if(Math.random() > 0.5) {
		return "A";
	}
	return "B";
}

function twoComplex() {
	var a = Math.random() > 0.5 ? "A" : "B";
	return a;
}

var test1 = shouldBeKept();
var test2 = replaceThis();
var test3 = replaceToo();
var test4 = replaceThree();
var test5 = replaceFour("keep");
var test6 = (function() { return "keep"; })();
var test7 = tooComplex();
var test8 = twoComplex();
