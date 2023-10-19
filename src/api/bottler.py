from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)
    lostRed = 0
    lostGreen = 0
    lostBlue = 0
    lostDark = 0
    
    for potion in potions_delivered:
        lostRed += potion.potion_type[0] * potion.quantity
        lostGreen += potion.potion_type[1] * potion.quantity
        lostBlue += potion.potion_type[2] * potion.quantity
        lostDark += potion.potion_type[3] * potion.quantity
    
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            potionIDPrice = connection.execute(sqlalchemy.text(
                                                        """
                                                            SELECT potion_id, price FROM potions
                                                            WHERE red_ml = :red
                                                            AND green_ml = :green
                                                            AND blue_ml = :blue
                                                            AND dark_ml = :dark
                                                        """),
                                                        [{
                                                            'quantity': potion.quantity,
                                                            'red': potion.potion_type[0],
                                                            'green': potion.potion_type[1],
                                                            'blue': potion.potion_type[2],
                                                            'dark': potion.potion_type[3]
                                                        }])
            potionIDPrice = potionIDPrice.all()
            
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO potion_ledger (potion_id, change)
                                                VALUES (:potion_id)
                                            """),
                                            [{
                                                'potion_id': potionIDPrice[0],
                                                'change': potionIDPrice[1]
                                            }])
        
        
        
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - :lostRed"), [{'lostRed': lostRed}])
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - :lostGreen"), [{'lostGreen': lostGreen}])
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml - :lostBlue"), [{'lostBlue': lostBlue}])
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_dark_ml = num_dark_ml - :lostDark"), [{'lostDark': lostDark}])

        for potion in potions_delivered:
            connection.execute(sqlalchemy.text("""
                                               UPDATE potions SET quantity = quantity + :quantity
                                               WHERE red_ml = :red
                                               AND green_ml = :green
                                               AND blue_ml = :blue
                                               AND dark_ml = :dark
                                               """),
                                                [{'quantity': potion.quantity,
                                                  'red': potion.potion_type[0],
                                                  'green': potion.potion_type[1],
                                                  'blue': potion.potion_type[2],
                                                  'dark': potion.potion_type[3]}])
        
    return "OK"
        
    # redPot = lostRed / 100
    # greenPot = lostGreen / 100
    # bluePot = lostBlue / 100
    # darkPot = lostDark / 100
    
    # with db.engine.begin() as connection:
    #     result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions, num_green_ml, num_green_potions, num_blue_ml, num_blue_potions, num_dark_ml, num_dark_potions FROM global_inventory"))
    #     fr = result.first()
        
    #     currRedMl = fr.num_red_ml
    #     currGreenMl = fr.num_green_ml
    #     currBlueMl = fr.num_blue_ml
    #     currDarkMl = fr.num_dark_ml
    #     currRedPots = fr.num_red_potions
    #     currGreenPots = fr.num_green_potions
    #     currBluePots = fr.num_blue_potions
    #     currDarkPots = fr.num_dark_potions
        
    #     currRedMl -= lostRed
    #     currGreenMl -= lostGreen
    #     currBlueMl -= lostBlue
    #     currDarkMl -= lostDark
    #     currRedPots += redPot
    #     currGreenPots += greenPot
    #     currBluePots += bluePot
    #     currDarkPots -= darkPot
        
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {currRedMl}"))
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {currRedPots}"))
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {currGreenMl}"))
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {currGreenPots}"))
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {currBlueMl}"))
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {currBluePots}"))
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = {currDarkMl}"))
    #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_potions = {currDarkPots}"))
    
    
    

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT potion_id, red_ml, green_ml, blue_ml, dark_ml, quantity FROM potions"))
        potionTable = result.fetchall()
        print(potionTable)
        random.shuffle(potionTable)
        
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"))
        fr = result.first()
        totalMlTable = [fr.num_red_ml, fr.num_green_ml, fr.num_blue_ml, fr.num_dark_ml]
        
        
        buyPotions = []
        
        for potion in potionTable:
            currPotionQuantity = potion[5]
            potionDict = {
                        "potion_type": [potion[1], potion[2], potion[3], potion[4]],
                        "quantity": 1
                    }
            while all([potion[idx+1] <= totalMlTable[idx] for idx in range(len(totalMlTable))]) and currPotionQuantity < 10:
                totalMlTable[0] -= potion[1]
                totalMlTable[1] -= potion[2]
                totalMlTable[2] -= potion[3]
                totalMlTable[3] -= potion[4]
                currPotionQuantity += 1

                if potionDict in buyPotions:
                    potionDict['quantity'] += 1
                else:
                    buyPotions.append(potionDict)
                           
        print(buyPotions) 
        return buyPotions
                
            
    
    
    # with db.engine.begin() as connection:
    #     result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"))
    #     firstRow = result.first()
        
    #     red = firstRow.num_red_ml // 100
    #     green = firstRow.num_green_ml // 100
    #     blue = firstRow.num_blue_ml // 100
    #     dark = firstRow.num_dark_ml // 100

    # buyPotions = []
    
    # if red > 0:
    #     buyPotions.append({
    #         "potion_type": [100, 0, 0, 0],
    #         "quantity": red
    #     })
        
    # if green > 0:
    #     buyPotions.append({
    #         "potion_type": [0, 100, 0, 0],
    #         "quantity": green
    #     })
        
    # if blue > 0:
    #     buyPotions.append({
    #         "potion_type": [0, 0, 100, 0],
    #         "quantity": blue
    #     })

    # if dark > 0:
    #     buyPotions.append({
    #         "potion_type": [0, 0, 0, 100],
    #         "quantity": dark
    #     })
                    
    #     # SELECT mL of each mL type to determine which potions to bottle
    #     # calculate how many potions of each kind to bottle by appending item dictionary
    #     #   to return list
        
    # return buyPotions
