var $ = cash; // Get cash functions from materialize.js

// Convert selected chips to a string to submit
function chipsToInput(chipContainer, targetInput) {
    var chipsInput = [];
    $(chipContainer + ' .chip.active').each(function() {
        chipsInput.push($(this).data('tag'));
    });
    if (chipsInput.length > 0) $(targetInput).val(chipsInput.join(' '));
}

// Add active class to chips, for use populating the list from the server on load.
function activateChips(chipContainer, tagString) {
    var tags = []
    if (tagString.indexOf(' ') != -1) tags = tagString.split(' ');
    else tags = [tagString];
    tags.forEach(function(tag) {
        if (tag != '') $(chipContainer).find('[data-tag=' + tag + ']').addClass('active');
    });
}

$(function() {
    // Toggle the active class when chips are clicked
    $('.chip').on('click', function() {
        $(this).toggleClass('active');
    });

    // Convert chips to strings on submit
    $('#preferences-form').on('submit', function(e) {
        chipsToInput('#include-chips', '#tags');
        chipsToInput('#exclude-chips', '#exclude');
    });
});