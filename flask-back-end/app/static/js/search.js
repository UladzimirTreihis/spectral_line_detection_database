$(document).ready(function(){
    var galaxy_name = [];
    function loadGalaxies(){
    $.getJSON('/galaxies', function(data, status, xhr)
    {
    for (var i = 0; i < data.length; i++ ) {
        galaxy_name.push(data[i].name);
    }
    });
    };
    loadGalaxies();
    
    $('#galaxy_name').autocomplete({
    source: galaxy_name, 
    }); 

    $.ajax({
    data: {galaxy_name:$('#galaxy_name').val()},
    type: 'POST',
    url : '/process'
    })
    .done(function(data){ 
    })
    e.preventDefault();
    
}); 