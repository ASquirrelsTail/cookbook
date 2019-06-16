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
app.config['MONGO_DBNAME'] = 'cookbook'
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.secret_key = os.getenv('SECRET_KEY')

mongo = PyMongo(app)


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


def find_recipes(page='1', tags=None, exclude=None, meals=None, username=None, forks=None, search=None, featured=None,
                 following=None, favourites=None, preferences=None, sort='views', order='-1', **kwargs):
    query = {}
    user = session.get('username')
    if preferences == '-1':
        user_preferences = None
        user_exclusions = None
    else:
        user_preferences = session.get('preferences')
        user_exclusions = session.get('exclusions')
    if tags is not None and tags != '' and user_preferences is not None and user_preferences != '':
            tags = tags + ' ' + user_preferences
    elif user_preferences is not None and user_preferences != '':
        tags = user_preferences
    if tags is not None and tags != '':
        if ' ' in tags:
            tags = tags.split(' ')
            query['tags'] = {'$all': tags}
        else:
            query['tags'] = {'$all': [tags]}

    if exclude is not None and exclude != '' and user_exclusions is not None and user_exclusions != '':
        exclude = exclude + ' ' + user_exclusions
    elif user_exclusions is not None and user_exclusions != '':
        exclude = user_exclusions

    if exclude is not None:
        if ' ' in exclude:
            exclude = exclude.split(' ')
            if query.get('tags'):
                query['tags']['$nin'] = exclude
            else:
                query['tags'] = {'$nin': exclude}
        else:
            if query.get('tags'):
                query['tags']['$nin'] = [exclude]
            else:
                query['tags'] = {'$nin': [exclude]}
    if query.get('tags'):
        for tag in query['tags'].get('$all', []):
            if tag in query['tags'].get('$nin', []):
                query['tags']['$nin'].remove(tag)

    if meals is not None and meals != '':
        meals = request.args['meals']
        if ' ' in meals:
            meals = meals.split(' ')
            query['meals'] = {'$all': meals}
        else:
            query['meals'] = meals
    if favourites is not None and user is not None:
        query['favouriting-users'] = user
    if following is not None:
        following_user = mongo.db.users.find_one({'username': user}, {'following': 1})
        if following_user is not None and isinstance(following_user.get('following'), list):
            query['username'] = {'$in': following_user['following']}
        else:
            if page != '1':
                abort(404)
            else:
                return {'recipes': [], 'no_recipes': 0, 'page': 1}
    elif username is not None and username != '':
        query['username'] = username
    if forks is not None and forks != '':
        query['parent'] = forks
    if featured is not None and featured != '':
        query['featured'] = {'$exists': True}
    if search is not None and search != '':
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

    order = int(order)
    if order != 1 and order != -1:
        order = -1
    try:
        page = int(page)
    except ValueError:
        page = 1
    offset = (page - 1) * 10
    no_recipes = mongo.db.recipes.count_documents(query)
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
    if recipe_data.get('prep-time', '') != '' and recipe_data.get('cook-time', '') != '':
        prep_time = recipe_data['prep-time'].split(':')
        cook_time = recipe_data['cook-time'].split(':')
        mins = int(prep_time[1]) + int(cook_time[1])
        hours = int(prep_time[0]) + int(cook_time[0])
        hours += mins // 60
        mins = mins % 60
        recipe_data['total-time'] = "{:0>2}:{:0>2}".format(hours, mins)
    if recipe_data.get('tags', '') == '':
        recipe_data['tags'] = None
    else:
        recipe_data['tags'] = recipe_data.get('tags', '').split('/')
    if recipe_data.get('meals', '') == '':
        recipe_data['meals'] = None
    else:
        recipe_data['meals'] = recipe_data.get('meals', '').split('/')
    if recipe_data.get('image', '') != '':
        imageBytes = b64decode(recipe_data['image'])
        try:
            image = Image.open(BytesIO(imageBytes))
            if image.format == 'JPEG' and image.size == (1200, 700):
                filename = recipe_data['urn'] + '.jpg'
                if s3_bucket is not None:
                    s3.upload_fileobj(BytesIO(imageBytes), s3_bucket, filename)
                    config = s3._client_config
                    config.signature_version = botocore.UNSIGNED
                    recipe_data['image'] = boto3.client('s3', config=config) \
                        .generate_presigned_url('get_object', ExpiresIn=0,
                                                Params={'Bucket': s3_bucket, 'Key': filename})
                else:
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
            flash('Failed to upload image, incorrectly formatted file.')
    elif recipe_data.get('old-image', '') != '':
        recipe_data['image'] = recipe_data['old-image']
        recipe_data.pop('old-image', '')
    else:
        recipe_data['image'] = None
    return recipe_data


