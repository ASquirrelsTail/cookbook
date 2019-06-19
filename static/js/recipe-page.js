var $ = cash; // Get cash functions from materialize.js


// Sends a json get request, and calls the callback on ready state change
function jsonGet(url, callback) {
    var xhr = new XMLHttpRequest();

    xhr.open("GET", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = callback;

    xhr.send();
}


// Sends a json post request, and calls the callback on ready state change
function jsonPost(url, data, callback) {
    var xhr = new XMLHttpRequest();

    xhr.open("POST", url, true); //Filter by postcodes, lat and lng as these are the only things we need
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = callback;

    xhr.send(JSON.stringify(data));
}


// Delete comment callback
function deleteComment() {
    if (this.readyState == 4) {
        if (this.status == 200) {
            var response = JSON.parse(this.responseText);
            if (response.success === true) {
                jsonGet(commentUrl, reloadComments); // If a change has been made, reload the comments
            }
            response.messages.forEach(function(message) {
                M.toast({ html: message });
            });
        } else M.toast({ html: 'Failed to delete comment!' });
    }
}


// Callback for loading comments
function reloadComments() {
    if (this.readyState == 4) {
        if (this.status == 200) {
            var response = JSON.parse(this.responseText);
            renderComments(response.comments);
            response.messages.forEach(function(message) {
                M.toast({ html: message });
            });
        }
    }
}


// Renders all comments again to reflect changes
function renderComments(comments) {
    var count = comments.filter(function(comment) { return !comment.deleted }).length;
    $('#comment-count').text(count + ' comments.'); // Update comment count.
    $('.comment-count').text(count);
    // Empty the comments list and repopulate with retrived comments.
    $('#comments-content').html('');
    comments.forEach(function(comment) {
        if (!comment.deleted) {
            $('#comments-content').append('<div class="divider"></div>');
            $('#comments-content').append('<p>By ' + comment.username + ' at ' + comment.time + '</p>');
            var commentContent = '';
            comment.comment.split('\n').forEach(function(line) { // Splits content on new line and renders as seperate paragraphs.
                commentContent += '<p>' + line + '</p>';
            });
            $('#comments-content').append('<blockquote>' + commentContent + '</blockquote>');
            // If there is the option to delete a comment add the delete button
            if (comment.delete == true) {
                var deleteForm = '<form action="';
                deleteForm += deleteCommentUrl;
                deleteForm += '" method="POST" class="delete-comment">';
                deleteForm += '<input type="hidden" name="comment-index" value="' + comment.index + '">';
                deleteForm += '<div class="delete-wrapper">';
                deleteForm += '<button class="btn waves-effect waves-light red small right" type="submit"><i class="material-icons left">delete</i>Delete Comment</button>';
                deleteForm += '</div>';
                deleteForm += '</form>';
                $('#comments-content').append(deleteForm);
            }
        }
    });
    // Attach event handler to new delete buttons
    $('.delete-comment').on('submit', function(e) {
        e.preventDefault();
        $('.delete-comment .btn[type=submit]').addClass('disabled')
        jsonPost($(this).attr('action'), { 'comment-index': $(this).find('input[name="comment-index"]').val() }, deleteComment);
    });
    $('#comments-content').append('<div class="divider"></div>');
}


// Callback for toggling favourite
function updateFavourite() {
    if (this.readyState == 4) {
        if (this.status == 200) {
            var response = JSON.parse(this.responseText);
            if (response.favourite === true) {
                $('.fav-count').text(parseInt($('.fav-count').text()) + 1)
                $('.fav-link i').text('favorite');
                M.toast({ html: '<i class="material-icons left">favorite</i> Recipe added to favorites!' });
            } else if (response.favourite === false) {
                $('.fav-link i').text('favorite_border');
                $('.fav-count').text(parseInt($('.fav-count').text()) - 1)
                M.toast({ html: 'Recipe removed from favourites.' });
            }
        } else M.toast({ html: 'Oops. Something went wrong.' });
    }
}


// Callback for toggling feature
function updateFeature() {
    if (this.readyState == 4) {
        if (this.status == 200) {
            var response = JSON.parse(this.responseText);
            if (response.feature === true) {
                $('.feat-link i').text('star');
                M.toast({ html: '<i class="material-icons left">star</i> Recipe featured!' });
            } else if (response.feature === false) {
                $('.feat-link i').text('star_border');
                M.toast({ html: 'Recipe removed from features.' });
            }
        } else M.toast({ html: 'Oops. Something went wrong.' });
    }
}


$(function() {
    M.Tooltip.init($('.tooltipped'));

    // Attach events for buttons
    $('.fav-link').on('click', function(e) {
        e.preventDefault();
        jsonGet($(this).attr('href'), updateFavourite);
    });
    $('.feat-link').on('click', function(e) {
        e.preventDefault();
        jsonGet($(this).attr('href'), updateFeature);
    });
    $('#add-comment').on('submit', function(e) {
        e.preventDefault();
        jsonPost($(this).attr('action'), { comment: $('#comment').val() }, reloadComments);
        $('#comment').val('');
    });
    $('.delete-comment').on('submit', function(e) {
        e.preventDefault();
        $('.delete-comment .btn[type=submit]').addClass('disabled')
        jsonPost($(this).attr('action'), { 'comment-index': $(this).find('input[name="comment-index"]').val() }, deleteComment);
    });
});