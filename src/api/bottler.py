from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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
        
    redPot = lostRed / 100
    greenPot = lostGreen / 100
    bluePot = lostBlue / 100
    
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions, num_green_ml, num_green_potions, num_blue_ml, num_blue_potions FROM global_inventory"))
        fr = result.first()
        
        currRedMl = fr.num_red_ml
        currGreenMl = fr.num_green_ml
        currBlueMl = fr.num_blue_ml
        currRedPots = fr.num_red_potions
        currGreenPots = fr.num_green_potions
        currBluePots = fr.num_blue_potions
        
        currRedMl -= lostRed
        currGreenMl -= lostGreen
        currBlueMl -= lostBlue
        currRedPots += redPot
        currGreenPots += greenPot
        currBluePots += bluePot
        
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {currRedMl}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {currRedPots}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {currGreenMl}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {currGreenPots}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {currBlueMl}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {currBluePots}"))

    return "OK"

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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"))
        firstRow = result.first()
        
        red = firstRow.num_red_ml // 100
        green = firstRow.num_green_ml // 100
        blue = firstRow.num_blue_ml // 100

    buyPotions = []
    
    if red > 0:
        buyPotions.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": red
        })
        
    if green > 0:
        buyPotions.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": green
        })
        
    if blue > 0:
        buyPotions.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": blue
        })
                    
        # SELECT mL of each mL type to determine which potions to bottle
        # calculate how many potions of each kind to bottle by appending item dictionary
        #   to return list
        
    return buyPotions
