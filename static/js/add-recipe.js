const $ = cash;

const tagChips = M.Chips.init($('#tag-chips')[0], {onChipAdd: addTagChip, onChipDelete: removeTagChip});
$(tagChips.el).find('input').addClass('hide'); // Hide the text input from the chips array, so users can't add custom tags
M.Dropdown.init($('.dropdown-trigger'));


// Converts the contents of chips to a string in the input element so they can be submitted
function chipsToInput(chipInstance, inputElem) {
    if (chipInstance.chipsData.length > 0) {
            let tags = chipInstance.chipsData.map(function(chip) {
                return chip.tag;
            });
            $(inputElem).val(tags.join('/'));
        }else $(inputElem).val('');
}

// Whenever a chip is added hide its option in the dropdown
function addTagChip($el, renderedChip) {
    tagName = this.chipsData[this.chipsData.length - 1].tag;
    $('#add-tag a[data-tag-name="' + tagName + '"]').parent().addClass('hide');
    $(renderedChip).attr('data-tag-name', tagName)
    if ($('#add-tag li').not('.hide').length == 0) $('#add-tag-button').addClass('disabled');
}

// Whenever a chip is deleted show its option in the dropdown menu
function removeTagChip($el, chip) {
    tagName = $(chip).attr('data-tag-name')
    $('#add-tag a[data-tag-name="' + tagName + '"]').parent().removeClass('hide');
    $('#add-tag-button').removeClass('disabled');
}

$(function() {
    $('#create-recipe').on('submit', function(e) {
        chipsToInput(tagChips, '#tag-input')
    });
    $('#add-tag a').on('click', function() {
        let tagName = $(this).attr('data-tag-name')
        tagChips.addChip({ tag: tagName });
    });
});