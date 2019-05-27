const $ = cash;

const tagChips = M.Chips.init($('#tag-chips')[0], { onChipAdd: addChip, onChipDelete: removeChip });
$(tagChips.el).find('input').addClass('hide'); // Hide the text input from the chips array, so users can't add custom tags
const mealChips = M.Chips.init($('#meal-chips')[0], { onChipAdd: addChip, onChipDelete: removeChip });
$(mealChips.el).find('input').addClass('hide'); // Hide the text input from the chips array, so users can't add custom tags
M.Dropdown.init($('.dropdown-trigger'));

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

// Converts the contents of chips to a string in the input element so they can be submitted
function chipsToInput(chipInstance, inputElem) {
    if (chipInstance.chipsData.length > 0) {
        let tags = chipInstance.chipsData.map(function(chip) {
            return chip.tag;
        });
        $(inputElem).val(tags.join('/'));
    } else $(inputElem).val('');
}

// Converts the inputs from the time fields into a 00:00 time string to be submitted
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

function deleteOldImage() {
    $('#old-image-container').remove();
    $('#old-image').remove();
}

function loadImage() {
    if ($('#image-upload').val() != '' && $('#image-upload').val() != null) {
        let reader = new FileReader();
        reader.readAsDataURL($('#image-upload')[0].files[0]);
        reader.onload = () => {
            window.image = new Image();
            let image = window.image;
            image.src = reader.result;
            image.addEventListener('load', function() {
                deleteOldImage();
                inputCanvas.setImage(window.image);
                $('#image-delete').addClass('scale-in');
                $('#image-crop').addClass('scale-in');
            }, false);
        };
    }else resetFileInput();
}

function resetFileInput() {
    $('#image-upload').parent().parent().find('.file-path').val('');
    $('#input-canvas').css({height: '0px'});
    $('#image-delete').removeClass('scale-in');
    $('#image-crop').removeClass('scale-in');
    $('#image-crop').removeClass('green');
    $('#image-reset').removeClass('scale-in');
    $('#image-data').val(null);
    $('#image-crop i').text('crop');
    inputCanvas.image = null;
}

function addRemoveMethodLine(e) {
    if (e.which == 13) {
        e.preventDefault();
        if ($(this).val() != null) {
            let textBefore = $(this).val().slice(0, $(this).prop("selectionStart"));
            let textAfter = $(this).val().slice($(this).prop("selectionEnd"));
            $(this).val(textBefore)
            $(this).parent().after('<li><textarea class="materialize-textarea"></textarea></li>');
            let newTextarea = $(this).parent().next().find('textarea');
            newTextarea.val(textAfter); // Set contents to text after newline
            newTextarea[0].setSelectionRange(0, 0); // Move the carot to the start
            newTextarea[0].focus(); // Focus the textarea
            newTextarea.on('keydown', addRemoveMethodLine); // Add event listener for this function
        }
    }else if (e.which == 8 && $(this).prop("selectionStart") == 0 && $('.method textarea').length > 1) {
        e.preventDefault();
        let textContent = $(this).val();
        let prevTextarea = $(this).parent().prev().find('textarea');
        console.log(prevTextarea);
        if (textContent != null) {
            textContent = textContent.slice($(this).prop("selectionEnd"))
            if (prevTextarea && prevTextarea.length > 0) {
                caretPosition = prevTextarea.val().length;
                prevTextarea.val(prevTextarea.val() + textContent);
                prevTextarea.prop("selectionStart", caretPosition).prop("selectionEnd", caretPosition);
                prevTextarea[0].focus();
                $(this).parent().remove();
            }
        }else{
            if (prevTextarea && prevTextarea.length > 0) prevTextarea[0].focus();
            else $(this).parent().next().find('textarea')[0].focus();
            $(this).parent().remove();
        }
        
    }
}

function concatFields(selector, target) {
    let fields = [];
    $(selector).each(function() {
        if ($(this).val() != null && $(this).val() != '') fields.push($(this).val());
    });
    $(target).val(fields.join('\n'));
}

