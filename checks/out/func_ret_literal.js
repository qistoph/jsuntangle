shouldBeKept = (function shouldBeKept(a) {
  return a + "-" + Math["random"]();
});
replaceThis = (function replaceThis() {
  var data;
  var n;
  return "keep";
});
replaceToo = (function replaceToo() {
  var dataToo;
  return "keep";
});
replaceThree = (function replaceThree() {
  return "keep";
});
replaceFour = (function replaceFour(dataFour) {
  return dataFour;
});
replaceFive = (function replaceFive() {
  return "keep";
});
replaceSix = (function replaceSix(argSix) {
  return argSix;
});
replaceSeven = (function replaceSeven(argSeven) {
  return argSeven;
});
tooComplex = (function tooComplex() {
  if((Math["random"]() > 0.5)) {
    return "A";
  }
  return "B";
});
twoComplex = (function twoComplex() {
  var a;
  var a;
  a = (Math["random"]() > 0.5) ? "A" : "B";
  return a;
});
var test1;
test1 = shouldBeKept();
var test2;
test2 = "keep";
var test3;
test3 = "keep";
var test4;
test4 = "keep";
var test5;
test5 = "keep";
var test6;
test6 = "keep";
var test7;
test7 = "keep";
var test8;
test8 = tooComplex();
var test9;
test9 = twoComplex();
var test10;
test10 = "dataSix";
var test11;
test11 = "dataSeven";
