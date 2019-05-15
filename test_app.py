import os
import unittest
import app
import datetime
from flask import escape
from re import findall


def flask_test_client():
    '''
    Sets up flask testing client, changes MongoDB database to test database
    '''
    app.app.config['TESTING'] = True
    app.app.config['DEBUG'] = False
    # Use the test database URI instead of the default
    app.mongo = app.PyMongo(app.app, uri=os.getenv('MONGO_TEST_URI'))
    client = app.app.test_client()
    mongo = app.mongo

    return client, mongo


class TestClient(unittest.TestCase):
    '''
    Parent class with utility functions for all tests
    '''
    @classmethod
    def setUpClass(cls):
        cls.client, cls.mongo = flask_test_client()

    @classmethod
    def create_user(cls, username='TestUser'):
        '''
        Helper function to create a new user by sending a POST request to /new-user
        '''
        return cls.client.post('/new-user', follow_redirects=True,
                               data={'username': username})

    @classmethod
    def login_user(cls, username='TestUser'):
        '''
        Helper function to log in user.
        '''
        return cls.client.post('/login', follow_redirects=True,
                               data={'username': username})

    @classmethod
    def logout_user(cls):
        '''
        Helper function to logout current user.
        '''
        cls.client.get('/logout', follow_redirects=True)

    @classmethod
    def submit_recipe(cls, title='Test Recipe', ingredients=['Test ingredient 1', 'Test ingredient 2'],
                      methods=['Add one to two.', 'Enjoy'], tags='', meals='', prep_time='00:01', cook_time='00:01', parent=None):
        '''
        Helper function to create a recipe.
        '''
        def join_if_array(input_list, string='\n'):
            if isinstance(input_list, list):
                return string.join(input_list)
            else:
                return input_list

        return cls.client.post('/add-recipe', follow_redirects=True,
                               data={'title': title, 'ingredients': join_if_array(ingredients), 'methods': join_if_array(methods),
                                     'tags': join_if_array(tags, '/'), 'meals': join_if_array(meals, '/'), 'prep-time': prep_time,
                                     'cook-time': cook_time, 'parent': parent})

    def test_home(self):
        '''
        The home page should return HTTP code 200 OK
        '''
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class TestUsers(TestClient):
    '''
    Class for testing the user creation and login pages
    '''
    def setUp(self):
        self.mongo.db.logins.delete_many({})
        self.logout_user()

    def test_new_user_page(self):
        '''
        The new-user page should return 200
        '''
        response = self.client.get('/new-user', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_create_new_user(self):
        '''
        Creating a new-user should return 200
        '''
        response = self.client.post('/new-user', follow_redirects=True,
                                    data={'username': 'TestUser'})
        self.assertEqual(response.status_code, 200)

    def test_create_new_user_adds_user(self):
        '''
        Creating a new user should add them to the logins collection
        '''
        username = 'TestUser'
        self.create_user(username)
        self.assertNotEqual(self.mongo.db.logins.find_one({'username': username}), None)

    def test_create_new_user_already_exists(self):
        '''
        Trying to create a new user that already exists should fail
        '''
        username = 'TestUser'
        self.create_user(username)
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.count_documents({'username': username}), 1)

    def test_create_new_user_missing_username(self):
        '''
        Trying to create a user with a blank username should fail
        '''
        username = ''
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.find_one({'username': username}), None)

        username = None
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.find_one({'username': username}), None)

    def test_create_new_user_invalid_username(self):
        '''
        Trying to create a user with username containing anything other than alphanumeric characters, dashes or underscores should fail
        '''
        username = ':D 8p >/'
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.find_one({'username': username}), None)

    def test_login_page(self):
        '''
        The login page should return 200 for users that are not logged in
        '''
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_login_user(self):
        '''
        A user that is successfully logged in should have their username saved to their session object
        '''
        username = 'TestUser'
        self.create_user(username)
        self.login_user(username)
        with self.client.session_transaction() as session:
            self.assertEqual(session.get('username'), username)

    def test_login_user_invalid_username(self):
        '''
        A user should not be able to log in if they don't exist
        '''
        username = 'NotARealUser'
        self.login_user(username)
        with self.client.session_transaction() as session:
            self.assertNotEqual(session.get('username'), username)

    def test_logged_in_user_cant_login(self):
        '''
        A user that is logged in should be redirected away from the login page
        '''
        username = 'TestUser'
        self.create_user(username)
        self.login_user(username)

        response = self.client.get('/login', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_cant_create_user(self):
        '''
        A user that is logged in should redirected away from the create new user page
        '''
        username = 'TestUser'
        self.create_user(username)
        self.login_user(username)

        response = self.client.get('/new-user', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_logout_not_logged_in(self):
        '''
        A user that is not logged in should not be able to access the logout page
        '''
        response = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(response.status_code, 403)

    def test_logout_when_logged_in(self):
        '''
        A user that is logged in should be logged out by the logout page
        '''
        username = 'TestUser'
        self.create_user(username)
        self.login_user(username)
        self.client.get('/logout')
        with self.client.session_transaction() as session:
            self.assertEqual(session.get('username'), None)


class TestAddRecipe(TestClient):
    '''
    Class for testing the add-recipe page
    '''
    def setUp(self):
        # Delete all records from the user collection and create test user
        self.mongo.db.logins.delete_many({})
        self.logout_user()
        self.create_user()
        self.login_user()
        # Delete all records from the recipe collection
        self.mongo.db.recipes.delete_many({})

    def test_add_recipe_page(self):
        '''
        The recipe creation page should return 200 for logged in users
        '''
        response = self.client.get('/add-recipe', follow_redirects=False)
        self.assertEqual(response.status_code, 200)

    def test_add_recipe_not_logged_in(self):
        '''
        A user that is not logged in should not be able to access the add recipe page
        '''
        self.logout_user()
        response = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(response.status_code, 403)

    def test_submit_recipe(self):
        '''
        Submitted recipes should be added to the recipes collection
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}), None)

    def test_submit_recipe_has_ingredients_methods_and_prep_times(self):
        '''
        Submitted recipes should have ingredients and methods
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        recipe_prep_time = '00:05'
        recipe_cook_time = '00:05'
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods, prep_time=recipe_prep_time, cook_time=recipe_cook_time)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('ingredients'), None)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('methods'), None)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('prep-time'), '00:05')
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('cook-time'), '00:05')

    def test_submit_recipe_has_tags_array(self):
        '''
        Submitted recipes with tags should store them as an array
        '''
        recipe_title = 'Vegan Pancakes'
        recipe_ingredients = ['Flour', 'Almond Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        recipe_tags = ['Vegan', 'Vegetarian', 'Dairy-Free', 'Egg-Free']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods, recipe_tags)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}.get('tags')), None)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('tags'), ['Vegan', 'Vegetarian', 'Dairy-Free', 'Egg-Free'])

    def test_submit_recipe_has_meals_array(self):
        '''
        Submitted recipes with meals should store them as an array
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        recipe_meals = ['Breakfast', 'Desert']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods, None, recipe_meals)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}.get('meals')), None)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('meals'), ['Breakfast', 'Desert'])

    def test_submit_recipe_has_username(self):
        '''
        Submitted recipes added to the recipes collection should include the username of the author
        '''
        username = 'TestUser'
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.create_user(username)
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('username'), username)

    def test_submit_recipe_has_time(self):
        '''
        Submitted recipes should have timestamp
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('date'), None)
        self.assertRegex(self.mongo.db.recipes.find_one({'title': recipe_title}).get('date', ''),
                         '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}')

    def test_submit_recipe_missing_fields(self):
        '''
        Submitted recipes without a title, ingredients or methods should should not be added
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(None, recipe_ingredients, recipe_methods)
        self.submit_recipe(recipe_title, None, recipe_methods)
        self.submit_recipe(recipe_title, recipe_ingredients, None)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}), None)

    def test_submit_recipe_missing_fields_preserves_input(self):
        '''
        Submitted recipes with missing fields returns the user to the add recipe page with inputs preserved
        '''
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        response = self.submit_recipe(None, recipe_ingredients, recipe_methods)
        self.assertIn(b'Cook until golden.', response.data)

    def test_submit_recipe_has_urn(self):
        '''
        Submitted recipes should have a Unique Resource Name
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('urn'), None)

    def test_submit_recipe_has_valid_urn(self):
        '''
        Submitted recipes should have a valid Unique Resource Name that only contains lowercase alphanumeric characters, underscores and dashes
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = ['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni']
        recipe_methods = ['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                          'Once mixture thickens add boiled macaroni.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotRegex(self.mongo.db.recipes.find_one({}).get('urn'), '[^a-z0-9_-]+')

    def test_submit_recipe_has_unique_urn(self):
        '''
        Submitted recipes should have a unique URN, even though titles can be identical
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = ['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni']
        recipe_methods = ['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                          'Once mixture thickens add boiled macaroni.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertEqual(self.mongo.db.recipes.count_documents({'urn': urn}), 1)

    def test_submit_recipe_fills_inputs_from_forked_recipe(self):
        '''
        Forking a recipe should return an add new recipe page with that recipe filled in
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = ['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni']
        recipe_methods = ['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                          'Once mixture thickens add boiled macaroni.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/add-recipe?fork={}'.format(urn))
        self.assertIn(b'Once mixture thickens add boiled macaroni.', response.data)

    def test_submit_recipe_has_parent_hidden_field_from_forked_recipe(self):
        '''
        Forking a recipe should return an add new recipe page with that recipes urn in a hidden 'parent' field
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = ['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni']
        recipe_methods = ['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                          'Once mixture thickens add boiled macaroni.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/add-recipe?fork={}'.format(urn))
        self.assertIn(str.encode('<input type="hidden" name="parent" value="{}">'.format(urn)), response.data)

    def test_forked_recipes_reference_parent(self):
        '''
        Forking a recipe should return an add new recipe page with that recipes urn in a hidden 'parent' field
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)

        parent_urn = self.mongo.db.recipes.find_one({}).get('urn')
        forked_recipe_title = 'Bananna Pancakes'
        forked_recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil', 'One Bannana']
        forked_recipe_methods = ['Heat oil in a pan.', 'Mush up the bananna.',
                                 'Whisk the rest of the ingredients together.', 'Cook until golden.']
        self.submit_recipe(forked_recipe_title, forked_recipe_ingredients, forked_recipe_methods, parent=parent_urn)
        self.assertEqual(parent_urn, self.mongo.db.recipes.find_one({'title': forked_recipe_title}).get('parent'))

    def test_forked_recipes_parent_references_child(self):
        '''
        Forking a recipe should return an add new recipe page with that recipes urn in a hidden 'parent' field
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)

        parent_urn = self.mongo.db.recipes.find_one({}).get('urn')
        forked_recipe_title = 'Bananna Pancakes'
        forked_recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil', 'One Bannana']
        forked_recipe_methods = ['Heat oil in a pan.', 'Mush up the bananna.',
                                 'Whisk the rest of the ingredients together.', 'Cook until golden.']
        self.submit_recipe(forked_recipe_title, forked_recipe_ingredients, forked_recipe_methods, parent=parent_urn)
        child_urn = self.mongo.db.recipes.find_one({'title': forked_recipe_title}).get('urn')
        self.assertIn({'urn': child_urn, 'title': forked_recipe_title},
                      self.mongo.db.recipes.find_one({'urn': parent_urn}).get('children', []))

    def test_forked_recipe_has_new_name(self):
        '''
        A forked recipe should not share the parent recipes name
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)

        parent_urn = self.mongo.db.recipes.find_one({}).get('urn')
        forked_recipe_title = 'Pancakes'
        forked_recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil', 'One Bannana']
        forked_recipe_methods = ['Heat oil in a pan.', 'Mush up the bananna.',
                                 'Whisk the rest of the ingredients together.', 'Cook until golden.']
        self.submit_recipe(forked_recipe_title, forked_recipe_ingredients, forked_recipe_methods, parent=parent_urn)
        self.assertEqual(self.mongo.db.recipes.find_one({'parent': parent_urn}), None)

    def test_forked_recipe_incorrect_parent(self):
        '''
        A forked recipe with an incorrect parent should have no parent attribute
        '''
        parent_urn = 'pancakes'
        forked_recipe_title = 'Bannana Pancakes'
        forked_recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil', 'One Bannana']
        forked_recipe_methods = ['Heat oil in a pan.', 'Mush up the bananna.',
                                 'Whisk the rest of the ingredients together.', 'Cook until golden.']
        self.submit_recipe(forked_recipe_title, forked_recipe_ingredients, forked_recipe_methods, parent=parent_urn)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': forked_recipe_title}).get('parent'), None)

    # def test_add_recipe_submit_recipe_html_escape(self):
    #     '''
    #     Submitted recipes should not contain unescaped html characters - Redundant due to autoescaping during render_template()
    #     '''
    #     recipe_title = '<b>Mac & Cheese</b>'
    #     recipe_ingredients = '\n'.join(['Flour', '4 \" Stick of Butter', 'Milk', 'Cheese', 'Macaroni'])
    #     recipe_methods = '\n'.join(['<script>macaroni.boil(\'Pan\')</script>', 'Melt butter in a pan and whisk in flour before adding milk.',
    #                                 'Once mixture thickens add boiled macaroni.'])
    #     self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
    #
    #     self.assertNotRegex(self.mongo.db.recipes.find_one({}).get('title'), '[<>\'\"]+')
    #     self.assertNotRegex(self.mongo.db.recipes.find_one({}).get('ingredients'), '[<>\'\"]+')
    #     self.assertNotRegex(self.mongo.db.recipes.find_one({}).get('methods'), '[<>\'\"]+')

    def test_add_recipe_success_redirects_to_recipe(self):
        '''
        After successfully submitting a recipe users should be redirected to its page
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = ['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni']
        recipe_methods = ['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                          'Once mixture thickens add boiled macaroni.']
        response = self.client.post('/add-recipe', follow_redirects=False,
                                    data={'title': recipe_title, 'ingredients': recipe_ingredients,
                                          'methods': recipe_methods})
        # urn = self.mongo.db.recipes.find_one({}).get('urn')
        self.assertEqual(response.status_code, 302)


class TestEditRecipe(TestClient):
    '''
    Class for testing the edit_recipe page
    '''
    def setUp(self):
        self.mongo.db.logins.delete_many({})
        # Delete all records from the recipe collection
        self.mongo.db.recipes.delete_many({})

    def test_page_not_user(self):
        '''
        The edit recipe page should return 403 forbidden if the user is not the user that created the recipe
        '''
        self.create_user('Tester')
        self.login_user('Tester')
        self.submit_recipe('Test Recipe')
        self.logout_user()
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/edit-recipe/{}'.format(urn))
        self.assertEqual(response.status_code, 403)
        self.create_user('NotTester')
        self.login_user('NotTester')
        response = self.client.get('/edit-recipe/{}'.format(urn))
        self.assertEqual(response.status_code, 403)

    def test_page_user_logged_in(self):
        '''
        A logged in user that is author for the recipe should be able to access the edit-recipe page
        '''
        self.create_user('Tester')
        self.login_user('Tester')
        self.submit_recipe('Test Recipe')
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/edit-recipe/{}'.format(urn))
        self.assertEqual(response.status_code, 200)

    def test_page_recipe_not_found(self):
        '''
        Attempting to edit a recipe that doesn't exist should return 404
        '''
        self.create_user('Tester')
        self.login_user('Tester')
        response = self.client.get('/edit-recipe/not-a-recipe')
        self.assertEqual(response.status_code, 404)

    def test_edit_recipe_contains_recipe(self):
        '''
        The edit-recipe page should contain the recipe details
        '''
        self.create_user()
        self.login_user()
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = ['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni']
        recipe_methods = ['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                          'Once mixture thickens add boiled macaroni.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/edit-recipe/{}'.format(urn))
        self.assertIn(str.encode(escape('Mac & Cheese.')), response.data)
        self.assertIn(b'Milk.', response.data)
        self.assertIn(b'Once mixture thickens add boiled macaroni.', response.data)


class TestRecipes(TestClient):
    '''
    Class for testing individual recipes pages
    '''
    def setUp(self):
        # Delete all records from the user collection and create test user
        self.mongo.db.logins.delete_many({})
        self.logout_user()
        self.create_user()
        self.login_user()
        # Delete all records from the recipe collection
        self.mongo.db.recipes.delete_many({})

    def test_page(self):
        '''
        The recipe page for a recipe should return 200
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({'title': recipe_title}).get('urn')
        response = self.client.get('/recipes/{}'.format(urn))
        self.assertEqual(response.status_code, 200)

    def test_page_recipe_does_not_exist(self):
        '''
        None existent recipes should return 404
        '''
        urn = 'not-a-real-recipe'
        response = self.client.get('/recipes/{}'.format(urn))
        self.assertEqual(response.status_code, 404)

    def test_page_contains_recipe(self):
        '''
        The recipe page for a recipe should return that recipe
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = ['Flour', 'Eggs', 'Milk', 'Vegetable Oil']
        recipe_methods = ['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                          'Cook until golden.']
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({'title': recipe_title}).get('urn')
        response = self.client.get('/recipes/{}'.format(urn))
        self.assertIn(b'Pancakes', response.data)
        self.assertIn(b'Flour', response.data)
        self.assertIn(b'Cook until golden.', response.data)

    def test_page_contains_author(self):
        '''
        The recipe page should display the authors Username.
        '''
        username = 'AuthorName'
        self.logout_user()
        self.create_user(username)
        self.login_user(username)
        self.submit_recipe()
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        self.logout_user()
        response = self.client.get('/recipes/{}'.format(urn))
        self.assertIn(str.encode(username), response.data)

    def test_page_contains_tags(self):
        '''
        The returned page should contain all tags
        '''
        recipe_tags = ['Vegan', 'Vegetarian', 'Dairy-free']
        self.submit_recipe(tags=recipe_tags)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/recipes/{}'.format(urn))
        for tag in recipe_tags:
            self.assertIn(str.encode(tag), response.data)

    def test_page_contains_meals(self):
        '''
        The returned page should contain all meals
        '''
        recipe_meals = ['Breakfast', 'Brunch', 'Dessert']
        self.submit_recipe(meals=recipe_meals)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/recipes/{}'.format(urn))
        for meal in recipe_meals:
            self.assertIn(str.encode(meal), response.data)

    def test_page_contains_creation_date(self):
        '''
        The returned page should contain the date the recipe was created.
        '''
        self.submit_recipe()
        today = datetime.date.today()
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/recipes/{}'.format(urn))
        self.assertIn(str.encode(escape(today.strftime('%a %d %b \'%y'))), response.data)

    def test_page_contains_number_of_forks(self):
        '''
        The returned page should show the number of child recipes.
        '''
        parent_title = 'Pancakes'
        self.submit_recipe(title=parent_title)
        parent_urn = self.mongo.db.recipes.find_one({}).get('urn')
        self.submit_recipe(parent=parent_urn)
        self.submit_recipe(parent=parent_urn)
        self.submit_recipe(parent=parent_urn)
        response = self.client.get('/recipes/{}'.format(parent_urn))
        self.assertIn(b'3 forks', response.data)

    def test_page_contains_prep_time_and_cook_time(self):
        '''
        The returned page should contain the prep time and cook time as strings in hours and minutes
        '''
        recipe_prep_time = '00:15'
        recipe_cook_time = '01:20'
        self.submit_recipe(prep_time=recipe_prep_time, cook_time=recipe_cook_time)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/recipes/{}'.format(urn))
        self.assertIn(b'Prep-Time: 15 minutes', response.data)
        self.assertIn(b'Cooking-Time: 1 hour 20 minutes', response.data)

    def test_page_view_increases_views(self):
        '''
        When a recipe page is viewed by a different user than the one that created it its number of views should increase.
        '''
        recipe_title = 'Test-recipe'
        self.submit_recipe(title=recipe_title)
        self.logout_user()
        urn = self.mongo.db.recipes.find_one({'title': recipe_title}).get('urn')
        self.client.get('/recipes/{}'.format(urn))
        self.assertLess(0, self.mongo.db.recipes.find_one({'urn': urn}).get('views', 0))

    def test_page_view_by_author_does_not_increase_views(self):
        '''
        When a recipe page is viewed by the user that created it the number of views should not increase.
        '''
        recipe_title = 'Test-recipe'
        self.login_user()
        self.submit_recipe(title=recipe_title)
        urn = self.mongo.db.recipes.find_one({'title': recipe_title}).get('urn')
        self.client.get('/recipes/{}'.format(urn))
        self.assertEqual(0, self.mongo.db.recipes.find_one({'urn': urn}).get('views', 0))


class TestRecipesList(TestClient):
    '''
    Class for testing the add-recipe page
    '''
    @classmethod
    def setUpClass(cls):
        super(TestRecipesList, cls).setUpClass()
        # Delete all records from the user collection and create test user
        cls.mongo.db.logins.delete_many({})
        # Delete all records from the recipe collection
        cls.mongo.db.recipes.delete_many({})

        # Create plenty of fake recipes and users
        cls.logout_user()
        cls.create_user('Alice')
        cls.login_user('Alice')
        cls.submit_recipe(title='Alice\'s Apple Pie', ingredients=['12 Apples', '2 oz Flour', 'One Stick of Butter'],
                          tags=['Vegetarian'], meals=['Dessert'])
        cls.submit_recipe(title='Alice\'s Aromatic Duck', meals=['Dinner'])
        cls.submit_recipe(title='Alice\'s Avocado Salad', tags=['Vegetarian', 'Vegan', 'Dairy-free'], meals=['Lunch', 'Snack'])
        cls.submit_recipe(title='Alice\'s Apple Coleslaw', ingredients=['One Apple', 'Half a white Cabbage', 'Half a jar of Mayo'],
                          tags=['Vegetarian', 'Dairy-free', 'Gluten-free'], meals=['Side'])
        cls.submit_recipe(title='Alice\'s Anzac Biscuits', tags=['Vegetarian', 'Dairy-free'], meals=['Snack'])
        [cls.submit_recipe() for n in range(20)]
        cls.logout_user()
        cls.create_user('Benjamin')
        cls.login_user('Benjamin')
        cls.submit_recipe(title='Ben\'s Baked Alaska', tags=['Vegetarian'], meals=['Dessert'])
        cls.submit_recipe(title='Ben\'s Bean Chilli', tags=['Vegetarian', 'Vegan'], meals=['Dinner'])
        cls.submit_recipe(title='Ben\'s Bannana Smoothie', ingredients=['Bannana', 'Apple Juice'], tags=['Vegetarian', 'Gluten-free'], meals=['Drink'])
        cls.submit_recipe(title='Ben\'s Beef Curry', tags=['Gluten-free'], meals=['Dinner'])
        cls.submit_recipe(title='Ben\'s Apple & Blackberry Pie', ingredients=['12 Apples', '4 cups Blackberries', '2 oz Flour', 'One Stick of Butter'],
                          tags=['Vegetarian'], meals=['Dessert'], parent='alice-s-apple-pie')
        [cls.submit_recipe() for n in range(15)]
        cls.logout_user()
        cls.create_user('Charlie')
        cls.login_user('Charlie')
        cls.submit_recipe(title='Charlie\'s Chicken Curry', tags=['Gluten-free'], meals=['Dinner'], parent='ben-s-beef-curry')
        cls.submit_recipe(title='Charlie\'s Chocolate Chip Cookies', tags=['Vegetarian'], meals=['Snack', 'Dessert'])
        cls.submit_recipe(title='Charlie\'s Cherry Bakewells', tags=['Vegetarian', 'Dairy-free'], meals=['Snack', 'Dessert'])
        cls.submit_recipe(title='Charlie\'s Cottage Pie', tags=['Vegetarian'], meals=['Dinner'])
        cls.submit_recipe(title='Charlie\'s Chicken Caesar Salad', tags=['Gluten-free'], meals=['Lunch', 'Dinner'])
        [cls.submit_recipe() for n in range(10)]
        cls.logout_user()
        cls.create_user()
        cls.logout_user()

    def test_page(self):
        '''
        Page should return 200 status
        '''
        response = self.client.get('/recipes')
        self.assertEqual(response.status_code, 200)

    def test_number_of_recipes(self):
        '''
        Recipes page should show how many recipes match the query
        '''
        response = self.client.get('/recipes')
        self.assertIn(b'60 recipes', response.data)

    def test_number_of_tagged_recipes(self):
        '''
        Recipes page should show how many recipes have the requested tag
        '''
        response = self.client.get('/recipes?tags=Vegetarian')
        self.assertIn(b'11 recipes', response.data)
        response2 = self.client.get('/recipes?tags=Vegan')
        self.assertIn(b'2 recipes', response2.data)

    def test_number_of_multiple_tags(self):
        '''
        Recipes page should show how many recipes have the requested tags
        '''
        response = self.client.get('/recipes?tags=Vegetarian%20Vegan')
        self.assertIn(b'2 recipes', response.data)

    def test_number_of_recipes_by_author(self):
        '''
        Recipes page should show how many recipes by the requested user
        '''
        response = self.client.get('/recipes?username=Alice')
        self.assertIn(b'25 recipes', response.data)

    def test_number_of_recipes_by_author_and_tags(self):
        '''
        Recipes page should show how many recipes by the requested user, with requested tags
        '''
        response = self.client.get('/recipes?username=Alice&tags=Vegetarian')
        self.assertIn(b'4 recipes', response.data)

    def test_number_of_recipes_by_meal(self):
        '''
        Recipes page should show how many recipes are the requested meal
        '''
        response = self.client.get('/recipes?meals=Snack')
        self.assertIn(b'4 recipes', response.data)

    def test_number_of_recipes_by_author_and_tags_and_meal(self):
        '''
        Recipes page should show how many recipes by the requested user, with requested tags
        '''
        response = self.client.get('/recipes?username=Alice&tags=Vegetarian&meals=Snack%20Lunch')
        self.assertIn(b'1 recipes', response.data)

    def test_number_of_recipes_by_fork(self):
        '''
        Recipes page should show how many forked recipes are returned.
        '''
        response = self.client.get('/recipes?forks=alice-s-apple-pie')
        self.assertIn(b'1 recipes', response.data)

    def test_no_recipes(self):
        '''
        Test to show number of recipes when none found
        '''
        response = self.client.get('/recipes?forks=alice-s-apple-pie&meals=breakfast')
        self.assertIn(b'0 recipes', response.data)

    def test_links_to_recipes(self):
        '''
        Recipes page should contain links to recipes
        '''
        response = self.client.get('/recipes')
        self.assertRegex(response.data.decode(), 'href="/recipes/[a-z0-9-]+"')

    def test_links_to_recipes_in_filter(self):
        '''
        Recipes page should contain links to recipes that have been filtrered
        '''
        response = self.client.get('/recipes?tags=Vegan')
        self.assertIn(b'href="/recipes/ben-s-bean-chilli"', response.data)
        self.assertIn(b'href="/recipes/alice-s-avocado-salad"', response.data)
        self.assertNotIn(b'href="/recipes/alice-s-apple-pie"', response.data)

    def test_recipe_names_in_link(self):
        '''
        Recipes page should contain links with recipe names
        '''
        response = self.client.get('/recipes?meals=Side')
        self.assertIn(str.encode('>{}</a>'.format(escape('Alice\'s Apple Coleslaw'))), response.data)

    def test_recipe_author(self):
        '''
        Recipes page should contain authors names
        '''
        response = self.client.get('/recipes?meals=Drink')
        self.assertIn(b'Benjamin', response.data)

    def test_less_than_ten_recipes_per_page(self):
        '''
        The page should display ten or less recipes per page
        '''
        response = self.client.get('/recipes')
        self.assertLess(response.data.decode().count('href="/recipes/'), 11)

    def test_pagination(self):
        '''
        The page should display the correct number of reuslts for the page
        '''
        response = self.client.get('/recipes?username=Alice&page=3')
        self.assertEqual(response.data.decode().count('href="/recipes/'), 5)

    def test_pagination_beyond_range(self):
        '''
        Pages beyond range should return 404 not found
        '''
        response = self.client.get('/recipes?page=7')
        self.assertEqual(response.status_code, 404)

    def test_pagination_links(self):
        '''
        The current page should link to the previous and next pages
        '''
        response = self.client.get('/recipes?page=3')
        self.assertIn(b'/recipes?page=2', response.data)
        self.assertIn(b'/recipes?page=4', response.data)

    def test_pagination_no_links_beyond_range(self):
        '''
        There shouldn't be pagination links to pages beyond bounds
        '''
        response = self.client.get('/recipes')
        self.assertNotIn(b'/recipes?page=0', response.data)
        response = self.client.get('/recipes?page=6')
        self.assertNotIn(b'/recipes?page=7', response.data)

    def test_pagination_links_include_queries(self):
        '''
        Pagination links should preserve the current query
        '''
        response = self.client.get('/recipes?username=Alice&page=1')
        links = findall('/recipes\?.+?"', response.data.decode())
        self.assertIn('page=2', links[0])
        self.assertIn('username=Alice', links[0])

    def test_results_should_be_ordered_by_views(self):
        '''
        The filter should be ordered by most viewed
        '''
        self.client.get('recipes/ben-s-beef-curry')
        self.client.get('recipes/ben-s-beef-curry')
        self.client.get('recipes/ben-s-beef-curry')
        self.client.get('recipes/ben-s-beef-curry')
        self.client.get('recipes/ben-s-beef-curry')
        self.client.get('recipes/ben-s-beef-curry')
        self.client.get('recipes/ben-s-beef-curry')
        self.client.get('recipes/alice-s-apple-pie')
        self.client.get('recipes/alice-s-apple-pie')
        self.client.get('recipes/alice-s-apple-pie')
        self.client.get('recipes/alice-s-apple-pie')
        self.client.get('recipes/charlie-s-cottage-pie')
        self.client.get('recipes/charlie-s-cottage-pie')
        response = self.client.get('/recipes?page=1')
        self.assertLess(response.data.decode().index('recipes/ben-s-beef-curry'), response.data.decode().index('recipes/alice-s-apple-pie'))
        self.assertLess(response.data.decode().index('recipes/alice-s-apple-pie'), response.data.decode().index('recipes/charlie-s-cottage-pie'))

    def test_text_search_ingredients(self):
        '''
        The search queries should return recipes with ingredients that match the query
        '''
        response = self.client.get('/recipes?search=apples')
        self.assertIn(str.encode('>{}</a>'.format(escape('Alice\'s Apple Coleslaw'))), response.data)
        self.assertIn(str.encode('>{}</a>'.format(escape('Ben\'s Bannana Smoothie'))), response.data)

        response = self.client.get('/recipes?search=apples%20flour')
        self.assertIn(str.encode('>{}</a>'.format(escape('Ben\'s Apple & Blackberry Pie'))), response.data)
        self.assertNotIn(str.encode('>{}</a>'.format(escape('Alice\'s Apple Coleslaw'))), response.data)

    def test_text_search_titles(self):
        '''
        The search queries should return recipes with titles that match the query
        '''
        response = self.client.get('/recipes?search=salad')
        self.assertIn(str.encode('>{}</a>'.format(escape('Alice\'s Avocado Salad'))), response.data)
        self.assertIn(str.encode('>{}</a>'.format(escape('Charlie\'s Chicken Caesar Salad'))), response.data)

    def test_text_search_exact_string(self):
        '''
        The search query should return recipes with exact matches to queries surrounded by quote marks
        '''
        response = self.client.get('/recipes?search=%22apple%20pie%22')
        self.assertIn(str.encode('>{}</a>'.format(escape('Alice\'s Apple Pie'))), response.data)
        self.assertNotIn(str.encode('>{}</a>'.format(escape('Ben\'s Apple & Blackberry Pie'))), response.data)

    def test_text_search_two_exact_strings(self):
        '''
        The search query should return recipes with exact matches to queries surrounded by quote marks when the query
        contains more than one double quoted string.
        '''
        response = self.client.get('/recipes?search=%2212%20apples%22%20%22stick%20of%20butter%22')
        self.assertIn(str.encode('>{}</a>'.format(escape('Alice\'s Apple Pie'))), response.data)
        self.assertIn(str.encode('>{}</a>'.format(escape('Ben\'s Apple & Blackberry Pie'))), response.data)

    def test_text_search_string_in_page(self):
        '''
        The search query should appear on the page
        '''
        response = self.client.get('/recipes?search=%22apple%20pie%22')
        self.assertIn(str.encode(escape('"apple pie"')), response.data)


if __name__ == '__main__':
    unittest.main()