$(function() {

    $("label").on('click', function() {
        let target = $(this).attr('for');
        if (target) $('[name="' + target + '"]')[0].focus();
    });

    inputCanvas.init();

    $('#create-recipe').on('submit', function(e) {
        concatFields('.method textarea', '#methods');
        updateTimeInput('#prep-time');
        updateTimeInput('#cook-time');
        chipsToInput(tagChips, '#tag-input');
        chipsToInput(mealChips, '#meal-input');
    });

    $('.dropdown-content[data-target] a').on('click', function() {
        let tagName = $(this).attr('data-chip-name');
        let chipInstance = M.Chips.getInstance($('#' + $(this).parent().parent().attr('data-target'))[0]);
        chipInstance.addChip({ tag: tagName });
    });

    $('#old-image-delete').on('click', deleteOldImage);

    $('#image-delete').on('click', resetFileInput);

    $('#image-crop').on('click', inputCanvas.toggleCrop);

    $(window).on('resize', function() {
        if (!inputCanvas.debounce) {
            inputCanvas.debounce = true;
            setTimeout(function() {
                inputCanvas.resizeCanvas();
            }, 300);
        }
    });

    $('#image-reset').on('click', function () {
        inputCanvas.autoCrop();
        inputCanvas.showAll();
    });

    $('#image-upload').on('change', loadImage);

    $('.method textarea').on('keydown', addRemoveMethodLine);
});

