try {
	var asdf = asdf();
} catch(ex) {
	alert(ex);
}

for(var i=0; i<10; ++i) {
	try {
		i += j;
	} catch(ex) {
		alert(ex);
	}
}
