import os
from re import match, findall, sub, split, escape as re_escape
from datetime import datetime
from flask import Flask, render_template, request, flash, session, redirect, url_for, abort, jsonify, escape, get_flashed_messages
from flask_pymongo import PyMongo
from PIL import Image
from base64 import b64decode
from io import BytesIO
import boto3
import botocore

s3 = boto3.client('s3')
s3_bucket = os.getenv('AWS_BUCKET')

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.secret_key = os.getenv('SECRET_KEY')

mongo = PyMongo(app)


####################
# Helper Functions #
####################

def hours_mins_to_string(hours_mins):
    '''
    Helper function to convert stored times to strings
    '''
    if hours_mins == '00:00' or not match("^[0-9]{2}:[0-5][0-9]$", hours_mins):
        return '0 minutes'
    hours, mins = hours_mins.split(':')
    hours = int(hours)
    mins = int(mins)
    string = ''
    if hours > 1:
        string += str(hours) + ' hours'
    elif hours == 1:
        string += str(hours) + ' hour'
    if hours > 0 and mins > 0:
        string += ' '
    if mins > 1:
        string += str(mins) + ' minutes'
    elif mins == 1:
        string += '1 minute'
    return string


def exists(variable, key=None):
    '''
    Helper function to check a variable is declared and not None
    '''
    if key is not None:
        try:
            variable = variable[key]
        except KeyError:
            return False
    return variable is not None and variable != ''


####################
# Shared Functions #
####################

def find_recipes(page='1', tags=None, exclude=None, meals=None, username=None, forks=None, search=None, featured=None,
                 following=None, favourites=None, preferences=None, sort='views', order='-1', **kwargs):
    '''
    Search function to find recipes based on a set of queries.
    '''
    query = {'deleted': {'$ne': True}}
    user = session.get('username')
    if preferences == '-1':  # Ignore preferences if preferences set to -1
        user_preferences = None
        user_exclusions = None
    else:
        user_preferences = session.get('preferences')
        user_exclusions = session.get('exclusions')
    if exists(user_preferences):  # If user preferences are set, add them to the tags
        if exists(tags):
            tags = tags + ' ' + user_preferences
        else:
            tags = user_preferences
    if exists(tags):  # All tags in query should be in tags
        query['tags'] = {'$all': tags.split(' ')}

    if exists(user_exclusions):
        if exists(exclude):  # If user exclusions are set, add them to the exclusions
            exclude = exclude + ' ' + user_exclusions
        else:
            exclude = user_exclusions
    if exists(exclude):  # Any exclusions should not be in tags
        exclude = exclude.split(' ')
        if query.get('tags'):
            query['tags']['$nin'] = exclude
        else:
            query['tags'] = {'$nin': exclude}
    if query.get('tags'):
        for tag in query['tags'].get('$all', []):
            if tag in query['tags'].get('$nin', []):
                query['tags']['$nin'].remove(tag)

    if exists(meals):
        query['meals'] = {'$all': meals.split(' ')}
    if exists(favourites):
        query['favouriting-users'] = user
    if following is not None:  # If we are looking only for users we follow the recipe author should be in the list of users we follow
        following_user = mongo.db.users.find_one({'username': user}, {'following': 1})
        if isinstance(following_user.get('following'), list):
            query['username'] = {'$in': following_user['following']}
        else:
            if page != '1':  # If we don't follow anybody return no recipes, if the page is greater than one it's out of bounds
                abort(404)
            else:
                return {'recipes': [], 'no_recipes': 0, 'page': 1}
    elif exists(username):
        query['username'] = username
    if exists(forks):
        query['parent'] = forks
    if exists(featured):
        query['featured'] = {'$exists': True}
    if exists(search):  # If there is a search string, find any parts in double quotes and seperate them out
        search_strings = None
        if '"' in search:
            search_strings = findall('".+"', search)
            for search_string in search_strings:
                search = sub(' *' + re_escape(search_string) + ' *', '', search)
        if ' ' in search:
            search = split(' +', search)
            search = '"' + '" "'.join(search) + '"'
        if search_strings is not None:
            search += ' ' + ' '.join(search_strings)
        query['$text'] = {'$search': search}

    try:
        order = int(order)
        if order != 1 and order != -1:
            order = -1
    except ValueError:
        order = -1
    try:
        page = int(page)
    except ValueError:
        page = 1
    offset = (page - 1) * 10
    no_recipes = mongo.db.recipes.count_documents(query)  # Count recipes matching query, if there's at least one and our page number is in bounds find the recipes
    if page < 1 or (page != 1 and offset >= no_recipes):
        abort(404)  # Out of bounds error
    if no_recipes > 0:
        recipes = (
            mongo.db.recipes.find(query, {'urn': 1, 'title': 1, 'username': 1, 'image': 1, 'comment-count': 1, 'favourites': 1})
            .sort(sort, order)
            .skip(offset)
            .limit(10)
        )
    else:
        recipes = []

    return {'recipes': recipes, 'no_recipes': no_recipes, 'page': page}


