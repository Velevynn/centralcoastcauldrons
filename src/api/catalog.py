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
        result = connection.execute(sqlalchemy.text("SELECT potion_id, item_sku, name, red_ml, green_ml, blue_ml, dark_ml, quantity, price FROM potions"))
        potionTable = result.fetchall()
       
        potionCatalog = []
        
        for potion in potionTable:
            if potion[7] > 0:
                potionCatalog.append(
                    {
                        'sku': potion[1],
                        'name': potion[2],
                        'quantity': potion[7],
                        'price': potion[8],
                        'potion_type': [potion[3], potion[4], potion[5], potion[6]]
                    }
                )
                
        return potionCatalog
                
    
    # with db.engine.begin() as connection:
    #     currPotions = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, num_dark_potions FROM global_inventory"))
    #     first_row = currPotions.first()
        
    #     redPotions = first_row.num_red_potions
    #     greenPotions = first_row.num_green_potions
    #     bluePotions = first_row.num_blue_potions
    #     darkPotions = first_row.num_dark_potions

    # potionTypes = {}
    # potionTypes['red'] = {'sku':'RED_POTION_0', 'name': 'red potion', 'quantity': redPotions // 2, 'price': 30, 'potion_type': [100, 0, 0, 0]}
    # potionTypes['green'] = {'sku': 'GREEN_POTION_0', 'name': 'green_potion', 'quantity': greenPotions // 2, 'price': 30, 'potion_type': [0, 100, 0, 0]}
    # potionTypes['blue'] = {'sku': 'BLUE_POTION_0', 'name': 'blue_potion', 'quantity': bluePotions // 2, 'price': 40, 'potion_type': [0, 0, 100, 0]}
    # potionTypes['dark'] = {'sku': 'DARK_POTION_0', 'name': 'dark_potion', 'quantity': darkPotions // 2, 'price': 40, 'potion_type': [0, 0, 100, 0]}

    # potionCatalog = []
    # for potion in potionTypes:
    #     if potionTypes[potion]['quantity'] > 0:
    #         potionCatalog.append(
    #             potionTypes[potion]
    #             )
    
            
    #     # check each potion type that is available using database
    #     # append to list the dictionary of each item

    # # Can return a max of 20 items.

    # return potionCatalog
