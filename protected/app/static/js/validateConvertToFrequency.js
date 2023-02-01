function validateConvertToFrequency() {
    // Get the checkbox
    var checkBox = document.getElementById('convertToFrequency');
    // Get the output text
    var linkDownloadLines = document.getElementById('downloadLines');
    var linkDownloadEverything = document.getElementById('downloadEverything');

    // If the checkbox is checked, display the output text
    if (checkBox.checked == true){
      linkDownloadLines.href = "{{ url_for ('main.convert_to_CSV', table = 'Galaxy Lines', identifier = galaxy.id, to_frequency = '1')|tojson }}";
    } else {
      linkDownloadLines.href = "{{ url_for ('main.convert_to_CSV', table = 'Galaxy Lines', identifier = galaxy.id, to_frequency = '0')|tojson }}";
    }
}