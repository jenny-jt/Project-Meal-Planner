"""CRUD operations."""
import os
from random import choice
from model import db, connect_to_db, Ingredient, Inventory, Recipe, User, MealPlan
import spoonacular as sp
from flask import session

api = sp.API(os.environ['apiKey'])


def add_user(name, email, password):
    """add and return user"""
    user = User(name=name, email=email, password=password)
    db.session.add(user)
    db.session.commit()

    return user


def add_ingredient(name, location):
    """add and return ingredient"""
    ingredient = Ingredient(name=name, location=location)
    db.session.add(ingredient)
    db.session.commit()

    return ingredient


def recipe_ingr(ingr_data):
    """takes in ingredient data, outputs unique list of ingredients"""
    recipe_ingredients = set()

    for ingr in ingr_data:
        if ingr["id"]:  # if the ID exists
            recipe_ingredients.add(ingr['name'])

    recipe_ingredients = list(recipe_ingredients)

    return recipe_ingredients


def add_recipe(name, ingredients, url, cook_time="n/a", image="none"):
    """add and return recipe with required ingredient(s)"""
    recipe = Recipe(name=name, ingredients=ingredients, url=url, cook_time=cook_time, image=image)
    db.session.add(recipe)
    db.session.commit()

    return recipe


def add_mealplan(date, user):
    """add meal plan with date"""
    mealplan = MealPlan(date=date)
    user_add_mealplan(mealplan, user)
    db.session.add(mealplan)
    db.session.commit()

    return mealplan


def all_recipes():
    """output all recipes in database"""
    recipes = Recipe.query.order_by(Recipe.name).all()

    return recipes


def all_mealplans():
    """output all mealplans in database"""
    mealplans = MealPlan.query.order_by(Mealplan.date).all()

    return mealplans


def api_id_search(ingredients, number):
    """"takes in main ingredient(s) and number of recipes,
     returns list (length of number) of unique recipe ids
    """
    # response from API for number of recipes, will extract recipe ids
    response = api.search_recipes_by_ingredients(ingredients, number=number, ranking=1)
    data = response.json()
    api_ids = set()

    for i in range(number):
        api_id = data[i]['id']
        api_ids.add(api_id)

    api_ids = list(api_ids)

    return api_ids


def api_recipes_list(api_ids):
    """takes in list of recipe ids and outputs list of assoc recipes"""
    api_recipes = []

    for api_id in api_ids:
        recipe = recipe_info(api_id)  # either new or in db already
        api_recipes.append(recipe)

    return api_recipes


def create_api_recipes(ingredients, api_num):
    """takes in ingredients and num, returns list api recipes api_num long"""
    api_ids = api_id_search(ingredients, api_num)
    api_recipes = api_recipes_list(api_ids)

    return api_recipes


def create_db_recipes(ingredients):
    """takes list of ingredients from form and outputs unique list of recipes associated with those ingredients"""
    ingredients = ingredients.split(", ")

    db_recipes = []
    for ingredient in ingredients:
        ingr_list = Ingredient.query.filter(Ingredient.name.ilike(f'%{ingredient}%')).all()

        # if not ingr:
        #     ingr = add_ingredient(name=ingredient, location=choice(location))
        for ingr in ingr_list:
            ingr_recipes = ingr.recipes_r
            db_recipes.extend(ingr_recipes)

    db_recipes = set(db_recipes)
    db_recipes = list(db_recipes)

    return db_recipes


def mealplan_add_recipe(mealplan, recipes_list, num_recipes):
    """takes in mealplan obj and list of recipes
    adds recipes to mealplan via a method, removes those from recipes_list
    returns list of unique recipes associated with mealplan obj
    """

    while len(mealplan.recipes_r) < num_recipes:
        for item in recipes_list:
            if item not in mealplan.recipes_r:
                break
        mealplan.add_recipe_to_mealplan(item)
        recipes_list.remove(item)
        db.session.commit()

    recipes = mealplan.recipes_r
    return recipes


def mealplan_add_altrecipe(mealplan, alt_recipes):
    """takes in mealplan obj and list of recipes
    adds recipes to mealplan via a method, removes those from recipes_list
    returns list of unique recipes associated with mealplan obj
    """
    while len(mealplan.altrecipes_r) < 3:
        for item in alt_recipes:
            if item not in mealplan.altrecipes_r:
                break
        mealplan.add_altrecipe_to_mealplan(item)
        db.session.commit()

    altrecipes = mealplan.altrecipes_r

    return altrecipes


def recipe_info(api_id):
    """take in id of api recipe and retrieve recipe info,
       if recipe not in db, make new recipe obj, return recipe object"""
    response = api.get_recipe_information(id=api_id)
    data = response.json()

    name = str(data['title'])
    cook_time = int(data['readyInMinutes'])
    url = data['sourceUrl']
    image = data['image']

    ingr_data = data['extendedIngredients']
    recipe_ingredients = recipe_ingr(ingr_data)

    check_db = Recipe.query.filter(Recipe.name == name).first()

    if not check_db:  # if recipe not in db
        ingredients = ", ".join(recipe_ingredients)
        recipe = add_recipe(name=name, ingredients=ingredients, url=url, cook_time=cook_time, image=image)
        location = ["freezer", "fridge", "pantry"]

        for ingr in recipe_ingredients:
            db_ingr = Ingredient.query.filter(Ingredient.name == ingr).first()
            # if ingredient is not in db, make a new one with a random location
            if not db_ingr:
                db_ingr = add_ingredient(name=ingr, location=choice(location))
            recipe.ingredients_r.append(db_ingr)

        db.session.add(recipe)
        db.session.commit()

        return recipe

    return check_db


def user_add_mealplan(mealplan, user):
    """called when mealplan added to db, adds mealplan to user"""
    user.add_mealplan_to_user(mealplan)


def user_by_id(user_id):
    """get user by id"""

    user = User.query.get(user_id)

    return user


def user_by_email(email):
    """get user by email"""

    user = User.query.filter(User.email == email).first()

    return user


def updated_recipes(recipe_ids):
    """generate updated list of recipe objects from ids to update mealplan"""

    recipes = []

    for id in recipe_ids:
        recipe = Recipe.query.get(id)
        recipes.append(recipe)

    return recipes


if __name__ == '__main__':
    from server import app
    connect_to_db(app)