def create_recipe_data(recipe_data):
    '''
    Prepares recipe data for submission
    '''
    if exists(recipe_data, 'prep-time'):  # Add cook time and prep time together as 00:00 string to order redipes by
        prep_time = recipe_data['prep-time'].split(':')
        if exists(recipe_data, 'cook-time'):
            cook_time = recipe_data['cook-time'].split(':')
        else:
            cook_time = ['00', '00']
        mins = int(prep_time[1]) + int(cook_time[1])
        hours = int(prep_time[0]) + int(cook_time[0])
        hours += mins // 60
        mins = mins % 60
        recipe_data['total-time'] = '{:0>2}:{:0>2}'.format(hours, mins)
    else:
        recipe_data['total-time'] = '99:59'
    if exists(recipe_data, 'tags'):  # If tags exists convert them back to a list
        recipe_data['tags'] = recipe_data.get('tags', '').split('/')
    else:
        recipe_data.pop('tags', '')
    if exists(recipe_data, 'meals'):  # If meals exists convert them back to a list
        recipe_data['meals'] = recipe_data.get('meals', '').split('/')
    else:
        recipe_data.pop('meals', '')
    if exists(recipe_data, 'image'):  # If there is an image included decode it back to bytes
        imageBytes = b64decode(recipe_data['image'])
        try:
            image = Image.open(BytesIO(imageBytes))  # Open the image and check its type and size are correct
            if image.format == 'JPEG' and image.size == (1200, 700):
                filename = recipe_data['urn'] + '.jpg'
                if s3_bucket is not None:  # If S3 is set up, upload it and return an unsigned url
                    s3.upload_fileobj(BytesIO(imageBytes), s3_bucket, filename)
                    # Snippet for unsigned url for S3 object from https://github.com/boto/boto3/issues/110
                    config = s3._client_config
                    config.signature_version = botocore.UNSIGNED
                    recipe_data['image'] = boto3.client('s3', config=config) \
                        .generate_presigned_url('get_object', ExpiresIn=0,
                                                Params={'Bucket': s3_bucket, 'Key': filename})
                else:  # Otherwise save it locally
                    f = open(os.path.join('static', 'user-images', filename), 'wb')
                    f.write(imageBytes)
                    f.close()
                    recipe_data['image'] = url_for('static', filename='user-images/' + filename)
            else:
                recipe_data.pop('image', '')
                flash('Failed to upload image.')
            image.close()
        except IOError:
            recipe_data.pop('image', '')
            flash('Failed to upload image.')
    elif exists(recipe_data, 'old-image'):  # Otherwise if there is an old image url, use that
        recipe_data['image'] = recipe_data['old-image']
        recipe_data.pop('old-image', '')
    else:
        recipe_data['image'] = None
    return recipe_data


