var $ = cash; // Get cash functions from materialize.js

// Initialise  materialize chips and dropdowns
var tagChips = M.Chips.init($('#tag-chips')[0], { onChipAdd: addChip, onChipDelete: removeChip });
$(tagChips.el).find('input').addClass('hide'); // Hide the text input from the chips array, so users can't add custom tags
var mealChips = M.Chips.init($('#meal-chips')[0], { onChipAdd: addChip, onChipDelete: removeChip });
$(mealChips.el).find('input').addClass('hide'); // Hide the text input from the chips array, so users can't add custom tags
M.Dropdown.init($('.dropdown-trigger'));


// Whenever a chip is added hide its option in the dropdown
function addChip($el, renderedChip) {
    var tagName = this.chipsData[this.chipsData.length - 1].tag;
    var $addDropdownButton = $('#' + $el.attr('data-add-target'));
    var addDropdown = '#' + $addDropdownButton.attr('data-target');
    $(addDropdown + ' a[data-chip-name="' + tagName + '"]').parent().addClass('hide');
    $(renderedChip).attr('data-chip-name', tagName);
    if ($(addDropdown + ' li').not('.hide').length == 0) $addDropdownButton.addClass('disabled');
}


// Whenever a chip is deleted show its option in the dropdown menu
function removeChip($el, chip) {
    var tagName = $(chip).attr('data-chip-name')
    var $addDropdownButton = $('#' + $el.attr('data-add-target'));
    var addDropdown = '#' + $addDropdownButton.attr('data-target');
    $(addDropdown + ' a[data-chip-name="' + tagName + '"]').parent().removeClass('hide');
    $addDropdownButton.removeClass('disabled');
}


// Converts the contents of chips to a string in the input element so they can be submitted
function chipsToInput(chipInstance, inputElem) {
    if (chipInstance.chipsData.length > 0) {
        var tags = chipInstance.chipsData.map(function(chip) {
            return chip.tag;
        });
        $(inputElem).val(tags.join('/'));
    } else $(inputElem).val('');
}


// Converts the inputs from the time fields into a 00:00 time string to be submitted
function updateTimeInput(target) {
    var hours = parseInt($(target + ' .hours').val());
    var minutes = parseInt($(target + ' .minutes').val());
    if (minutes > 59) {
        $(target + ' .hours').val(Math.min(hours + 1, 24));
        $(target + ' .minutes').val(0)
    } else if (minutes < 0) {
        $(target + ' .hours').val(Math.max(hours - 1, 0));
        $(target + ' .minutes').val(59);
    }
    $(target + '-input').val(hours.toString().padStart(2, '0') + ':' + minutes.toString().padStart(2, '0'));
}


// Combines multiple fields into one, split by newlines for submission.
function concatFields(selector, target) {
    var fields = [];
    $(selector).each(function() {
        if ($(this).val() != null && $(this).val() != '') fields.push($(this).val());
    });
    $(target).val(fields.join('\n'));
}


// Removes the old image from the page along with its hidden url input
function deleteOldImage() {
    $('#old-image-container').remove();
    $('#old-image').remove();
}


// Loads image and passes it to the inputCanvas, deletes old image
// Resets file input if input value is blank
function loadImage() {
    if ($('#image-upload').val() != '' && $('#image-upload').val() != null) {
        var reader = new FileReader();
        reader.readAsDataURL($('#image-upload')[0].files[0]);
        reader.onload = () => {
            window.image = new Image();
            var image = window.image;
            image.src = reader.result;
            image.addEventListener('load', function() {
                deleteOldImage();
                inputCanvas.setImage(window.image);
                $('#image-delete').addClass('scale-in');
                $('#image-crop').addClass('scale-in');
            }, false);
        };
    } else resetFileInput();
}


