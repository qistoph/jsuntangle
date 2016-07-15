var a = 9;
var b = 8;
var c = (a = 1, b = 2);

var e = (prompt("This popup is missing"), prompt("This popup is shown"))

/* Expected (optimal readable) output:
var a = 9;
var b = 8;
a = 1;
b = 2;
var c = 2;

prompt("This popup is missing");
var e = prompt("This popup is shown")
*/
