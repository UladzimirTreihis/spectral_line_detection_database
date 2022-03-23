function raToSexagecimal(raString) {
    var hString="";
    var mString="";
    var sString="";
    let raFloat = parseFloat(raString);
    let h = Math.floor(raFloat / 15);
    let m = Math.floor((raFloat - h*15) / 0.25);
    let s = ((raFloat - h*15) - m*0.25) * 240; 
    if(h<10){
        hString += "0" + h.toFixed() + "h";
    } else {
        hString += h.toFixed() + "h";
    };
    if(m<10){
        mString += "0" + m.toFixed() + "m";
    } else {
        mString += m.toFixed() + "m";
    };
    if(s<10){
        sString += "0" + s.toFixed(3) + "s";
    } else {
        sString += s.toFixed(3) + "s";
    };

    return hString + mString + sString;
};

var raCoordinates = document.getElementsByName("raCoordinates");
for (var i = 0; i < raCoordinates.length; i++) {
    raCoordinates[i].innerHTML = raToSexagecimal(raCoordinates[i].id);
};

function decToSexagecimal(decString) {
    var dString="";
    var mString="";
    var sString="";
    var minus=""
    let decFloat = parseFloat(decString);
    if (decFloat<0) {
        decFloat *= -1
        minus += "-"
    } 
    let d = Math.floor(decFloat);
    let m = Math.floor((decFloat - d) * 60);
    let s = (((decFloat - d) * 60) - m) * 60; 
    if(d<10 && d>-10){
        dString += "0" + d.toFixed() + "d";
    } else {
        dString += d.toFixed() + "d";
    };
    if(m<10){
        mString += "0" + m.toFixed() + "m";
    } else {
        mString += m.toFixed() + "m";
    };
    if(s<10){
        sString += "0" + s.toFixed(3) + "s";
    } else {
        sString += s.toFixed(3) + "s";
    };

    return minus + dString + mString + sString;
};

var decCoordinates = document.getElementsByName("decCoordinates");
for (var i = 0; i < decCoordinates.length; i++) {
    decCoordinates[i].innerHTML = decToSexagecimal(decCoordinates[i].id);
};