// Hides and resets the image input canvas, controls and file upload when the image is removed
// Clears the file input by replacing it and reattaching the on change event.
function resetFileInput() {
    $('#image-upload').parent().parent().find('.file-path').val('');
    $('#input-canvas').css({ height: '0px' });
    $('#image-delete').removeClass('scale-in');
    $('#image-crop').removeClass('scale-in');
    $('#image-crop').removeClass('green');
    $('#image-reset').removeClass('scale-in');
    $('#image-data').val(null);
    $('#image-crop i').text('crop');
    inputCanvas.image = null;

    var imageUpload = $('#image-upload');
    var parent = imageUpload.parent();
    imageUpload.remove();
    parent.append('<input type="file" id="image-upload" accept="image/*">');
    $('#image-upload').on('change', loadImage);

}


// Adds a new textarea when user enters a new line, removes the textarea if they backspace the start of it
// Text before/after the caret is passed to the next textarea
function addRemoveInputLine(e) {
    if (e.which == 13) {
        // Return key pressed, and this textarea isn't empty
        e.preventDefault();
        if ($(this).val() != null) {
            var textBefore = $(this).val().slice(0, $(this).prop('selectionStart'));
            var textAfter = $(this).val().slice($(this).prop('selectionEnd'));
            $(this).val(textBefore)
            $(this).parent().after('<li><textarea class="materialize-textarea"></textarea></li>');
            var newLi = $(this).parent().next();
            newLi.on('click', function() { // Attach click listener for entire li (to include numbers)
                $(this).find('textarea')[0].focus();
            });
            var newTextarea = newLi.find('textarea');
            newTextarea.val(textAfter); // Set contents to text after newline
            newTextarea[0].setSelectionRange(0, 0); // Move the caret to the start
            newTextarea[0].focus(); // Focus the textarea
            newTextarea.on('keydown', addRemoveInputLine); // Add event listener for this function
        }
    } else if (e.which == 8 && $(this).prop('selectionStart') == 0 && $(this).parent().parent().find('textarea').length > 1) {
        // Backspace pressed, and caret is at start of input, and this isn't the only textarea
        e.preventDefault();
        var textContent = $(this).val();
        var prevTextarea = $(this).parent().prev().find('textarea');
        console.log(prevTextarea);
        if (textContent != null) { // If there is content and another textarea before this one move it the previous textarea and delete this one
            textContent = textContent.slice($(this).prop('selectionEnd'))
            if (prevTextarea && prevTextarea.length > 0) {
                var caretPosition = prevTextarea.val().length;
                prevTextarea.val(prevTextarea.val() + textContent);
                prevTextarea.prop('selectionStart', caretPosition).prop('selectionEnd', caretPosition);
                prevTextarea[0].focus();
                $(this).parent().remove();
            }
        } else {
            if (prevTextarea && prevTextarea.length > 0) prevTextarea[0].focus(); // Otherwise move the cursor to the previous input, or the next and delete this one
            else $(this).parent().next().find('textarea')[0].focus();
            $(this).parent().remove();
        }
    }
}


// Validates the prep time input field before submission
function validatePrepTime() {
    updateTimeInput('#prep-time');
    if ($('#prep-time-input').val() == '00:00') {
        $('#prep-time input[type=number]').addClass('invalid');
        $('#prep-time').addClass('invalid');
        return false;
    } else {
        $('#prep-time input[type=number]').removeClass('invalid');
        $('#prep-time').removeClass('invalid');
        return true;
    }
}


// Validates a multiline input (such as ingredient or method) to ensure there is something to submit
function validateMultilineInput(target) {
    var valid = false;
    $(target).each(function() {
        if ($(this).val() != '' && $(this).val() != null) valid = true;
    })
    if (!valid) {
        $(target).addClass('invalid');
        return false;
    } else {
        $(target).removeClass('invalid');
        return true;
    }
}


