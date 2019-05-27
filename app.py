import os
from re import match, findall, sub, split, escape as re_escape
from datetime import datetime
from flask import Flask, render_template, request, flash, session, redirect, url_for, abort
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


def find_recipes(page='1', tags=None, meals=None, username=None, forks=None, search=None, featured=None, sort='views', order='-1'):
    query = {}

    if tags is not None and tags != '':
        if ' ' in tags:
            tags = tags.split(' ')
            query['tags'] = {'$all': tags}
        else:
            query['tags'] = tags
    if meals is not None and meals != '':
        meals = request.args['meals']
        if ' ' in meals:
            meals = meals.split(' ')
            query['meals'] = {'$all': meals}
        else:
            query['meals'] = meals
    if username is not None and username != '':
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
    page = int(page)
    offset = (page - 1) * 10
    no_recipes = mongo.db.recipes.count_documents(query)
    if page < 1 or (page != 1 and offset >= no_recipes):
        abort(404)  # Out of bounds error
    if no_recipes > 0:
        recipes = (
            mongo.db.recipes.find(query, {'urn': 1, 'title': 1, 'username': 1, 'image': 1})
            .sort(sort, order)
            .skip(offset)
            .limit(10)
        )
    else:
        recipes = []

    return {'recipes': recipes, 'no_recipes': no_recipes, 'page': page}


@app.route('/')
def index():
    featured_recipes = find_recipes(featured='1', sort='featured', order='-1').get('recipes')
    recent_recipes = find_recipes(sort='date', order='-1')
    recent_recipes['query'] = {'sort': 'date', 'order': '-1'}
    popular_recipes = find_recipes(sort='favourites', order='-1')
    popular_recipes['query'] = {'sort': 'favourites', 'order': '-1'}
    return render_template('index.html', username=session.get('username'), featured_recipes=featured_recipes,
                           recent_recipes=recent_recipes, popular_recipes=popular_recipes)