def prepare_recipe_template(action, recipe_data=None, urn=None):
    all_tags = mongo.db.tags.find()
    all_meals = mongo.db.meals.find()
    if recipe_data is not None:
        recipe_data['prep-time'] = recipe_data['prep-time'].split(':')
        recipe_data['cook-time'] = recipe_data['cook-time'].split(':')
        if recipe_data.get('tags', '') != '' and isinstance(recipe_data['tags'], list):
            recipe_data['tags'] = '/'.join(recipe_data['tags'])
        if recipe_data.get('meals', '') != '' and isinstance(recipe_data['meals'], list):
            recipe_data['meals'] = '/'.join(recipe_data['meals'])
        if recipe_data.get('image') is not None:
            recipe_data['old-image'] = recipe_data['image']

    return render_template('add-recipe.html', action=action, recipe=recipe_data, username=session.get('username'),
                           tags=all_tags, meals=all_meals, urn=urn)


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


@app.route('/new-user', methods=['POST', 'GET'])
def new_user():
    if session.get('username') is not None:
        return redirect(url_for('index'))
    elif request.method == 'POST':
        username = request.form.get('username', '')
        # Regex snippet for allowed characters from
        # https://stackoverflow.com/questions/89909/how-do-i-verify-that-a-string-only-contains-letters-numbers-underscores-and-da
        if username == '' or not match("^[A-Za-z0-9_-]*$", username):
            flash("Please enter a valid username!")
        elif mongo.db.logins.find_one({'username': username}) is not None:
            flash('Username "{}" is already taken, please choose another.'.format(username))
        else:
            mongo.db.logins.insert_one(request.form.to_dict())
            mongo.db.users.insert_one({'username': username, 'joined': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")})
            return redirect(url_for('login'), code=307)

    return render_template('new-user.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    target = None
    if session.get('username') is not None:
        return redirect(url_for('index'))
    elif request.method == 'POST':
        username = request.form.get('username', '')
        if username != '' and mongo.db.logins.find_one({'username': username}):
            session['username'] = username
            user_data = mongo.db.users.find_one({'username': username}, {'preferences': 1, 'exclusions': 1})
            session['preferences'] = user_data.get('preferences', None)
            session['exclusions'] = user_data.get('exclusions', None)
            flash('Successfully logged in as "{}".'.format(username))
            if request.form.get('target') is not None:
                return redirect(request.form.get('target'))
            return redirect(url_for('index'))
        else:
            flash("Failed to log in, invalid username.")
            target = request.form.get('target')

    return render_template('login.html', target=target)


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if session.get('username') != 'Admin':
        return abort(403)
    else:
        if request.method == 'POST':
            if request.form.get('add-tag', '') != '':
                if match('^[A-Za-z-]+$', request.form['add-tag']):
                    mongo.db.tags.insert_one({'name': request.form['add-tag']})
                    flash('Added tag "{}"'.format(request.form['add-tag']))
                else:
                    flash('Failed to add tag.')
            if request.form.get('add-meal', '') != '':
                if match('^[A-Za-z-]+$', request.form['add-meal']):
                    mongo.db.meals.insert_one({'name': request.form['add-meal']})
                    flash('Added meal "{}"'.format(request.form['add-meal']))
                else:
                    flash('Failed to add meal.')
            if request.form.get('remove-tag', '') != '':
                response = mongo.db.tags.delete_one({'name': request.form['remove-tag']}).deleted_count
                if response == 1:
                    flash('Deleted tag "{}"'.format(request.form['remove-tag']))
                else:
                    flash('Failed to delete tag.')
            if request.form.get('remove-meal', '') != '':
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
    if session.get('username') is not None:
        session['username'] = None
        session['preferences'] = None
        session['exclusions'] = None
        flash("Successfully logged out.")
        return redirect(url_for('index'))
    return abort(403)


@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    username = session.get('username')
    if session.get('username') is not None:
        all_tags = mongo.db.tags.find()
        if request.method == 'POST':
            tags = request.form.get('tags')
            exclude = request.form.get('exclude')
            if tags is not None and ' ' in tags:
                tag_list = tags.split(' ')
            else:
                tag_list = [tags]
            if tags is not None and exclude is not None:
                for tag in tag_list:
                    if tag is not None and tag != '' and tag in exclude:
                        tags = None
                        exclude = None
                        flash('Can\'t exclude a tag that is already included in preferences!')
                        break

            if tags is not None or exclude is not None:
                mongo.db.users.update_one({'username': username}, {'$set': {'preferences': tags, 'exclusions': exclude}})
                session['preferences'] = tags
                session['exclusions'] = exclude
                flash('Preferences updated!')
        all_tags = list(mongo.db.tags.find())
        return render_template('preferences.html', username=username, all_tags=all_tags,
                               preferences=session.get('preferences'), exclusions=session.get('exclusions'))
    abort(403)


@app.route('/users/<user>')
def user_page(user):
    user_details = mongo.db.users.find_one({'username': user})
    if user_details is None:
        abort(404)
    user_details['joined'] = datetime.strptime(user_details['joined'], "%Y-%m-%d %H:%M:%S").strftime('%b \'%y')
    user_recipes = find_recipes(username=user, preferences='-1')
    return render_template('user.html', username=session.get('username'), user_details=user_details, user_recipes=user_recipes)


@app.route('/users')
def user_list():
    query = {}
    if request.args.get('following', '') != '':
        query['followers'] = request.args['following']
    if request.args.get('followers', '') != '':
        query['following'] = request.args['followers']
    no_users = mongo.db.users.count_documents(query)
    try:
        page = int(request.args.get('page', '1'))
    except ValueError:
        page = 1
    offset = (page - 1) * 10
    if page < 1 or (page != 1 and offset >= no_users):
        abort(404)  # Out of bounds error
    sort = request.args.get('sort', 'joined')
    order = request.args.get('order', '-1')
    try:
        order = int(order)
    except ValueError:
        order = -1
    users = mongo.db.users.find(query, {'username': 1}).sort(sort, order).skip(offset).limit(10)
    current_query = request.args.to_dict()
    current_query.pop('page', '')
    return render_template('users.html', username=session.get('username'), page=page, no_users=no_users,
                           users=users, current_query=current_query)


@app.route('/follow/<user>')
def follow(user):
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


@app.route('/add-recipe', methods=['POST', 'GET'])
def add_recipe():
    if session.get('username') is None:
        return abort(403)

    action = 'Add'
    if request.method == 'POST':
        recipe_data = request.form.to_dict()
        if (recipe_data.get('title', '') != '' and
                recipe_data.get('ingredients', '') != '' and
                recipe_data.get('methods', '') != ''):
            recipe_data['urn'] = '-'.join(findall('[a-z-]+', recipe_data['title'].lower()))
            count = mongo.db.recipes.count_documents({'urn': {'$regex': '^' + recipe_data['urn'] + '[0-9]*'}})
            if count != 0:
                recipe_data['urn'] += '{}'.format(count)
            recipe_data['username'] = session.get('username')
            recipe_data['date'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            recipe_data = create_recipe_data(recipe_data)

            if recipe_data.get('parent') is not None:
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
    elif request.args.get('fork') is not None:
        action = 'Fork'
        parent = request.args.get('fork')
        recipe_data = mongo.db.recipes.find_one({'urn': parent},
                                                {'title': 1, 'ingredients': 1, 'methods': 1, 'tags': 1,
                                                'meals': 1, 'prep-time': 1, 'cook-time': 1, 'image': 1})
        if recipe_data is not None:
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
    recipe_data = mongo.db.recipes.find_one({'urn': urn}, {'_id': -1, 'title': 1, 'username': 1, 'ingredients': 1, 'methods': 1,
                                                           'prep-time': 1, 'cook-time': 1, 'tags': 1, 'meals': 1, 'image': 1})
    username = session.get('username')
    action = 'Edit'
    if recipe_data is None:
        abort(404)
    elif username == recipe_data['username'] or username == 'Admin':
        if request.method == 'POST':
            updated_recipe = request.form.to_dict()
            if (updated_recipe.get('title', '') != '' and
                    updated_recipe.get('ingredients', '') != '' and
                    updated_recipe.get('methods', '') != ''):
                updated_recipe['urn'] = urn
                updated_recipe = create_recipe_data(updated_recipe)
                updated_recipe.pop('urn', '')
                mongo.db.recipes.update_one({'urn': urn}, {'$set': updated_recipe})
                flash('Successfully edited recipe!')
                return redirect(url_for('recipe', urn=urn))
        else:
            if recipe_data.get('image', '') != '':
                recipe_data['old-image'] = recipe_data['image']
            return prepare_recipe_template(action, recipe_data, urn=urn)
    else:
        abort(403)


@app.route('/delete-recipe/<urn>', methods=['GET', 'POST'])
def delete_recipe(urn):
    recipe_data = mongo.db.recipes.find_one({'urn': urn}, {'title': 1, 'username': 1, 'parent': 1, 'children': 1})
    username = session.get('username')
    if recipe_data is None:
        abort(404)
    elif username == recipe_data['username'] or username == 'Admin':
        if request.method == 'POST':
            if request.form.get('confirm') == recipe_data['title']:
                mongo.db.recipes.delete_one({'urn': urn})
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
    preferences = session.get('preferences', '')
    exclusions = session.get('exclusions', '')
    query_args = request.args.to_dict()
    results = find_recipes(**query_args)
    if query_args.get('following') is not None:
        query_args.pop('username', '')
    query_args.pop('page', '')
    if preferences is not None and preferences != '':
        tags = query_args.pop('tags', '')
        if tags != '':
            tags += ' ' + preferences
        else:
            tags = preferences
        query_args['tags'] = tags
    if exclusions is not None and exclusions != '':
        exclude = query_args.pop('exclude', '')
        if exclude != '':
            exclude += ' ' + exclusions
        else:
            exclude = exclusions
        query_args['exclude'] = exclude
    if query_args.get('forks', '') != '':
        parent_title = mongo.db.recipes.find_one({'urn': query_args['forks']}, {'title': 1}).get('title')
    else:
        parent_title = None

    all_tags = list(mongo.db.tags.find())
    all_meals = mongo.db.meals.find()

    return render_template('recipes.html', current_query=query_args, username=session.get('username'),
                           parent_title=parent_title, all_meals=all_meals, all_tags=all_tags, **results)


@app.route('/recipes/<urn>')
def recipe(urn):
    recipe = mongo.db.recipes.find_one({'urn': urn})
    favourite = None
    if recipe is None:
        abort(404)
    else:
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
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'username': 1, 'favouriting-users': 1})
    if recipe is None:
        abort(404)
    username = session.get('username')
    if username is None or username == recipe.get('username', username):
        abort(403)
    else:
        if username in recipe.get('favouriting-users', []):
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'favourites': -1}, '$pull': {'favouriting-users': username}})
            favourite = False
        else:
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'favourites': 1}, '$addToSet': {'favouriting-users': username}})
            favourite = True
    if request.is_json:
        return jsonify(favourite=favourite)
    else:
        return redirect(url_for('recipe', urn=urn))


