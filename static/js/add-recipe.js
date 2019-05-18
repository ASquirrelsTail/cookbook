const $ = cash;

const tagChips = M.Chips.init($('#tag-chips')[0], { onChipAdd: addChip, onChipDelete: removeChip });
$(tagChips.el).find('input').addClass('hide'); // Hide the text input from the chips array, so users can't add custom tags
const mealChips = M.Chips.init($('#meal-chips')[0], { onChipAdd: addChip, onChipDelete: removeChip });
$(mealChips.el).find('input').addClass('hide'); // Hide the text input from the chips array, so users can't add custom tags
M.Dropdown.init($('.dropdown-trigger'));


// Converts the contents of chips to a string in the input element so they can be submitted
function chipsToInput(chipInstance, inputElem) {
    if (chipInstance.chipsData.length > 0) {
        let tags = chipInstance.chipsData.map(function(chip) {
            return chip.tag;
        });
        $(inputElem).val(tags.join('/'));
    } else $(inputElem).val('');
}

// Whenever a chip is added hide its option in the dropdown
function addChip($el, renderedChip) {
    tagName = this.chipsData[this.chipsData.length - 1].tag;
    $addDropdownButton = $('#' + $el.attr('data-add-target'));
    addDropdown = '#' + $addDropdownButton.attr('data-target');
    $(addDropdown + ' a[data-chip-name="' + tagName + '"]').parent().addClass('hide');
    $(renderedChip).attr('data-chip-name', tagName);
    if ($(addDropdown + ' li').not('.hide').length == 0) $addDropdownButton.addClass('disabled');
}

// Whenever a chip is deleted show its option in the dropdown menu
function removeChip($el, chip) {
    tagName = $(chip).attr('data-chip-name')
    $addDropdownButton = $('#' + $el.attr('data-add-target'));
    addDropdown = '#' + $addDropdownButton.attr('data-target');
    $(addDropdown + ' a[data-chip-name="' + tagName + '"]').parent().removeClass('hide');
    $addDropdownButton.removeClass('disabled');
}

function updateTimeInput(target) {
    let hours = parseInt($(target + ' .hours').val());
    let minutes = parseInt($(target + ' .minutes').val());
    if (minutes > 59) {
        $(target + ' .hours').val(Math.min(hours + 1, 24));
        $(target + ' .minutes').val(0)
    } else if (minutes < 0) {
        $(target + ' .hours').val(Math.max(hours - 1, 0));
        $(target + ' .minutes').val(59);
    }
    $(target + '-input').val(hours.toString().padStart(2, '0') + ':' + minutes.toString().padStart(2, '0'));
}

$(function() {
    $('#create-recipe').on('submit', function(e) {
        chipsToInput(tagChips, '#tag-input');
        chipsToInput(mealChips, '#meal-input');
    });
    $('#prep-time input').on('change', function() {
        updateTimeInput('#prep-time');
    });
    $('#cook-time input').on('change', function() {
        updateTimeInput('#cook-time');
    });
    $('.dropdown-content[data-target] a').on('click', function() {
        let tagName = $(this).attr('data-chip-name');
        console.log('#' + $(this).parent().parent().attr('data-target'));
        let chipInstance = M.Chips.getInstance($('#' + $(this).parent().parent().attr('data-target'))[0]);
        chipInstance.addChip({ tag: tagName });
    });

    $('#image-delete').on('click', function () {
        $('#image-upload').parent().parent().find('.file-path').val('');
        $('#input-canvas').css({height: '0px'});
        $('#canvas-overlay').css({opacity: 0})
        $('#image-data').val(null);
    })

    $('#image-upload').on('change', () => {
            if ($('#image-upload').val() != '' && $('#image-upload').val() != null) {

                let reader = new FileReader();
                reader.readAsDataURL($('#image-upload')[0].files[0]);
                reader.onload = () => {
                    let image = new Image();
                    image.src = reader.result;
                    image.addEventListener('load', () => {
                        console.log("File loaded")
                        $('#input-canvas')[0].width = $('#input-canvas').parent().width();
                        $('#input-canvas')[0].height = 7 / 12 * $('#input-canvas').parent().width();
                        let inputCtx = $('#input-canvas')[0].getContext('2d');
                        inputCtx.resetTransform();
                        inputCtx.scale($('#input-canvas').parent().width() / image.width, $('#input-canvas').parent().width() / image.width);
                        inputCtx.drawImage(image, 0, 0);
                        inputCtx.fillStyle = 'rgba(0, 0, 0, 0.5)';
                        inputCtx.fillRect(0, 7 / 12 * image.width, image.width, image.height - (7 / 12 * image.width));
                        $('#input-canvas').css({height: (7 / 12 * $('#input-canvas').parent().width()) + 'px'});
                        $('#canvas-overlay').css({opacity: 1})
                        $('#output-canvas')[0].getContext('2d').resetTransform();
                        $('#output-canvas')[0].getContext('2d').scale(1200 / image.width, 1200 / image.width);
                        $('#output-canvas')[0].getContext('2d').drawImage(image, 0, 0);
                        $('#image-data').val($('#output-canvas')[0].toDataURL('image/jpeg', 0.5).split(',')[1]);
                    }, false);
                };
            }else{
                $('#image-upload').parent().parent().find('.file-path').val('');
                $('#input-canvas').css({height: '0px'});
                $('#canvas-overlay').css({opacity: 0})
                $('#image-data').val(null);
            }
        });
});