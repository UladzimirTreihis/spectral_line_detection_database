$(function () {
    $(".gfgselect").click(function () {
        var notes = $(this).parents("tr").find(".notes").text();
        var p = "";
        p += "<p> " + notes + "</p>";
        $("#divGFG").empty();
        $("#divGFG").append(p);
    });
});