@app.route('/new-user', methods=['POST', 'GET'])
def new_user():
    if session.get('username') is not None:
        return redirect(url_for('index'))
    elif request.method == 'POST':
        username = request.form.get('username', '')
        # Regex snippet for allowed characters from https://stackoverflow.com/questions/89909/how-do-i-verify-that-a-string-only-contains-letters-numbers-underscores-and-da
        if username == '' or not match("^[A-Za-z0-9_-]*$", username):
            flash("Please enter a valid username!")
        elif mongo.db.logins.find_one({'username': username}) is not None:
            flash('Username "{}" is already taken, please choose another.'.format(username))
        else:
            mongo.db.logins.insert_one(request.form.to_dict())
            mongo.db.users.insert_one({'username': username})
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
        flash("Successfully logged out.")
        return redirect(url_for('index'))
    return abort(403)


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
            recipe_data['username'] = session.get('username')
            recipe_data['date'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            recipe_data['urn'] = '-'.join(findall('[a-z-]+', recipe_data['title'].lower()))
            if recipe_data.get('tags', '') != '':
                recipe_data['tags'] = recipe_data['tags'].split('/')
            if recipe_data.get('meals', '') != '':
                recipe_data['meals'] = recipe_data['meals'].split('/')
            if recipe_data.get('image', '') != '':
                imageBytes = b64decode(recipe_data['image'])
                try:
                    image = Image.open(BytesIO(imageBytes))
                    if image.format == 'JPEG' and image.size == (1200, 700):
                        filename = recipe_data['urn'] + '.jpg'
                        s3.upload_fileobj(BytesIO(imageBytes), s3_bucket, filename)
                        config = s3._client_config
                        config.signature_version = botocore.UNSIGNED

                        recipe_data['image'] = boto3.client('s3', config=config).generate_presigned_url('get_object', ExpiresIn=0, Params={'Bucket': s3_bucket, 'Key': filename})
                    else:
                        recipe_data.pop('image', '')
                        flash('Failed to upload image.')
                except IOError:
                    recipe_data.pop('image', '')
                    flash('Failed to upload image, incorrectly formatted file.')
            elif recipe_data.get('old-image', '') != '':
                recipe_data['image'] = recipe_data['old-image']
                recipe_data.pop('old-image', '')
            count = mongo.db.recipes.count_documents({'urn': {'$regex': '^' + recipe_data['urn'] + '[0-9]*'}})
            if count != 0:
                recipe_data['urn'] += '{}'.format(count)
            if recipe_data.get('parent') is not None:
                parent = mongo.db.recipes.find_one({'urn': recipe_data['parent']}, {'title': 1})
                if parent is not None:
                    parent_title = parent.get('title')
                    if parent_title == recipe_data['title']:
                        flash('Forked recipes must have a different title.')
                        all_tags = mongo.db.tags.find()
                        all_meals = mongo.db.meals.find()
                        recipe_data['prep-time'] = recipe_data['prep-time'].split(':')
                        recipe_data['cook-time'] = recipe_data['cook-time'].split(':')
                        if recipe_data.get('tags', '') != '':
                            recipe_data['tags'] = '/'.join(recipe_data['tags'])
                        if recipe_data.get('meals', '') != '':
                            recipe_data['meals'] = '/'.join(recipe_data['meals'])
                        return render_template('add-recipe.html', recipe=recipe_data, username=session.get('username'), tags=all_tags, meals=all_meals)
                    else:
                        mongo.db.recipes.update_one({'urn': recipe_data['parent']},
                                                    {'$addToSet': {'children': {'urn': recipe_data['urn'],
                                                                                'title': recipe_data['title']}}})
                else:
                    recipe_data['parent'] = None
                    flash('Parent recipe does not exist!')
            mongo.db.recipes.insert_one(recipe_data)
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
            recipe_data['prep-time'] = recipe_data['prep-time'].split(':')
            recipe_data['cook-time'] = recipe_data['cook-time'].split(':')
            if recipe_data.get('tags', '') != '' and isinstance(recipe_data['tags'], list):
                recipe_data['tags'] = '/'.join(recipe_data['tags'])
            if recipe_data.get('meals', '') != '' and isinstance(recipe_data['meals'], list):
                recipe_data['meals'] = '/'.join(recipe_data['meals'])
            if recipe_data.get('image') is not None:
                recipe_data['old-image'] = recipe_data['image']
        else:
            flash('Could not fork recipe. Failed to find parent!')
    else:
        recipe_data = None

    all_tags = mongo.db.tags.find()
    all_meals = mongo.db.meals.find()
    return render_template('add-recipe.html', action=action, recipe=recipe_data, username=session.get('username'), tags=all_tags, meals=all_meals)


@app.route('/edit-recipe/<urn>', methods=['POST', 'GET'])
def edit_recipe(urn):
    recipe_data = mongo.db.recipes.find_one({'urn': urn}, {'title': 1, 'username': 1, 'ingredients': 1, 'methods': 1,
                                                           'prep-time': 1, 'cook-time': 1, 'tags': 1, 'meals': 1, 'image': 1})
    username = session.get('username')
    if recipe_data is None:
        abort(404)
    elif username == recipe_data['username'] or username == 'Admin':
        if request.method == 'POST':
            updated_recipe = request.form.to_dict()
            if (updated_recipe.get('title', '') != '' and
                    updated_recipe.get('ingredients', '') != '' and
                    updated_recipe.get('methods', '') != '' and
                    updated_recipe.get('prep-time', '') != '' and
                    updated_recipe.get('cook-time', '') != ''):
                if updated_recipe.get('tags', '') == '':
                    updated_recipe['tags'] = None
                else:
                    updated_recipe['tags'] = updated_recipe.get('tags', '').split('/')
                if updated_recipe.get('meals', '') == '':
                    updated_recipe['meals'] = None
                else:
                    updated_recipe['meals'] = updated_recipe.get('meals', '').split('/')
                if updated_recipe.get('image', '') != '':
                    imageBytes = b64decode(updated_recipe['image'])
                    try:
                        image = Image.open(BytesIO(imageBytes))
                        if image.format == 'JPEG' and image.size == (1200, 700):
                            filename = urn + '.jpg'
                            s3.upload_fileobj(BytesIO(imageBytes), s3_bucket, filename)
                            config = s3._client_config
                            config.signature_version = botocore.UNSIGNED

                            updated_recipe['image'] = boto3.client('s3', config=config).generate_presigned_url('get_object', ExpiresIn=0, Params={'Bucket': s3_bucket, 'Key': filename})
                        else:
                            updated_recipe.pop('image', '')
                            flash('Failed to upload image.')
                    except IOError:
                        updated_recipe.pop('image', '')
                        flash('Failed to upload image, incorrectly formatted file.')
                elif updated_recipe.get('old-image', '') != '':
                    updated_recipe['image'] = updated_recipe['old-image']
                else:
                    updated_recipe['image'] = None

                mongo.db.recipes.update_one({'urn': urn},
                                            {'$set': {'title': updated_recipe['title'], 'ingredients': updated_recipe['ingredients'],
                                                      'methods': updated_recipe['methods'], 'prep-time': updated_recipe['prep-time'],
                                                      'cook-time': updated_recipe['cook-time'], 'tags': updated_recipe['tags'],
                                                      'meals': updated_recipe['meals'], 'image': updated_recipe['image']}})
                flash('Successfully edited recipe!')
                return redirect(url_for('recipe', urn=urn))
        else:
            all_tags = mongo.db.tags.find()
            all_meals = mongo.db.meals.find()
            recipe_data['prep-time'] = recipe_data['prep-time'].split(':')
            recipe_data['cook-time'] = recipe_data['cook-time'].split(':')
            if recipe_data.get('tags', '') != '' and isinstance(recipe_data['tags'], list):
                recipe_data['tags'] = '/'.join(recipe_data['tags'])
            if recipe_data.get('meals', '') != '' and isinstance(recipe_data['meals'], list):
                recipe_data['meals'] = '/'.join(recipe_data['meals'])
            if recipe_data.get('image', '') != '':
                recipe_data['old-image'] = recipe_data['image']
            return render_template('add-recipe.html', action='Edit', recipe=recipe_data, username=username, tags=all_tags, meals=all_meals)
    else:
        abort(403)


@app.route('/delete-recipe/<urn>', methods=['GET', 'POST'])
def delete_recipe(urn):
    recipe_data = mongo.db.recipes.find_one({'urn': urn}, {'title': 1, 'username': 1})
    username = session.get('username')
    if recipe_data is None:
        abort(404)
    elif username == recipe_data['username'] or username == 'Admin':
        if request.method == 'POST':
            if request.form.get('confirm') == recipe_data['title']:
                mongo.db.recipes.delete_one({'urn': urn})
                flash('Successfully deleted recipe "{}".'.format(recipe_data['title']))
                return redirect(url_for('index'))
            else:
                flash('Failed to delete recipe "{}".'.format(recipe_data['title']))
        return render_template('delete-recipe.html', title=recipe_data['title'], urn=urn, username=username)
    else:
        abort(403)


@app.route('/recipes')
def recipes():
    query_args = request.args.to_dict()
    results = find_recipes(**query_args)
    query_args.pop('page', '')

    all_tags = mongo.db.tags.find()
    all_meals = mongo.db.meals.find()

    return render_template('recipes.html', current_query=query_args, username=session.get('username'),
                           all_meals=all_meals, all_tags=all_tags, **results)


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
                favourite = mongo.db.users.find_one({'username': username, 'favourites': {'$in': [urn]}}, {'_id': 1})
        recipe['ingredients'] = recipe['ingredients'].split('\n')
        recipe['methods'] = recipe['methods'].split('\n')
        recipe['date'] = datetime.strptime(recipe['date'], "%Y-%m-%d %H:%M:%S").strftime('%a %d %b \'%y')
        recipe['prep-time'] = hours_mins_to_string(recipe['prep-time'])
        recipe['cook-time'] = hours_mins_to_string(recipe['cook-time'])
        if recipe.get('children') is not None:
            recipe['forks'] = len(recipe['children'])
    return render_template('recipe.html', recipe=recipe, username=username, favourite=favourite)


@app.route('/recipes/<urn>/favourite')
def favourite_recipe(urn):
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'username': 1})
    if recipe is None:
        abort(404)
    username = session.get('username')
    if username is None or username == recipe.get('username', username):
        abort(403)
    else:
        if urn in mongo.db.users.find_one({'username': username}, {'favourites': 1}).get('favourites', []):
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'favourites': -1}})
            mongo.db.users.update_one({'username': username}, {'$pull': {'favourites': urn}})
        else:
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'favourites': 1}})
            mongo.db.users.update_one({'username': username}, {'$addToSet': {'favourites': urn}})
    return redirect(url_for('recipe', urn=urn))


@app.route('/recipes/<urn>/feature')
def feature_recipe(urn):
    if session.get('username') != 'Admin':
        abort(403)
    recipe = mongo.db.recipes.find_one({'urn': urn}, {'featured': 1})
    if recipe.get('featured') is None:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        mongo.db.recipes.update_one({'urn': urn}, {'$set': {'featured': now}})
    else:
        mongo.db.recipes.update_one({'urn': urn}, {'$unset': {'featured': ''}})

    return redirect(url_for('recipe', urn=urn))


@app.route('/cookies')
def cookies():
    return render_template('cookies.html', username=session.get('username'))


@app.route('/about')
def about():
    return render_template('about.html', username=session.get('username'))


if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = os.environ.get('PORT'),
            debug = True)