@app.route('/recipes/<urn>/feature')
def feature_recipe(urn):
    if session.get('username') != 'Admin':
        abort(403)
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'featured': 1})
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
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'username': 1, 'title': 1, 'comment-count': 1, 'comments': 1})
    username = session.get('username')
    if recipe is None:
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
        for comment in recipe.get('comments', []):
            comment['comment'] = escape(comment['comment'])
            if username == 'Admin' or username == comment['username']:
                comment['delete'] = True
        return jsonify(comments=recipe.get('comments', []), success=success, messages=get_flashed_messages())
    else:
        return render_template('comments.html', username=username, recipe=recipe, urn=urn)


@app.route('/recipes/<urn>/delete-comment', methods=['POST'])
def delete_comment(urn):
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
        comment = mongo.db.recipes.find_one({'urn': urn}, {'comments': {'$slice': [index, 1]}}).get('comments')
        if len(comment) != 1:
            abort(403)
        else:
            comment = comment[0]
        if username == 'Admin' or username == comment['username']:
            mongo.db.recipes.update_one({'urn': urn}, {'$pull': {'comments': comment}, '$inc': {'comment-count': -1}})
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


# Static pages #

@app.route('/cookies')
def cookies():
    return render_template('cookies.html', username=session.get('username'))


@app.route('/about')
def about():
    return render_template('about.html', username=session.get('username'))


# Custom error pages #

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
