var obj;
obj = {  "property": "default", "doit": (function () { (console).log(("this.property: " + (this).property)); }) };
var a;
a = "prop";
var b;
b = "erty";
obj["property"] = "updated";
obj["doit"]();