// On load attach event listeners
$(function() {

    M.Tooltip.init($('.tooltipped'));

    // Fix materialize label focus bug
    $('label').on('click', function() {
        var target = $(this).attr('for');
        if (target) $('[name="' + target + '"]')[0].focus();
    });

    // Focus method inputs on number click
    $('.method li').on('click', function() {
        $(this).find('textarea')[0].focus();
    });

    //Initialise the canvas for editing images
    inputCanvas.init();

    // Attach on submit event to form, validate inputs then prepare them for submission
    $('#create-recipe').on('submit', function(e) {
        if (!validatePrepTime()) { // If a validation fails, focus its input
            e.preventDefault();
            $('#prep-time .hours')[0].focus();
        }
        if (!validateMultilineInput('.method textarea')) {
            e.preventDefault();
            $('ol.method').addClass('invalid');
            $('.method textarea')[0].focus();
        } else $('ol.method').removeClass('invalid');
        if (!validateMultilineInput('.ingredient textarea')) {
            e.preventDefault();
            $('ul.ingredient').addClass('invalid');
            $('.ingredient textarea')[0].focus();
        } else $('ul.method').removeClass('invalid');
        if (!validateMultilineInput('[name=title]')) {
            e.preventDefault();
            $('[name=title]')[0].focus();
        }

        // Convert all inputs to strings
        concatFields('.ingredient textarea', '#ingredients');
        concatFields('.method textarea', '#methods');
        updateTimeInput('#cook-time');
        chipsToInput(tagChips, '#tag-input');
        chipsToInput(mealChips, '#meal-input');
        // Draw the final image to the hidden canvas, then render it as a string to a hidden input.
        inputCanvas.renderOutput();
    });

    // Listen for add tag or add meal
    $('.dropdown-content[data-target] a').on('click', function() {
        var tagName = $(this).attr('data-chip-name');
        var chipInstance = M.Chips.getInstance($('#' + $(this).parent().parent().attr('data-target'))[0]);
        chipInstance.addChip({ tag: tagName });
    });

    $('#old-image-delete').on('click', deleteOldImage);

    $('#image-delete').on('click', resetFileInput);

    $('#image-crop').on('click', inputCanvas.toggleCrop);

    $('#image-reset').on('click', function() {
        inputCanvas.autoCrop();
        inputCanvas.showAll();
        M.Tooltip.getInstance($('#image-reset')[0]).close();
    });

    $('#image-upload').on('change', loadImage);

    // Resize canvas on window resize, debounce to a third of a second.
    $(window).on('resize', function() {
        if (!inputCanvas.debounce) {
            inputCanvas.debounce = true;
            setTimeout(function() {
                inputCanvas.resizeCanvas();
            }, 300);
        }
    });

    // Listen for newlines on methods and ingredients, and validate them on blur. Add the invalid class to the ol element to trigger the tooltip if necessary.
    $('.method textarea').on('keydown', addRemoveInputLine).on('blur', function() {
        if (validateMultilineInput('.method textarea')) $('ol.method').removeClass('invalid');
        else $('ol.method').addClass('invalid');
    });
    $('.ingredient textarea').on('keydown', addRemoveInputLine).on('blur', function() {
        if (validateMultilineInput('.ingredient textarea')) $('ol.ingredient').removeClass('invalid');
        else $('ul.ingredient').addClass('invalid');
    });

    // Validate inputs on blur
    $('[name=title]').on('blur', function() {
        validateMultilineInput('[name=title]')
    });
    $('#prep-time input[type=number]').on('blur', validatePrepTime);
});


