if(true) shortCall();

if(true) {
    shortCall();
}

if(true) {
    firstCall();
    secondCall();
}

if(false) noCall();
else doCall();

if(false) {
    noCall();
} else {
    doCall();
}

if(false) {
    noCallOne();
    noCallTwo();
} else {
    doCallOne();
    doCallTwo();
}