def prepare_recipe_template(action, recipe_data=None, urn=None):
    '''
    Calls render template for add/edit-recipe. Gets tags and meals and prefills recipe data if it exists.
    '''
    all_tags = mongo.db.tags.find()
    all_meals = mongo.db.meals.find()
    if isinstance(recipe_data, dict):
        recipe_data['prep-time'] = recipe_data['prep-time'].split(':')
        recipe_data['cook-time'] = recipe_data['cook-time'].split(':')
        if recipe_data.get('tags', '') != '':
            recipe_data['tags'] = '/'.join(recipe_data['tags'])
        if recipe_data.get('meals', ''):
            recipe_data['meals'] = '/'.join(recipe_data['meals'])
        if recipe_data.get('image') is not None:
            recipe_data['old-image'] = recipe_data['image']
    else:
        recipe_data = None

    return render_template('add-recipe.html', action=action, recipe=recipe_data, username=session.get('username'),
                           tags=all_tags, meals=all_meals, urn=urn)


#########
# Index #
#########

@app.route('/')
def index():
    featured_recipes = find_recipes(featured='1', sort='featured', order='-1').get('recipes')
    recent_recipes = find_recipes(sort='date', order='-1')
    recent_recipes['query'] = {'sort': 'date', 'order': '-1'}
    popular_recipes = find_recipes(sort='favourites', order='-1')
    popular_recipes['query'] = {'sort': 'favourites', 'order': '-1'}
    username = session.get('username')
    if username is not None:
        following_recipes = find_recipes(following='1', sort='date', order='-1')
        following_recipes['query'] = {'following': '1', 'sort': 'date', 'order': '-1'}
        if following_recipes['no_recipes'] == 0:
            following_recipes = None
    else:
        following_recipes = None
    return render_template('index.html', username=username, featured_recipes=featured_recipes,
                           recent_recipes=recent_recipes, popular_recipes=popular_recipes,
                           following_recipes=following_recipes)


################
# Users routes #
################

