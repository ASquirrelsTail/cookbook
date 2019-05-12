import os
from re import match, findall
from datetime import datetime
from flask import Flask, render_template, request, flash, session, redirect, url_for, abort
from flask_pymongo import PyMongo

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


@app.route('/')
def index():
    return render_template('index.html', username=session.get('username'))


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
            return redirect(url_for('login'), code=307)

    return render_template('new-user.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if session.get('username') is not None:
        return redirect(url_for('index'))
    elif request.method == 'POST':
        username = request.form.get('username', '')
        if username != '' and mongo.db.logins.find_one({'username': username}):
            session['username'] = username
            flash('Successfully logged in as "{}".'.format(username))
            return redirect(url_for('index'))
        else:
            flash("Failed to log in, invalid username.")

    return render_template('login.html')


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
        parent = request.args.get('fork')
        recipe_data = mongo.db.recipes.find_one({'urn': parent},
                                                {'title': 1, 'ingredients': 1, 'methods': 1, 'tags': 1,
                                                'meals': 1, 'prep-time': 1, 'cook-time': 1})
        if recipe_data is not None:
            recipe_data['parent'] = parent
            recipe_data['prep-time'] = recipe_data['prep-time'].split(':')
            recipe_data['cook-time'] = recipe_data['cook-time'].split(':')
            if recipe_data.get('tags', '') != '':
                recipe_data['tags'] = '/'.join(recipe_data['tags'])
            if recipe_data.get('meals', '') != '':
                recipe_data['meals'] = '/'.join(recipe_data['meals'])
        else:
            flash('Could not fork recipe. Failed to find parent!')
    else:
        recipe_data = None

    all_tags = mongo.db.tags.find()
    all_meals = mongo.db.meals.find()
    return render_template('add-recipe.html', recipe=recipe_data, username=session.get('username'), tags=all_tags, meals=all_meals)


@app.route('/recipes/<urn>')
def recipe(urn):
    recipe = mongo.db.recipes.find_one({'urn': urn})
    if recipe is None:
        abort(404)
    else:
        if recipe['username'] != session['username']:
            mongo.db.recipes.update_one({'urn': urn}, {'$inc': {'views': 1}})
        recipe['ingredients'] = recipe['ingredients'].split('\n')
        recipe['methods'] = recipe['methods'].split('\n')
        recipe['date'] = datetime.strptime(recipe['date'], "%Y-%m-%d %H:%M:%S").strftime('%a %d %b \'%y')
        recipe['prep-time'] = hours_mins_to_string(recipe['prep-time'])
        recipe['cook-time'] = hours_mins_to_string(recipe['cook-time'])
        if recipe.get('children') is not None:
            recipe['forks'] = len(recipe['children'])
    return render_template('recipe.html', recipe=recipe, username=session.get('username'))


if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = os.environ.get('PORT'),
            debug = True)