// inputCanvas stores, manipulates and outputs uploaded images for submission.
// It uses 2 canvases, one to show the user what they're using,
// and another to render the image out at the correct resolution before converting it to a string to submit.
var inputCanvas = {
    elem: $('#input-canvas')[0],
    $elem: $('#input-canvas'),
    ctx: $('#input-canvas')[0].getContext('2d'),
    height: $('#input-canvas')[0].height,
    width: $('#input-canvas')[0].width,
    aspect: 7 / 12,
    crop: false,
    mouse: false,
    touches: [],
    cropStart: { x: 100, y: 100 },
    cropSize: { x: 120, y: 70 },
    init: function() { // Sets up input canvas for image editing.
        var that = this;
        // Adds mouse event listeners for input canvas
        this.$elem.on('mousedown', function(e) {
            e.preventDefault();
            if (that.crop) {
                // If we are cropping, registers the mouse position.
                that.mouse = {
                    x: ((e.pageX - $(this).offset().left - (that.width / 2)) / that.scale) + (that.image.width / 2),
                    y: ((e.pageY - $(this).offset().top - (that.height / 2)) / that.scale) + (that.image.height / 2)
                };
            }
        });
        this.$elem.on('mouseup', function() {
            that.mouse = false;
        });
        this.$elem.on('mouseout', function() {
            that.mouse = false;
        });
        this.$elem.on('mousemove', function(e) {
            if (that.crop) {
                // If we are cropping registers the new mosue position
                var newMouse = {
                    x: ((e.pageX - $(this).offset().left - (that.width / 2)) / that.scale) + (that.image.width / 2),
                    y: ((e.pageY - $(this).offset().top - (that.height / 2)) / that.scale) + (that.image.height / 2)
                };
                if (that.mouse) {
                    // If there is a previous mouse position logged, calculate the change
                    var mouseChange = { x: newMouse.x - that.mouse.x, y: newMouse.y - that.mouse.y }
                    var change;
                    if (that.crop == 'move') {
                        // If we are repositioning the image, move the image by the amount the mouse moved
                        that.cropStart.x += mouseChange.x;
                        that.cropStart.y += mouseChange.y;
                    } else if (that.crop == 'nw-resize') {
                        // If we are resizing, move that corner by the amount the mouse moved, constrain the aspect, and limit scaling the crop to within the image boundries
                        change = mouseChange.x;
                        if (that.cropStart.x < -change) change = -that.cropStart.x;
                        if (that.cropStart.y < -change * that.aspect) change = -that.cropStart.y / that.aspect;
                        that.cropStart.x += change;
                        that.cropStart.y += change * that.aspect;
                        that.cropSize.x -= change;
                        that.cropSize.y -= change * that.aspect;
                    } else if (that.crop == 'se-resize') {
                        change = mouseChange.x;
                        if (that.image.width - (that.cropStart.x + that.cropSize.x) < change) change = that.image.width - (that.cropStart.x + that.cropSize.x);
                        if (that.image.height - (that.cropStart.y + that.cropSize.y) < change * that.aspect) change = (that.image.height - (that.cropStart.y + that.cropSize.y)) / that.aspect;
                        that.cropSize.x += change;
                        that.cropSize.y += change * that.aspect;
                    } else if (that.crop == 'ne-resize') {
                        change = mouseChange.x;
                        if (that.image.width - (that.cropStart.x + that.cropSize.x) < change) change = that.image.width - (that.cropStart.x + that.cropSize.x);
                        if (that.cropStart.y < change * that.aspect) change = -that.cropStart.y / that.aspect;
                        that.cropStart.y -= change * that.aspect;
                        that.cropSize.x += change;
                        that.cropSize.y += change * that.aspect;
                    } else if (that.crop == 'sw-resize') {
                        change = mouseChange.x;
                        if (that.cropStart.x < -change) change = -that.cropStart.x;
                        if (that.image.height - (that.cropStart.y + that.cropSize.y) < -change * that.aspect) change = (that.image.height - (that.cropStart.y + that.cropSize.y)) / that.aspect;
                        that.cropStart.x += change;
                        that.cropSize.x -= change;
                        that.cropSize.y -= change * that.aspect;
                    }
                    
                    // Constrain the minimum size of the crop
                    if (that.cropSize.x < 120 || that.cropSize.y < 70) {
                        that.cropSize.x = 120;
                        that.cropSize.y = 70;
                    }

                    // Constrain the crop to within the boundries of the image
                    if (that.cropStart.x < 0) that.cropStart.x = 0;
                    else if (that.cropStart.x > that.image.width - that.cropSize.x) that.cropStart.x = that.image.width - that.cropSize.x;
                    if (that.cropStart.y < 0) that.cropStart.y = 0;
                    else if (that.cropStart.y > that.image.height - that.cropSize.y) that.cropStart.y = that.image.height - that.cropSize.y;
                    that.mouse = newMouse;
                    that.showAll(); // Redraw the image
                    // If the mouse isn't down, chnage the cursor based on its position within the crop
                } else if (newMouse.x > that.cropStart.x + (that.cropSize.x / 5) && newMouse.x < that.cropStart.x + (that.cropSize.x * 0.8) &&
                    newMouse.y > that.cropStart.y + (that.cropSize.y / 5) && newMouse.y < that.cropStart.y + (that.cropSize.y * 0.8)) {
                    that.$elem.css({ cursor: 'move' });
                    that.crop = 'move';
                } else {
                    if (newMouse.x < that.cropStart.x + (that.cropSize.x / 2)) {
                        if (newMouse.y < that.cropStart.y + (that.cropSize.y / 2)) that.crop = 'nw-resize';
                        else that.crop = 'sw-resize';
                    } else {
                        if (newMouse.y < that.cropStart.y + (that.cropSize.y / 2)) that.crop = 'ne-resize';
                        else that.crop = 'se-resize';
                    }
                    that.$elem.css({ cursor: that.crop });
                }
            }
        });
        //Add touch event listeners for inputCanvas
        // Add new touches on touch start
        this.$elem.on('touchstart', function(e) {
            if (that.crop) {
                e.preventDefault();
                var newTouches = e.changedTouches;

                var i;
                for (i = 0; i < newTouches.length; i++) {
                    that.touches.push(newTouches[i]);
                }
                console.log(that.touches)
            }else that.touches = [];
        });
        
        // Remove touches on touchend
        this.$elem.on('touchend', function(e) {
            if (that.crop) {
                e.preventDefault();
                var removeTouches = e.changedTouches;

                that.touches = that.touches.filter(function(touch) {
                    var i;
                    for (i = 0; i < removeTouches.length; i++) {
                        if (removeTouches[i].identifier == touch.identifier) return false;
                    }
                });
                console.log(that.touches)
            }else that.touches = [];
        });

        this.$elem.on('touchcancel', function(e) {
            if (that.crop) {
                e.preventDefault();
                var removeTouches = e.changedTouches;

                that.touches = that.touches.filter(function(touch) {
                    var i;
                    for (i = 0; i < removeTouches.length; i++) {
                        if (removeTouches[i].identifier == touch.identifier) return false;
                    }
                });
                console.log(that.touches)
            }else that.touches = [];
        });
        
        // Handle touchmoves
        this.$elem.on('touchmove', function(e) {
            if (that.crop) {
                e.preventDefault();
                var updatedTouches = e.changedTouches
                if (that.touches.length == 1 && updatedTouches.length == 1 && that.touches[0].identifier == updatedTouches[0].identifier) { // If one finger touch, it's a move
                    var touchStartPos = {
                        x: ((that.touches[0].pageX - $(this).offset().left - (that.width / 2)) / that.scale) + (that.image.width / 2),
                        y: ((that.touches[0].pageY - $(this).offset().top - (that.height / 2)) / that.scale) + (that.image.height / 2)
                    };
                    var touchEndPos = {
                        x: ((updatedTouches[0].pageX - $(this).offset().left - (that.width / 2)) / that.scale) + (that.image.width / 2),
                        y: ((updatedTouches[0].pageY - $(this).offset().top - (that.height / 2)) / that.scale) + (that.image.height / 2)
                    };

                    console.log(touchStartPos, touchEndPos)

                    var touchPosChange = { x: touchEndPos.x - touchStartPos.x, y: touchEndPos.y - touchStartPos.y }
                    
                    // Move the image by the amount the finger moved
                    that.cropStart.x += touchPosChange.x;
                    that.cropStart.y += touchPosChange.y;

                    that.touches[0] = updatedTouches[0]; // Replace the previous touch event with the new one

                }else if (that.touches.length == 2) { // If two finger touch, its a zoom
                    // Find the distance between touches at the start
                    var startDistance = Math.sqrt(Math.pow(that.touches[0].pageX - that.touches[1].pageX, 2) + Math.pow(that.touches[0].pageY - that.touches[1].pageY, 2));
                    // Update touches
                    var i, j;
                    for (i = 0; i < updatedTouches.length; i++) {
                        for (j = 0; j < that.touches.length; j++) {
                            if (updatedTouches[i].identifier == that.touches[j].identifier) that.touches[j] = updatedTouches[i];
                        }   
                    }
                    // Find the new distance between touches
                    var endDistance = Math.sqrt(Math.pow(that.touches[0].pageX - that.touches[1].pageX, 2) + Math.pow(that.touches[0].pageY - that.touches[1].pageY, 2));

                    // See how much the size has changed
                    var change = endDistance / startDistance;

                    // Constrain that change to the smallest dimension
                    if (change > 1) {
                        if (that.aspect < that.image.height / that.image.width) change = Math.min(that.image.width / that.cropSize.x , change);
                        else  change = Math.min(that.image.height / that.cropSize.y, change);
                    }

                    // Move the top left corner outwards by half the change, the scale the crop size.
                    that.cropStart.x = that.cropStart.x - ((that.cropSize.x * (change - 1)) / 2);
                    that.cropStart.y = that.cropStart.y - ((that.cropSize.y * (change - 1)) / 2);

                    that.cropSize.x = that.cropSize.x * change;
                    that.cropSize.y = that.cropSize.y * change;
                    
                    // Limit the minimum size of the crop
                    if (that.cropSize.x < 120 || that.cropSize.y < 70) {
                        that.cropSize.x = 120;
                        that.cropSize.y = 70;
                    }

                }else{ // Otherwise just update all touch positions
                    var k, l;
                    for (k = 0; k < updatedTouches.length; k++) {
                        for (l = 0; l < that.touches.length; l++) {
                            if (updatedTouches[k].identifier == that.touches[l].identifier) that.touches[l] = updatedTouches[k];
                        }   
                    }
                }

                // Constrain the crop to within the boundries of the image
                if (that.cropStart.x < 0) that.cropStart.x = 0;
                else if (that.cropStart.x > that.image.width - that.cropSize.x) that.cropStart.x = that.image.width - that.cropSize.x;
                if (that.cropStart.y < 0) that.cropStart.y = 0;
                else if (that.cropStart.y > that.image.height - that.cropSize.y) that.cropStart.y = that.image.height - that.cropSize.y;
                
                that.showAll(); // Redraw the image

            }else that.touches = [];
        });
    },
    toggleCrop: function() { // Toggle the input canvas in and out of crop mode, change buttons to reflect options
        if (inputCanvas.crop) {
            inputCanvas.showOutput();
            $('#image-reset').removeClass('scale-in');
            $('#image-crop i').text('crop');
            $('#image-crop').removeClass('green');
            inputCanvas.crop = false;
            inputCanvas.$elem.css({ cursor: 'auto' });
        } else {
            $('#image-crop i').text('check');
            $('#image-crop').addClass('green');
            $('#image-reset').addClass('scale-in');
            inputCanvas.crop = true;
            inputCanvas.$elem.css({ cursor: 'move' });
            inputCanvas.showAll();
        }
        M.Tooltip.getInstance($('#image-crop')[0]).close();
    },
    setImage: function(image) { // Set the image to edit in the input canvas
        if (image.width < 240 || image.height < 140) M.toast({ html: 'Image too small, choose a larger image!' });
        else {
            this.image = image;
        this.autoCrop();
        this.showOutput();
        this.renderOutput();
        $('#image-reset').removeClass('scale-in');
        $('#image-crop i').text('crop');
        inputCanvas.crop = false;
        }
    },
    autoCrop: function() { // Crop the image to the centre of the image, constrained to the aspect ratio, as large as it will fit.
        var imageAspect = this.image.height / this.image.width;
        if (imageAspect > this.aspect) {
            this.cropSize.x = this.image.width;
            this.cropSize.y = this.cropSize.x * this.aspect;
            this.cropStart.x = 0;
            this.cropStart.y = (this.image.height - this.cropSize.y) / 2;
        } else {
            this.cropSize.y = this.image.height;
            this.cropSize.x = this.cropSize.y / this.aspect;
            this.cropStart.y = 0;
            this.cropStart.x = (this.image.width - this.cropSize.x) / 2;
        }
    },
    showOutput: function() { // Show only the cropped image in the input canvas
        this.width = this.elem.width = this.$elem.parent().width();
        this.height = this.elem.height = this.width * this.aspect;
        this.$elem.css({ height: this.height + 'px' });
        this.ctx.resetTransform();
        this.scale = this.width / this.cropSize.x;
        this.ctx.scale(this.scale, this.scale);
        this.ctx.drawImage(this.image, -this.cropStart.x, -this.cropStart.y);
        this.renderOutput();
    },
    showAll: function() { // Show the whole image in the input canvas, with the cropped area marked.
        var imageAspect = this.image.height / this.image.width;
        if (imageAspect > this.aspect) this.scale = this.height / this.image.height;
        else this.scale = this.width / this.image.width;
        this.ctx.resetTransform();
        this.ctx.clearRect(0, 0, this.width, this.height)
        this.ctx.translate(this.width / 2, this.height / 2);
        this.ctx.scale(this.scale, this.scale);
        this.ctx.translate(-this.image.width / 2, -this.image.height / 2);
        this.ctx.drawImage(this.image, 0, 0);
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        // https://stackoverflow.com/questions/13618844/polygon-with-a-hole-in-the-middle-with-html5s-canvas
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(this.image.width, 0);
        this.ctx.lineTo(this.image.width, this.image.height);
        this.ctx.lineTo(0, this.image.height);
        this.ctx.lineTo(0, 0);
        this.ctx.moveTo(this.cropStart.x, this.cropStart.y);
        this.ctx.lineTo(this.cropStart.x, this.cropStart.y + this.cropSize.y);
        this.ctx.lineTo(this.cropStart.x + this.cropSize.x, this.cropStart.y + this.cropSize.y);
        this.ctx.lineTo(this.cropStart.x + this.cropSize.x, this.cropStart.y);
        this.ctx.lineTo(this.cropStart.x, this.cropStart.y);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 2 / this.scale;
        this.ctx.strokeRect(this.cropStart.x, this.cropStart.y, this.cropSize.x, this.cropSize.y);
    },
    renderOutput: function() { // Redraw the cropped image to the apropriately sized output canvas, then convert that image to a string to submit.
        var target = $('#output-canvas')[0];
        var width = target.width;

        var ctx = target.getContext('2d');
        ctx.resetTransform();

        var scale = width / this.cropSize.x;
        ctx.scale(scale, scale);

        ctx.drawImage(this.image, -this.cropStart.x, -this.cropStart.y);
        $('#image-data').val(target.toDataURL('image/jpeg', 0.5).split(',')[1]);
    },
    resizeCanvas: function() { // Resize the canvas to fit, reset the debounce on resizing.
        this.debounce = false;
        if (this.image) {
            this.$elem.removeClass('resize-height');
            this.showOutput();
            if (this.crop) this.showAll();
            this.$elem.addClass('resize-height');
        }
    }

}