from fastapi import APIRouter
import sqlalchemy
from src import database as db


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    
    with db.engine.begin() as connection:
        currPotions = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, num_dark_potions FROM global_inventory"))
        first_row = currPotions.first()
        
        redPotions = first_row.num_red_potions
        greenPotions = first_row.num_green_potions
        bluePotions = first_row.num_blue_potions
        darkPotions = first_row.num_dark_potions

    potionTypes = {}
    potionTypes['red'] = {'sku':'RED_POTION_0', 'name': 'red potion', 'quantity': min(redPotions, 1), 'price': 30, 'potion_type': [100, 0, 0, 0]}
    potionTypes['green'] = {'sku': 'GREEN_POTION_0', 'name': 'green_potion', 'quantity': min(greenPotions, 1), 'price': 30, 'potion_type': [0, 100, 0, 0]}
    potionTypes['blue'] = {'sku': 'BLUE_POTION_0', 'name': 'blue_potion', 'quantity': min(bluePotions, 1), 'price': 40, 'potion_type': [0, 0, 100, 0]}
    potionTypes['dark'] = {'sku': 'DARK_POTION_0', 'name': 'dark_potion', 'quantity': min(darkPotions, 1), 'price': 40, 'potion_type': [0, 0, 100, 0]}

    potionCatalog = []
    for potion in potionTypes:
        if potionTypes[potion]['quantity'] > 0:
            potionCatalog.append(
                potionTypes[potion]
                )
    
            
        # check each potion type that is available using database
        # append to list the dictionary of each item

    # Can return a max of 20 items.

    return potionCatalog
