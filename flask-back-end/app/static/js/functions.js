function showUncertainties() {
// Get the checkbox
var checkBox = document.getElementById("myCheck");
// Get the output text
var form = document.getElementById("uncertainty");

// If the checkbox is checked, display the output text
if (checkBox.checked == true){
    form.style.display = "block";
} else {
    form.style.display = "none";
}
};

function onlyOne(checkbox) {
    var checkboxes = document.getElementsByName('check')
    checkboxes.forEach((item) => {
        if (item !== checkbox) item.checked = false
    })
}

