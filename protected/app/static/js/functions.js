function onlyOne(checkbox) {
    var checkboxes = document.getElementsByName('check')
    checkboxes.forEach((item) => {
        if (item !== checkbox) {
            item.checked = false
        }
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

// Cycle our input elements list and find the checkboxes 
// that are checked.
function fromIDList(){
  for ( let i = 0; i < checkboxes.length; i++ ) {
    if ( checkboxes[i].name == "rowid" && checkboxes[i].checked ) {
        checked.push(checkboxes[i].value);
        rows[i-1].style.display = "none";
        checkboxes[i] = false;
    }
};
}

function unCheckAll(){
checkboxes.forEach(function(checkbox){
    checkbox.checked = false;
});
}

function emptyChecked(){
    checked.length = 0;
}

function deleteFromIdList(){
    fromIDList()
    console.log(checked)
    $.ajax({
        type: "POST",
        url:document.URL,
        data: JSON.stringify({'delete': checked}),
        dataType: 'json'
    }).done(function(data) { 
        console.log(data);
    });
    emptyChecked();
    unCheckAll();
}

function approveFromIdList(){
    fromIDList()
    $.ajax({
        type: "POST",
        url:document.URL,
        data: JSON.stringify({'approve': checked}),
        dataType: 'json'
    }).done(function(data) { 
        console.log(data);
    });
    emptyChecked();
    unCheckAll();
}



