// Drop all collections and replace them with new ones, or just create them if they don't exist.
db.logins.drop();
db.createCollection('logins');
db.meals.drop();
db.createCollection('meals');
db.recipes.drop();
db.createCollection('recipes');
db.tags.drop();
db.createCollection('tags');
db.users.drop();
db.createCollection('users');
// Create the admin user
db.logins.insertOne({'username': 'Admin'});
db.users.insertOne({'username': 'Admin', 'joined': '1970-01-01 00:00:00'});
// Create the tag and meal types for use by the app.
db.tags.insertMany([{'name' : 'Vegan'},
                    {'name' : 'Vegetarian'},
                    {'name' : 'Dairy-Free'},
                    {'name' : 'Gluten-Free'},
                    {'name' : 'Egg-Free'},
                    {'name' : 'Nuts'},
                    {'name' : 'Soya'},
                    {'name' : 'Shellfish'}]);
db.meals.insertMany([{'name' : 'Breakfast'},
                     {'name' : 'Brunch'},
                     {'name' : 'Lunch'},
                     {'name' : 'Snack'},
                     {'name' : 'Starter'},
                     {'name' : 'Dinner'},
                     {'name' : 'Side'},
                     {'name' : 'Dessert'},
                     {'name': 'Drink'}]);
// Create text index for recipe name and ingredients search.
db.recipes.createIndex({'title':'text','ingredients':'text'})
