var obj = {
	"property": "default",
	"doit": function() {
		console.log("this.property: " + this.property);
	}
};

var a = "prop";
var b = "erty";
obj[a + b] = "updated";
obj.doit();
