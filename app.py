import os
from re import match, findall
from flask import Flask, render_template, request, flash, session, redirect, url_for, abort, escape
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'cookbook'
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.secret_key = os.getenv('SECRET_KEY')

mongo = PyMongo(app)


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
    elif request.method == 'POST':
        if (request.form.get('title') is not None and
                request.form.get('ingredients') is not None and
                request.form.get('methods') is not None):
            recipe_data = request.form.to_dict()
            recipe_data['username'] = session.get('username')
            recipe_data['urn'] = '-'.join(findall('[a-z-]+', recipe_data['title'].lower()))
            count = mongo.db.recipes.count_documents({'urn': {'$regex': '^' + recipe_data['urn'] + '[0-9]*'}})
            if count != 0:
                recipe_data['urn'] += '{}'.format(count)
            mongo.db.recipes.insert_one(recipe_data)
            flash('Recipe "{}" successfully created.'.format(recipe_data['title']))
            return redirect(url_for('recipe', urn = recipe_data['urn']))
        else:
            flash('Failed to add recipe!')
    return render_template('add-recipe.html')


@app.route('/recipes/<urn>')
def recipe(urn):
    recipe = mongo.db.recipes.find_one_and_update({'urn': urn}, {'$inc': {'views': 1}})
    if recipe is None:
        abort(404)
    else:
        recipe['ingredients'] = recipe['ingredients'].split('\n')
        recipe['methods'] = recipe['methods'].split('\n')
    return render_template('recipe.html', recipe=recipe)


if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = os.environ.get('PORT'),
            debug = True)
