var $ = cash; // Get cash functions from materialize.js
M.FormSelect.init($('select')); // Initialise materialize select


// Convert selected chips to a string to submit
function chipsToInput(chipContainer, targetInput) {
    var chipsInput = [];
    $(chipContainer + ' .chip.active').each(function() {
        chipsInput.push($(this).data('tag'));
    });
    if (chipsInput.length > 0) $(targetInput).val(chipsInput.join(' '));
    else $(targetInput).remove();
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


// Reset all chips to not active, submits the form to show updated results
function resetChips(chipContainer) {
    $(chipContainer + ' .chip.active').removeClass('active');
    $('#filters-form').trigger('submit');
}


$(function() {
    // Attach event to show/hide filters on mobile
    $('#filter-toggle').on('click', function() {
        $('#filters').toggleClass('hide-on-small-and-down');
        if ($('#filters').hasClass('hide-on-small-and-down')) $('#filter-toggle').html('Show filters <i class="material-icons">keyboard_arrow_down</i>');
        else $('#filter-toggle').html('Hide filters <i class="material-icons">keyboard_arrow_up</i>');
    });

    // Add event handlers to update and submit the filter form
    $('.input-field select').on('change', function() {
        $('#filters-form').trigger('submit');
    });

    $('.reset').on('click', function() {
        resetChips('#' + $(this).data('target'))
    });

    $('.chip').on('click', function() {
        $(this).toggleClass('active');
        $('#filters-form').trigger('submit');
    });

    $('#filter-search').on('keydown', function(e) {
        if (e.which == 13) $('#filters-form').trigger('submit');
    });

    // On submit convert chips to strings and set the sort order depending on input.
    $('#filters-form').on('submit', function() {
        chipsToInput('#include-chips', '#tags')
        chipsToInput('#exclude-chips', '#exclude')
        if ($('#sort').val() == 'total-time') $('#order').val('1');
        else $('#order').val('-1');
        $('#filter-search').attr('name', 'search');
        $('#filters-form')[0].submit();
    });
});