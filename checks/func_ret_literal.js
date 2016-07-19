function shouldBeKept(a) {
	return a + "-" + Math.random();
}

function replaceThis() {
	var data = ["not", "not", "not", "keep", "not", "not"];
	var n = 3;
	return data[n];
}

function replaceToo() {
	var dataToo = ["not", "not", "not", "keep", "not", "not"][3];
	return dataToo;
}

function replaceThree() {
	return "keep";
}

function replaceFour(dataFour) {
	return dataFour;
}

function replaceFive() {
	return ["one", "two", "keep", "four"][2];
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
var test6 = replaceFive();
var test7 = (function() { return "keep"; })();
var test8 = tooComplex();
var test9 = twoComplex();
