# UX Process

## Goals

- The main goal of the project is to create a recipe website that will engage users and keep them coming back.
- This engagement will be achieved by allowing users to contribute recipes and modify existing recipes to create new ones, as well as favourite and comment on them.
- The site should present recipes in an easy to understand format. Creating new recipes should be strait forward and intuitive.
- Recipes should be easy to find by filtering and searching.

## Target Audience

Users of the site will fall into one of two categories:

- Casual users, who are looking for recipes to cook and inspiration.
- Contributing users, who want to share recipes on the site.

### User Research

To find out how users interact with recipe websites I talked with a number of friends and family about what websites, as well as recipe books, they use on a regular basis. They told me what they like and what works, as well as what they don't and what turns them off a site or book.

I had them look at a number of recipe websites and asked a few questions, some that accept public contributions, and others that are more curated blogs, or the sites of celebrity chefs. The sites they looked at were:

- [BBC Good Food](https://www.bbcgoodfood.com/recipes)
- [All Recipes](https://www.allrecipes.com/)
- [Jamie Oliver](https://www.jamieoliver.com/recipes/)
- [Guardian Recipes](https://www.theguardian.com/tone/recipes)
- [Thug Kitchen](https://www.thugkitchen.com/recipes)
- [Simply Recipes](https://www.simplyrecipes.com/)

Feedback was that users generally preferred more curated sites. They liked sites and books with big images, and ones that made ingredients immediately obvious on recipe pages, rather than pushing them down below a blurb or introduction.

Users with dietary requirements were clear that they wanted to easily filter out recipes they can't have.

Of those that share their own recipes they preferred sharing them to a blog, as opposed to the larger recipe sites. However as can be seen from the huge recipe sites, there are plenty of people out there who do share recipes on these larger sites.

Users look at recipes on mobile phones and tablets just as often as they do from desktop devices.

### User Stories

Casual users are after something they can cook now, some example user stories might be:

- Sarah is searching for a quick meal to make for dinner.
- Ashley has a load of sweet potatoes and wants an interesting recipe to make the most of them.
- Jessica is lactose intolerant, and doesn't want to be shown delicious looking recipes she can't have.

Contributing users will be repeat visitors to the site, and will submit their own recipes. Some example user stories might be:

- Jeremy comes up with his own recipes, and wants feedback from other cooks.
- Theresa wants to share some of her traditional recipes with the world.
- Ryan wants to keep up to date with recipes from cooks whos food he enjoys.
- Mark likes to put his own spin on recipes, and once he's found something that works like to come back and make it again.
- Lauren enjoys veganising traditional recipes to share with her vegan friends.

## Features

### Key Features

- Clear recipe pages, featuring a list of ingredients, method and a picture.
- Ability to register and log in as a user to create their own recipes.
- Registered users can create new recipes, or modify or "fork" existing ones.
- Ability to search and filter recipes by ingredients, diet type, meal and/or preperation time.
- The site should be easy to use and responsive on mobiles, tablets and desktops.

### Additional Features

- Registered users can favourite recipes, and follow other users to see when they post new recipes.
- Registered users can comment on recipes, and reply to comments.
- Registered users can set preferences to exclude or promote recipes based on. Dietary requirements, for example.
- Moderators can choose recipes to be featured on the front page.
- Moderators can remove inappropriate content or comments.

## Structure

### Information Architecture

Database relationship diagram:

![alt text](https://raw.githubusercontent.com/ASquirrelsTail/cookbook/master/preprod/data-relations.jpg "Database relationship diagram")

The data will be stored using MongoDB, so these relationships will be stored as nested documents with enough information to navigate between them on the frontend.

For example a document in the "users" collection, in addition to their username and display name, contain an array of their recipes, with just the name, date and URI of each recipe.

### Site Map

![alt text](https://raw.githubusercontent.com/ASquirrelsTail/cookbook/master/preprod/sitemap.jpg "Sitemap")

## Wireframes

![alt text](https://raw.githubusercontent.com/ASquirrelsTail/cookbook/master/preprod/wireframe-home.jpg "Home Page")

![alt text](https://raw.githubusercontent.com/ASquirrelsTail/cookbook/master/preprod/wireframe-recipe.jpg "Recipe Page")

![alt text](https://raw.githubusercontent.com/ASquirrelsTail/cookbook/master/preprod/wireframe-mobile.jpg "Mobile Pages")

## Visuals

Having decided on Fork.it as a catchy name (sadly the domain is already taken, but lies empty) a hipster aesthetic seems to suit it. A minimalist style with a little vintage typography such as Courier New for headings and ingredients. Clear vector icons will play a part, particularly on the mobile version of the site.

Images will play a big role, with hero images of each dish taking up a large portion of the page above the fold. This relies on good images being submitted by users, which I intend to encourage by promoting recipes with images, and allowing other users to contribute images to recipes that lack them.

Colours should be muted, allowing the hero images to shine, using monochrome plus one pallet, featuring a pale brown/ochre/beige to complement the vintage stylings.

The [Materialize](https://materializecss.com/) front-end framework will provide a nice crunchy UI with a flat design that can be pared back to something more minimalist with custom scss.









