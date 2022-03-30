function showUncertainties() {
// Get the checkbox
var checkBox = document.getElementById("myCheck");
// Get the output text
fields = []
var one = document.getElementById("uncertainty1");
if (checkBox.checked == true){
        one.style.display = "block";
    } else {
        one.style.display = "none";
    }
var two = document.getElementById("uncertainty2");
if (checkBox.checked == true){
        two.style.display = "block";
    } else {
        two.style.display = "none";
    }

var three = document.getElementById("uncertainty3");
if (checkBox.checked == true){
        three.style.display = "block";
    } else {
        three.style.display = "none";
    }
var four = document.getElementById("uncertainty4");
if (checkBox.checked == true){
        four.style.display = "block";
    } else {
        four.style.display = "none";
    }
};

function onlyOne(checkbox) {
    var checkboxes = document.getElementsByName('check')
    checkboxes.forEach((item) => {
        if (item !== checkbox) item.checked = false
    })
}

var checkboxes = document.querySelectorAll("input[type = 'checkbox']");
var rows = document.getElementsByName('row');
function checkAll(myCheckbox){
    if(myCheckbox.checked == true){
        checkboxes.forEach(function(checkbox){
            checkbox.checked = true;
        });
    }
    else{
        checkboxes.forEach(function(checkbox){
            checkbox.checked = false;
        });
    }
}

// Find all input elements.
var inputs = document.getElementsByTagName("input");
var checked = [];
var list = [1, 2];
var action_delete = "delete";
var action_approve = "approve";

// Cycle our input elements list and find the checkboxes 
// that are checked.
function deleteFromIdList(){
    for ( var i = 0; i < checkboxes.length; i++ ) {
        if ( checkboxes[i].name == "rowid" && checkboxes[i].checked ) {
            checked.push(checkboxes[i].value);
            rows[i-1].style.display = "none";
        }
    };
    $.ajax({
        type: "POST",
        url:"http://127.0.0.1:5000/posts/",
        data: JSON.stringify({'delete': checked}),
        dataType: 'json'
    }).done(function(data) { 
        console.log(data);
    });
}

function approveFromIdList(){
    for ( var i = 0; i < checkboxes.length; i++ ) {
        if ( checkboxes[i].name == "rowid" && checkboxes[i].checked ) {
            checked.push(checkboxes[i].value);
            rows[i-1].style.display = "none";
        }
    };
    $.ajax({
        type: "POST",
        url:"http://127.0.0.1:5000/posts/",
        data: JSON.stringify({'approve': checked}),
        dataType: 'json'
    }).done(function(data) { 
        console.log(data);
    });
}

function checkFromIdList(){
    for ( var i = 0; i < checkboxes.length; i++ ) {
        if ( checkboxes[i].name == "rowid" && checkboxes[i].checked ) {
            checked.push(checkboxes[i].value);
            rows[i-1].style.display = "none";
        }
    };
    $.ajax({
        type: "POST",
        url:"http://127.0.0.1:5000/posts/",
        data: JSON.stringify({'check': checked}),
        dataType: 'json'
    }).done(function(data) { 
        console.log(data);
    });
}

