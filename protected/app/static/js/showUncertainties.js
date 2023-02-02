function showUncertainties() {
    // Get the checkbox
    var checkBox = document.getElementById("myCheck");
    // Get the output text
    fields = []
    var values = document.getElementsByName("value");
    var positives = document.getElementsByName("positive");
    var negatives = document.getElementsByName("negative");

    if (checkBox.checked == true){
        values.forEach((value) => {
            value.className = "col-md-4";
        }
        )
        positives.forEach((positive) => {
            positive.className = "col-md-4";
        }
        )
        negatives.forEach((negative) => {
            negative.style.display = "block";
        }   
        )   
    } else {
        values.forEach((value) => {
            value.className = "col-md-6";
        }
        )
        positives.forEach((positive) => {
            positive.className = "col-md-6";
        }
        )
        negatives.forEach((negative) => {
            negative.style.display = "none";
        }   
        )
    }
};