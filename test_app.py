import os
import unittest
import app


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
    def setUp(self):
        self.client, self.mongo = flask_test_client()

    def create_user(self, username='TestUser'):
        '''
        Helper function to create a new user by sending a POST request to /new-user
        '''
        return self.client.post('/new-user', follow_redirects=True,
                                data={'username': username})

    def login_user(self, username='TestUser'):
        '''
        Helper function to log in user.
        '''
        return self.client.post('/login', follow_redirects=True,
                                data={'username': username})

    def logout_user(self):
        '''
        Helper function to logout current user.
        '''
        self.client.get('/logout', follow_redirects=True)

    def submit_recipe(self, title='Test Recipe', ingredients='Test ingredient 1\nTest ingredient 2',
                      methods='Add one to two.\nEnjoy', tags='', parent=None):
        '''
        Helper function to create a recipe.
        '''
        return self.client.post('/add-recipe', follow_redirects=True,
                                data={'title': title, 'ingredients': ingredients, 'methods': methods,
                                      'tags': tags, 'parent': parent})

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
        super(TestUsers, self).setUp()
        # Delete all records from the user collection and create test user
        self.mongo.db.logins.delete_many({})

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
        super(TestAddRecipe, self).setUp()
        # Delete all records from the user collection and create test user
        self.mongo.db.logins.delete_many({})
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
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}), None)

    def test_submit_recipe_has_ingredients_and_methods(self):
        '''
        Submitted recipes should have ingredients and methods
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}.get('ingredients')), None)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}.get('methods')), None)

    def test_submit_recipe_has_tags_array(self):
        '''
        Submitted recipes should have ingredients and methods
        '''
        recipe_title = 'Vegan Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Almond Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        recipe_tags = '\n'.join(['Vegan', 'Vegetarian', 'Dairy-Free', 'Egg-Free'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods, recipe_tags)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}.get('tags')), None)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('tags'), ['Vegan', 'Vegetarian', 'Dairy-Free', 'Egg-Free'])

    def test_submit_recipe_has_username(self):
        '''
        Submitted recipes added to the recipes collection should include the username of the author
        '''
        username = 'TestUser'
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.create_user(username)
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('username'), username)

    def test_submit_recipe_missing_fields(self):
        '''
        Submitted recipes without a title, ingredients or methods should should not be added
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(None, recipe_ingredients, recipe_methods)
        self.submit_recipe(recipe_title, None, recipe_methods)
        self.submit_recipe(recipe_title, recipe_ingredients, None)
        self.assertEqual(self.mongo.db.recipes.find_one({'title': recipe_title}), None)

    def test_submit_recipe_missing_fields_preserves_input(self):
        '''
        Submitted recipes with missing fields returns the user to the add recipe page with inputs preserved
        '''
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        response = self.submit_recipe(None, recipe_ingredients, recipe_methods)
        self.assertIn(b'Cook until golden.', response.data)

    def test_submit_recipe_has_urn(self):
        '''
        Submitted recipes should have a Unique Resource Name
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotEqual(self.mongo.db.recipes.find_one({'title': recipe_title}).get('urn'), None)

    def test_submit_recipe_has_valid_urn(self):
        '''
        Submitted recipes should have a valid Unique Resource Name that only contains lowercase alphanumeric characters, underscores and dashes
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = '\n'.join(['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni'])
        recipe_methods = '\n'.join(['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                                    'Once mixture thickens add boiled macaroni.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertNotRegex(self.mongo.db.recipes.find_one({}).get('urn'), '[^a-z0-9_-]+')

    def test_submit_recipe_has_unique_urn(self):
        '''
        Submitted recipes should have a unique URN, even though titles can be identical
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = '\n'.join(['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni'])
        recipe_methods = '\n'.join(['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                                    'Once mixture thickens add boiled macaroni.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        self.assertEqual(self.mongo.db.recipes.count_documents({'urn': urn}), 1)

    def test_submit_recipe_fills_inputs_from_forked_recipe(self):
        '''
        Forking a recipe should return an add new recipe page with that recipe filled in
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = '\n'.join(['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni'])
        recipe_methods = '\n'.join(['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                                    'Once mixture thickens add boiled macaroni.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/add-recipe?fork={}'.format(urn))
        self.assertIn(b'Once mixture thickens add boiled macaroni.', response.data)

    def test_submit_recipe_has_parent_hidden_field_from_forked_recipe(self):
        '''
        Forking a recipe should return an add new recipe page with that recipes urn in a hidden 'parent' field
        '''
        recipe_title = 'Mac & Cheese'
        recipe_ingredients = '\n'.join(['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni'])
        recipe_methods = '\n'.join(['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                                    'Once mixture thickens add boiled macaroni.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({}).get('urn')
        response = self.client.get('/add-recipe?fork={}'.format(urn))
        self.assertIn(str.encode('<input type="hidden" name="parent" value="{}">'.format(urn)), response.data)

    def test_forked_recipes_reference_parent(self):
        '''
        Forking a recipe should return an add new recipe page with that recipes urn in a hidden 'parent' field
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)

        parent_urn = self.mongo.db.recipes.find_one({}).get('urn')
        forked_recipe_title = 'Bananna Pancakes'
        forked_recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil', 'One Bannana'])
        forked_recipe_methods = '\n'.join(['Heat oil in a pan.', 'Mush up the bananna.',
                                           'Whisk the rest of the ingredients together.', 'Cook until golden.'])
        self.submit_recipe(forked_recipe_title, forked_recipe_ingredients, forked_recipe_methods, parent=parent_urn)
        self.assertEqual(parent_urn, self.mongo.db.recipes.find_one({'title': forked_recipe_title}).get('parent'))

    def test_forked_recipes_parent_references_child(self):
        '''
        Forking a recipe should return an add new recipe page with that recipes urn in a hidden 'parent' field
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)

        parent_urn = self.mongo.db.recipes.find_one({}).get('urn')
        forked_recipe_title = 'Bananna Pancakes'
        forked_recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil', 'One Bannana'])
        forked_recipe_methods = '\n'.join(['Heat oil in a pan.', 'Mush up the bananna.',
                                           'Whisk the rest of the ingredients together.', 'Cook until golden.'])
        self.submit_recipe(forked_recipe_title, forked_recipe_ingredients, forked_recipe_methods, parent=parent_urn)
        child_urn = self.mongo.db.recipes.find_one({'title': forked_recipe_title}).get('urn')
        self.assertIn({'urn': child_urn, 'title': forked_recipe_title},
                      self.mongo.db.recipes.find_one({'urn': parent_urn}).get('children', []))

    def test_forked_recipe_has_new_name(self):
        '''
        A forked recipe should not share the parent recipes name
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)

        parent_urn = self.mongo.db.recipes.find_one({}).get('urn')
        forked_recipe_title = 'Pancakes'
        forked_recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil', 'One Bannana'])
        forked_recipe_methods = '\n'.join(['Heat oil in a pan.', 'Mush up the bananna.',
                                           'Whisk the rest of the ingredients together.', 'Cook until golden.'])
        self.submit_recipe(forked_recipe_title, forked_recipe_ingredients, forked_recipe_methods, parent=parent_urn)
        self.assertEqual(self.mongo.db.recipes.find_one({'parent': parent_urn}), None)

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
        recipe_ingredients = '\n'.join(['Flour', 'Butter', 'Milk', 'Cheese', 'Macaroni'])
        recipe_methods = '\n'.join(['Boil macaroni in a pan.', 'Melt butter in a pan and whisk in flour before adding milk.',
                                    'Once mixture thickens add boiled macaroni.'])
        response = self.client.post('/add-recipe', follow_redirects=False,
                                    data={'title': recipe_title, 'ingredients': recipe_ingredients,
                                          'methods': recipe_methods})
        # urn = self.mongo.db.recipes.find_one({}).get('urn')
        self.assertEqual(response.status_code, 302)


class TestRecipes(TestClient):
    '''
    Class for testing the add-recipe page
    '''
    def setUp(self):
        super(TestRecipes, self).setUp()
        # Delete all records from the user collection and create test user
        self.mongo.db.logins.delete_many({})
        self.create_user()
        self.login_user()
        # Delete all records from the recipe collection
        self.mongo.db.recipes.delete_many({})

    def test_page(self):
        '''
        The recipe page for a recipe should return 200
        '''
        recipe_title = 'Pancakes'
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
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
        recipe_ingredients = '\n'.join(['Flour', 'Eggs', 'Milk', 'Vegetable Oil'])
        recipe_methods = '\n'.join(['Heat oil in a pan.', 'Whisk the rest of the ingredients together.',
                                    'Cook until golden.'])
        self.submit_recipe(recipe_title, recipe_ingredients, recipe_methods)
        urn = self.mongo.db.recipes.find_one({'title': recipe_title}).get('urn')
        response = self.client.get('/recipes/{}'.format(urn))
        self.assertIn(b'Pancakes', response.data)
        self.assertIn(b'Flour', response.data)
        self.assertIn(b'Cook until golden.', response.data)

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


if __name__ == '__main__':
    unittest.main()