let inputCanvas = {
    elem: $('#input-canvas')[0],
    $elem: $('#input-canvas'),
    ctx: $('#input-canvas')[0].getContext('2d'),
    height: $('#input-canvas')[0].height,
    width: $('#input-canvas')[0].width,
    aspect: 7 / 12,
    crop: false,
    mouse: false,
    cropStart: {x: 100, y: 100},
    cropSize: {x: 120, y: 70},
    init() {
        let that = this;
        this.$elem.on('mousedown', function(e) {
            e.preventDefault();
            if (that.crop) {
                that.mouse = {x: ((e.pageX - $(this).offset().left - (that.width / 2)) / that.scale) + (that.image.width / 2),
                              y: ((e.pageY - $(this).offset().top - (that.height / 2)) / that.scale) + (that.image.height / 2)};
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
                let newMouse = {x: ((e.pageX - $(this).offset().left - (that.width / 2)) / that.scale) + (that.image.width / 2),
                                y: ((e.pageY - $(this).offset().top - (that.height / 2)) / that.scale) + (that.image.height / 2)};
                if (that.mouse) {
                    let mouseChange = {x: newMouse.x - that.mouse.x, y: newMouse.y - that.mouse.y}
                    if (that.crop == 'move') {
                        that.cropStart.x += mouseChange.x;
                        that.cropStart.y += mouseChange.y;
                    }else if (that.crop == 'nw-resize') {
                        let change = mouseChange.x;
                        if (that.cropStart.x < -change) change = -that.cropStart.x;
                        if (that.cropStart.y < -change * that.aspect) change = -that.cropStart.y / that.aspect;
                        that.cropStart.x += change;
                        that.cropStart.y += change * that.aspect;
                        that.cropSize.x -= change;
                        that.cropSize.y -= change * that.aspect;
                    }else if (that.crop == 'se-resize') {
                        let change = mouseChange.x;
                        if (that.image.width - (that.cropStart.x + that.cropSize.x) < change) change = that.image.width - (that.cropStart.x + that.cropSize.x);
                        if (that.image.height - (that.cropStart.y + that.cropSize.y) < change * that.aspect) change = (that.image.height - (that.cropStart.y + that.cropSize.y)) / that.aspect;
                        that.cropSize.x += change;
                        that.cropSize.y += change * that.aspect;
                    }else if (that.crop == 'ne-resize') {
                        let change = mouseChange.x;
                        if (that.image.width - (that.cropStart.x + that.cropSize.x) < change) change = that.image.width - (that.cropStart.x + that.cropSize.x);
                        if (that.cropStart.y < change * that.aspect) change = -that.cropStart.y / that.aspect;
                        that.cropStart.y -= change * that.aspect;
                        that.cropSize.x += change;
                        that.cropSize.y += change * that.aspect;
                    }else if (that.crop == 'sw-resize') {
                        let change = mouseChange.x;
                        if (that.cropStart.x < -change) change = -that.cropStart.x;
                        if (that.image.height - (that.cropStart.y + that.cropSize.y) < -change * that.aspect) change = (that.image.height - (that.cropStart.y + that.cropSize.y)) / that.aspect;
                        that.cropStart.x += change;
                        that.cropSize.x -= change;
                        that.cropSize.y -= change * that.aspect;
                    }
                    if (that.cropStart.x < 0) that.cropStart.x = 0;
                    else if (that.cropStart.x > that.image.width - that.cropSize.x) that.cropStart.x = that.image.width - that.cropSize.x;
                    if (that.cropStart.y < 0) that.cropStart.y = 0;
                    else if (that.cropStart.y > that.image.height - that.cropSize.y) that.cropStart.y = that.image.height - that.cropSize.y;
                    that.mouse = newMouse;
                    that.showAll();
                }else if (newMouse.x > that.cropStart.x + (that.cropSize.x / 5) && newMouse.x < that.cropStart.x + (that.cropSize.x * 0.8) &&
                          newMouse.y > that.cropStart.y + (that.cropSize.y / 5) && newMouse.y < that.cropStart.y + (that.cropSize.y * 0.8)) {
                    that.$elem.css({cursor: 'move'});
                    that.crop = 'move';
                }else{
                    if (newMouse.x < that.cropStart.x + (that.cropSize.x / 2)) {
                        if (newMouse.y < that.cropStart.y + (that.cropSize.y / 2)) that.crop = 'nw-resize';
                        else that.crop = 'sw-resize';
                    }else{
                        if (newMouse.y < that.cropStart.y + (that.cropSize.y / 2)) that.crop = 'ne-resize';
                        else that.crop = 'se-resize';
                    }
                    that.$elem.css({cursor: that.crop});
                }
            }
            
        });
    },
    toggleCrop() {
        if (inputCanvas.crop){
            inputCanvas.showOutput();
            $('#image-reset').removeClass('scale-in');
            $('#image-crop i').text('crop');
            $('#image-crop').removeClass('green');
            inputCanvas.crop = false;
            inputCanvas.$elem.css({cursor: 'auto'});
        }else{
            $('#image-crop i').text('check');
            $('#image-crop').addClass('green');
            $('#image-reset').addClass('scale-in');
            inputCanvas.crop = true;
            inputCanvas.$elem.css({cursor: 'move'});
            inputCanvas.showAll();
        }
    },
    setImage(image) {
        this.image = image;
        this.autoCrop();
        this.showOutput();
        this.renderOutput();
        $('#image-reset').removeClass('scale-in');
        $('#image-crop i').text('crop');
        inputCanvas.crop = false;
    },
    autoCrop() {
        let imageAspect = this.image.height / this.image.width;
        if (imageAspect > this.aspect) {
            this.cropSize.x = this.image.width;
            this.cropSize.y = this.cropSize.x * this.aspect;
            this.cropStart.x = 0;
            this.cropStart.y = (this.image.height - this.cropSize.y) / 2;
        }else{
            this.cropSize.y = this.image.height;
            this.cropSize.x = this.cropSize.y / this.aspect;
            this.cropStart.y = 0;
            this.cropStart.x = (this.image.width - this.cropSize.x) / 2;
        }
    },
    showOutput() {
        this.width = this.elem.width = this.$elem.parent().width();
        this.height = this.elem.height = this.width * this.aspect;
        this.$elem.css({height: this.height + 'px'});
        this.ctx.resetTransform();
        this.scale = this.width / this.cropSize.x;
        this.ctx.scale(this.scale, this.scale);
        this.ctx.drawImage(this.image, -this.cropStart.x, -this.cropStart.y);
        this.renderOutput();
    },
    showAll() {
        let imageAspect = this.image.height / this.image.width;
        if (imageAspect > this.aspect) this.scale = this.height / this.image.height;
        else this.scale = this.width / this.image.width;
        this.ctx.resetTransform();
        this.ctx.clearRect(0, 0, this.width, this.height)
        this.ctx.translate(this.width /2, this.height /2);
        this.ctx.scale(this.scale, this.scale);
        this.ctx.translate(-this.image.width /2, -this.image.height /2);
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
    renderOutput() {
        let target = $('#output-canvas')[0];
        let width = target.width;
        let height = target.height;
        let ctx = target.getContext('2d');
        ctx.resetTransform();
        
        scale = width / this.cropSize.x;
        ctx.scale(scale, scale);
        
        ctx.drawImage(this.image, -this.cropStart.x, -this.cropStart.y);
        $('#image-data').val(target.toDataURL('image/jpeg', 0.5).split(',')[1]);
    },
    resizeCanvas() {
        this.debounce = false;
        if (this.image) {
            this.$elem.removeClass('resize-height');
            this.showOutput();
            if (this.crop) this.showAll();
            this.$elem.addClass('resize-height');
        }
    }
    
}