@app.route('/new-user', methods=['POST', 'GET'])
def new_user():
    '''
    New user page, POST route creates a new user
    '''
    if session.get('username') is not None:  # If user is already logged in redirect to home page
        return redirect(url_for('index'))
    elif request.method == 'POST':
        username = request.form.get('username', '')
        # Regex snippet for allowed characters from
        # https://stackoverflow.com/questions/89909/how-do-i-verify-that-a-string-only-contains-letters-numbers-underscores-and-da
        if not exists(username) or not match("^[A-Za-z0-9_-]{3,20}$", username):  # If the username is mssing, not between 3 and 20 chars or already taken don't add it
            flash("Please enter a valid username!")
        elif mongo.db.logins.find_one({'username': username}) is not None:
            flash('Username "{}" is already taken, please choose another.'.format(username))
        else:  # Otherwise add the usernamed to the logins collection, and create a document for the user in the users collection
            mongo.db.logins.insert_one({'username': username})
            mongo.db.users.insert_one({'username': username, 'joined': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")})
            return redirect(url_for('login'), code=307)
    return render_template('new-user.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    '''
    Log In Page, POST route logs user in
    '''
    target = None
    if session.get('username') is not None:  # If user is logged in redirect to index
        return redirect(url_for('index'))
    elif request.method == 'POST':
        username = request.form.get('username', '')
        if username != '' and mongo.db.logins.find_one({'username': username}):  # If the user exists log them in and add their preferences to the session cookie
            session['username'] = username
            user_data = mongo.db.users.find_one({'username': username}, {'preferences': 1, 'exclusions': 1})
            session['preferences'] = user_data.get('preferences', None)
            session['exclusions'] = user_data.get('exclusions', None)
            flash('Successfully logged in as "{}".'.format(username))
            if request.form.get('target') is not None:  # If there is a redirect target send them there
                return redirect(request.form['target'])
            return redirect(url_for('index'))  # Otherwise send them home
        else:
            flash("Failed to log in, invalid username.")  # Otherwise preserve the target page if it's there and keep them on the log in page
            target = request.form.get('target')

    return render_template('login.html', target=target)


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    '''
    Admin settings page. Post route adds/removes tags and meals
    '''
    if session.get('username') != 'Admin':  # Return forbidden if user not Admin
        return abort(403)
    else:
        if request.method == 'POST':
            if exists(request.form, 'add-tag'):  # Validate and added tags or meals and add them to the mongo collection
                if match('^[A-Za-z-]+$', request.form['add-tag']):
                    mongo.db.tags.insert_one({'name': request.form['add-tag']})
                    flash('Added tag "{}"'.format(request.form['add-tag']))
                else:
                    flash('Failed to add tag.')
            if exists(request.form, 'add-meal'):
                if match('^[A-Za-z-]+$', request.form['add-meal']):
                    mongo.db.meals.insert_one({'name': request.form['add-meal']})
                    flash('Added meal "{}"'.format(request.form['add-meal']))
                else:
                    flash('Failed to add meal.')
            if exists(request.form, 'remove-tag'):  # Remove any deleted tags from their collections if they exist
                response = mongo.db.tags.delete_one({'name': request.form['remove-tag']}).deleted_count
                if response == 1:
                    flash('Deleted tag "{}"'.format(request.form['remove-tag']))
                else:
                    flash('Failed to delete tag.')
            if exists(request.form, 'remove-meal'):
                response = mongo.db.meals.delete_one({'name': request.form['remove-meal']}).deleted_count
                if response == 1:
                    flash('Deleted meal "{}"'.format(request.form['remove-meal']))
                else:
                    flash('Failed to delete meal.')

        all_tags = mongo.db.tags.find()
        all_meals = mongo.db.meals.find()
        return render_template('admin.html', username='Admin', tags=all_tags, meals=all_meals)


@app.route('/logout')
def logout():
    '''
    Logs user out and redirects to home. Clears session data.
    '''
    if session.get('username') is not None:
        session['username'] = None
        session['preferences'] = None
        session['exclusions'] = None
        flash("Successfully logged out.")
        return redirect(url_for('index'))
    return abort(403)


@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    '''
    User preferences page. Post route updates preferences.
    '''
    username = session.get('username')
    if session.get('username') is not None:
        all_tags = mongo.db.tags.find()
        if request.method == 'POST':
            tags = request.form.get('tags')
            exclude = request.form.get('exclude')
            if exists(tags):  # Check none of the tags are also in the exclusions
                tag_list = tags.split(' ')
            else:
                tag_list = []
            if exclude is not None:
                for tag in tag_list:
                    if tag != '' and tag in exclude:  # If they are don't change preferences
                        tags = None
                        exclude = None
                        flash('Can\'t exclude a tag that is already included in preferences!')
                        break

            if tags is not None or exclude is not None:  # If there are preferences to update, update the users document and session cookie
                mongo.db.users.update_one({'username': username}, {'$set': {'preferences': tags, 'exclusions': exclude}})
                session['preferences'] = tags
                session['exclusions'] = exclude
                flash('Preferences updated!')
        all_tags = list(mongo.db.tags.find())
        return render_template('preferences.html', username=username, all_tags=all_tags,
                               preferences=session.get('preferences'), exclusions=session.get('exclusions'))
    abort(403)  # If user not logged in return forbidden


@app.route('/users/<user>')
def user_page(user):
    '''
    User page. Displays details on a user and a list of recipes
    '''
    user_details = mongo.db.users.find_one({'username': user})
    if user_details is None:
        abort(404)
    user_details['joined'] = datetime.strptime(user_details['joined'], "%Y-%m-%d %H:%M:%S").strftime('%b \'%y')
    user_recipes = find_recipes(username=user, preferences='-1')
    return render_template('user.html', username=session.get('username'), user_details=user_details, user_recipes=user_recipes)


@app.route('/users')
def user_list():
    '''
    Users list, returns a list of users matching the current query
    '''
    query = {}
    if exists(request.args, 'following'):  # If looking for users followed by a user, search for users with their username in the followers list
        query['followers'] = request.args['following']
    if exists(request.args, 'followers'):  # If looking for users following a user, search for users with their username in the following list
        query['following'] = request.args['followers']
    no_users = mongo.db.users.count_documents(query)
    try:
        page = int(request.args.get('page', '1'))
    except ValueError:
        page = 1
    offset = (page - 1) * 10
    if page < 1 or (page != 1 and offset >= no_users):  # Check the page is within bounds
        abort(404)
    sort = request.args.get('sort', 'joined')  # If the query doesn't specify a sort or order default to joined descending
    order = request.args.get('order', '-1')
    try:
        order = int(order)
    except ValueError:
        order = -1
    users = mongo.db.users.find(query, {'username': 1, 'follower-count': 1, 'following-count': 1}).sort(sort, order).skip(offset).limit(10)  # Find user info for matching users
    current_query = request.args.to_dict()
    current_query.pop('page', '')  # Remove the page number from the current query before passing it to the template
    return render_template('users.html', username=session.get('username'), page=page, no_users=no_users,
                           users=users, current_query=current_query)


@app.route('/follow/<user>')
def follow(user):
    '''
    Adds or removes a logged in user to another users followers
    '''
    followee = mongo.db.users.find_one({'username': user}, {'followers': 1})
    if followee is None:
        return abort(404)
    follower = session.get('username')
    if follower is None:
        return abort(403)
    else:
        if follower not in followee.get('followers', []):
            mongo.db.users.update_one({'username': user}, {'$inc': {'follower-count': 1}, '$addToSet': {'followers': follower}})
            mongo.db.users.update_one({'username': follower}, {'$inc': {'following-count': 1}, '$addToSet': {'following': user}})
            following = True
        else:
            mongo.db.users.update_one({'username': user}, {'$inc': {'follower-count': -1}, '$pull': {'followers': follower}})
            mongo.db.users.update_one({'username': follower}, {'$inc': {'following-count': -1}, '$pull': {'following': user}})
            following = False
        if request.is_json:
            return jsonify(following=following)
        return redirect(url_for('recipes', username=user))


##################
# Recipes Routes #
##################

@app.route('/add-recipe', methods=['POST', 'GET'])
def add_recipe():
    '''
    Add new recipe page, or forks an existing one if the fork query is supplied. Post route adds teh recipe
    '''
    if session.get('username') is None:
        return abort(403)

    action = 'Add'
    if request.method == 'POST':
        recipe_data = request.form.to_dict()
        if exists(recipe_data, 'title') and exists(recipe_data, 'ingredients') and exists(recipe_data, 'methods'):  # If valida data has been supplied
            recipe_data['urn'] = '-'.join(findall('[a-z-]+', recipe_data['title'].lower()))  # Create a slug/urn from the title
            count = mongo.db.recipes.count_documents({'urn': {'$regex': '^' + recipe_data['urn'] + '[0-9]*'}})  # Count how many of that slug exists
            if count != 0:  # if one or more already exist, add the number onto the slug
                recipe_data['urn'] += str(count)
            recipe_data['username'] = session.get('username')
            recipe_data['date'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            recipe_data = create_recipe_data(recipe_data)

            if recipe_data.get('parent') is not None:  # If this is a fork, look for the parent, check the new recipe has a new name, and add the fork to the parent recipe
                parent = mongo.db.recipes.find_one({'urn': recipe_data['parent']}, {'title': 1})
                if parent is not None:
                    parent_title = parent.get('title')
                    recipe_data['parent-title'] = parent.get('title')
                    if parent_title == recipe_data['title']:
                        flash('Forked recipes must have a different title.')
                        return prepare_recipe_template(action, recipe_data)
                    else:
                        mongo.db.recipes.update_one({'urn': recipe_data['parent']},
                                                    {'$addToSet': {'children': {'urn': recipe_data['urn'],
                                                                                'title': recipe_data['title']}}})
                else:
                    recipe_data['parent'] = None
                    flash('Parent recipe does not exist!')
            mongo.db.recipes.insert_one(recipe_data)
            mongo.db.users.update_one({'username': recipe_data['username']}, {'$inc': {'recipe-count': 1}})
            flash('Recipe "{}" successfully created.'.format(recipe_data['title']))
            return redirect(url_for('recipe', urn = recipe_data['urn']))
        else:
            flash('Failed to add recipe!')
    elif request.args.get('fork') is not None:  # If this is a fork, find the parent and add its recipe data to the template
        action = 'Fork'
        parent = request.args.get('fork')
        recipe_data = mongo.db.recipes.find_one({'urn': parent},
                                                {'title': 1, 'ingredients': 1, 'methods': 1, 'tags': 1,
                                                'meals': 1, 'prep-time': 1, 'cook-time': 1, 'image': 1})
        if recipe_data is not None and not recipe_data.get('deleted', False):
            recipe_data['parent'] = parent
            if recipe_data.get('image') is not None:
                recipe_data['old-image'] = recipe_data['image']
        else:
            flash('Could not fork recipe. Failed to find parent!')
    else:
        recipe_data = None

    return prepare_recipe_template(action, recipe_data)


@app.route('/edit-recipe/<urn>', methods=['POST', 'GET'])
def edit_recipe(urn):
    '''
    Edit recipe page. Post route updates recipe.
    '''
    recipe_data = mongo.db.recipes.find_one({'urn': urn}, {'_id': -1, 'title': 1, 'username': 1, 'ingredients': 1, 'methods': 1,
                                                           'prep-time': 1, 'cook-time': 1, 'tags': 1, 'meals': 1, 'image': 1, 'deleted': 1})
    username = session.get('username')
    action = 'Edit'
    if recipe_data is None or recipe_data.get('deleted', False):
        abort(404)
    elif username == recipe_data['username'] or username == 'Admin':  # Only the author and admins can edit a recipe
        if request.method == 'POST':
            updated_recipe = request.form.to_dict()
            if exists(updated_recipe, 'title') and exists(updated_recipe, 'ingredients') and exists(updated_recipe, 'methods'):  # Verify recipe and update
                updated_recipe['urn'] = urn
                updated_recipe = create_recipe_data(updated_recipe)
                updated_recipe.pop('urn', '')
                mongo.db.recipes.update_one({'urn': urn}, {'$set': updated_recipe})
                flash('Successfully edited recipe!')
                return redirect(url_for('recipe', urn=urn))
        else:
            if recipe_data.get('image', '') != '':  # pass the recipes current image to the template as old recipe
                recipe_data['old-image'] = recipe_data['image']
            return prepare_recipe_template(action, recipe_data, urn=urn)
    else:
        abort(403)


@app.route('/delete-recipe/<urn>', methods=['GET', 'POST'])
def delete_recipe(urn):
    '''
    Delete recipe page. Post route deletes recipe.
    '''
    recipe_data = mongo.db.recipes.find_one({'urn': urn}, {'title': 1, 'username': 1, 'parent': 1, 'children': 1})
    username = session.get('username')
    if recipe_data is None:
        abort(404)
    elif username == recipe_data['username'] or username == 'Admin':  # Only the autor and admins can delete
        if request.method == 'POST':  # Delete recipe and update authors recipe count, and remove references from parents and children
            if request.form.get('confirm') == recipe_data['title']:
                mongo.db.recipes.replace_one({'urn': urn}, {'urn': urn, 'deleted': True})
                mongo.db.users.update_one({'username': recipe_data['username']}, {'$inc': {'recipe-count': -1}})
                if recipe_data.get('parent') is not None:
                    mongo.db.recipes.update_one({'urn': recipe_data['parent']},
                                                {'$pull': {'children': {'urn': urn, 'title': recipe_data['title']}}})
                if recipe_data.get('children') is not None:
                    mongo.db.recipes.update_many({'parent': urn}, {'$set': {'parent': None}})
                flash('Successfully deleted recipe "{}".'.format(recipe_data['title']))
                return redirect(url_for('index'))
            else:
                flash('Failed to delete recipe "{}".'.format(recipe_data['title']))
        return render_template('delete-recipe.html', title=recipe_data['title'], title_pattern=re_escape(recipe_data['title']),
                               urn=urn, username=username)
    else:
        abort(403)


@app.route('/recipes')
def recipes():
    '''
    Recipes list page. returns a list of recipes matching the query.
    '''
    preferences = session.get('preferences', '')
    exclusions = session.get('exclusions', '')
    query_args = request.args.to_dict()
    results = find_recipes(**query_args)  # Pass the query to find recipes
    if query_args.get('following') is not None:  # Following overrides username as it uses the same field
        query_args.pop('username', '')
    query_args.pop('page', '')  # Remove the page from the query, as it will be replaced in the template
    if exists(preferences):  # Add preferences and exclusions to query string
        tags = query_args.pop('tags', '')
        if tags != '':
            tags += ' ' + preferences
        else:
            tags = preferences
        query_args['tags'] = tags
    if exists(exclusions):
        exclude = query_args.pop('exclude', '')
        if exclude != '':
            exclude += ' ' + exclusions
        else:
            exclude = exclusions
        query_args['exclude'] = exclude
    if query_args.get('forks', '') != '':  # If searching for forks, get parent title to pass to template
        parent_title = mongo.db.recipes.find_one({'urn': query_args['forks']}, {'title': 1}).get('title')
    else:
        parent_title = None

    all_tags = list(mongo.db.tags.find())
    all_meals = mongo.db.meals.find()

    return render_template('recipes.html', current_query=query_args, username=session.get('username'),
                           parent_title=parent_title, all_meals=all_meals, all_tags=all_tags, **results)


@app.route('/recipes/<urn>')
def recipe(urn):
    '''
    Individual recipe page
    '''
    recipe = mongo.db.recipes.find_one({'urn': urn})
    favourite = None
    if recipe is None or recipe.get('deleted', False):
        abort(404)
    else:  # If recipe exists, prepare it for the template, and check if the user has favourited it.
        username = session.get('username')
        if recipe['username'] != username:
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'views': 1}})
            if username is not None:
                favourite = username in recipe.get('favouriting-users', [])
        recipe['ingredients'] = recipe['ingredients'].split('\n')
        recipe['methods'] = recipe['methods'].split('\n')
        recipe['date'] = datetime.strptime(recipe['date'], "%Y-%m-%d %H:%M:%S").strftime('%a %d %b \'%y')
        recipe['prep-time'] = hours_mins_to_string(recipe['prep-time'])
        recipe['cook-time'] = hours_mins_to_string(recipe['cook-time'])
        if recipe.get('children') is not None:
            recipe['forks'] = len(recipe['children'])
    return render_template('recipe.html', recipe=recipe, urn=urn, username=username, favourite=favourite)


@app.route('/recipes/<urn>/favourite')
def favourite_recipe(urn):
    '''
    Add or remove a recipe to a users favourites
    '''
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'username': 1, 'favouriting-users': 1})
    if recipe is None or recipe.get('deleted', False):
        abort(404)
    username = session.get('username')
    if username is None or username == recipe.get('username', username):
        abort(403)
    else:
        if username in recipe.get('favouriting-users', []):  # If a user is in the list of favouriting users, remove them
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'favourites': -1}, '$pull': {'favouriting-users': username}})
            favourite = False
        else:  # Otheriwse add them
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'favourites': 1}, '$addToSet': {'favouriting-users': username}})
            favourite = True
    if request.is_json:
        return jsonify(favourite=favourite)
    else:
        return redirect(url_for('recipe', urn=urn))


@app.route('/recipes/<urn>/feature')
def feature_recipe(urn):
    '''
    Admin user adds or removes featured flag to a recipe.
    '''
    if session.get('username') != 'Admin':
        abort(403)
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'featured': 1, 'deleted': 1})
    if recipe is None or recipe.get('deleted', False):
        abort(404)
    if recipe.get('featured') is None:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        mongo.db.recipes.update_one({'urn': urn}, {'$set': {'featured': now}})
        feature = True
    else:
        mongo.db.recipes.update_one({'urn': urn}, {'$unset': {'featured': ''}})
        feature = False
    if request.is_json:
        return jsonify(feature=feature)
    else:
        return redirect(url_for('recipe', urn=urn))


@app.route('/recipes/<urn>/comments', methods=['POST', 'GET'])
def comments(urn):
    '''
    Comments page. Post route adds comment.
    '''
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'username': 1, 'title': 1, 'comment-count': 1, 'comments': 1})
    username = session.get('username')
    if recipe is None or recipe.get('deleted', False):
        abort(404)
    if request.method == 'POST':
        if username is None:
            abort(403)
        else:
            if request.is_json:
                comment = request.json.get('comment', '')
            else:
                comment = request.form.get('comment', '')
            if comment != '' and comment is not None:
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                comment_doc = {'username': username, 'time': now, 'comment': comment}
                mongo.db.recipes.update_one({'urn': urn}, {'$addToSet': {'comments': comment_doc},
                                                           '$inc': {'comment-count': 1}})
                success = True
                if isinstance(recipe.get('comment-count'), int):
                    recipe['comment-count'] += 1
                else:
                    recipe['comment-count'] = 1
                if not isinstance(recipe.get('comments'), list):
                    recipe['comments'] = []
                recipe['comments'].append(comment_doc)
                flash('Added comment to {}'.format(recipe['title']))
            else:
                flash('Failed to add comment to {}'.format(recipe['title']))
                success = False
    else:
        success = None
    if request.is_json:
        for index, comment in enumerate(recipe.get('comments', [])):
            if not comment.get('deleted', False):
                comment['comment'] = escape(comment['comment'])
                comment['index'] = index
                if username == 'Admin' or username == comment['username']:
                    comment['delete'] = True
        return jsonify(comments=recipe.get('comments', []), success=success, messages=get_flashed_messages())
    else:
        return render_template('comments.html', username=username, recipe=recipe, urn=urn)


@app.route('/recipes/<urn>/delete-comment', methods=['POST'])
def delete_comment(urn):
    '''
    Deletes a comment.
    '''
    username = session.get('username')
    if username is None:
        abort(403)
    else:
        try:
            if request.is_json:
                index = int(request.json.get('comment-index'))
            else:
                index = int(request.form.get('comment-index'))
        except ValueError:
            abort(403)
        recipe = mongo.db.recipes.find_one({'urn': urn}, {'comments': 1, 'deleted': 1})
        if recipe is None or recipe.get('deleted', False):
            abort(404)
        else:
            if len(recipe.get('comments', [])) <= index:  # If the index is out of bounds return forbidden
                abort(403)
            else:
                comment = recipe['comments'][index]
            if username == 'Admin' or username == comment['username']:  # If the user is admin, or the comment author, delete the comment
                mongo.db.recipes.update_one({'urn': urn}, {'$set': {'comments.{}'.format(index): {'deleted': True}},
                                                           '$inc': {'comment-count': -1}})  # Mark comment as deleted and reduce comment count
                if username == 'Admin':
                    flash('Successfully deleted comment from {}.'.format(comment['username']))
                else:
                    flash('Successfully deleted your comment.')
                if request.is_json:
                    return jsonify(success=True, index=index, messages=get_flashed_messages())
                else:
                    return redirect(url_for('comments', urn=urn))
            else:
                abort(403)


################
# Static pages #
################

@app.route('/cookies')
def cookies():
    return render_template('cookies.html', username=session.get('username'))


@app.route('/about')
def about():
    return render_template('about.html', username=session.get('username'))


######################
# Custom error pages #
######################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', username=session.get('username')), 404


@app.errorhandler(403)
def page_forbidden(e):
    return render_template('403.html', username=session.get('username')), 403


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', username=session.get('username')), 500


if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = os.environ.get('PORT'),
            debug = True)
