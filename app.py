import os
from re import match
from flask import Flask, render_template, request
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'cookbook'
app.config['MONGO_URI'] = os.getenv('MONGO_URI')

mongo = PyMongo(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/new-user', methods=['POST', 'GET'])
def new_user():
    if request.method == 'POST':
        username = request.form.get('username', '')
        # Regex snipped for allowed characters from https://stackoverflow.com/questions/89909/how-do-i-verify-that-a-string-only-contains-letters-numbers-underscores-and-da
        if (username != '' and match("^[A-Za-z0-9_-]*$", username) and
                mongo.db.logins.find_one({'username': username}) is None):
            mongo.db.logins.insert_one(request.form.to_dict())

    return render_template('new-user.html')


if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = os.environ.get('PORT'),
            debug = True)
