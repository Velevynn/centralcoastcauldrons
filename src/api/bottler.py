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
    newPotions = 0
    lostMl = 0
    
    for potion in potions_delivered:
        newPotions += potion.quantity
        lostMl += potion.quantity * 100
    
    with db.engine.begin() as connection:
        currMl = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory"))
        currMl = currMl.scalar()
        currPotions = connection.execute(sqlalchemy.text(f"SELECT num_red_potions FROM global_inventory"))
        currPotions = currPotions.scalar()
        
        currMl = currMl - lostMl
        currPotions = currPotions + newPotions
        
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {currMl}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {currPotions}"))

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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        numMl = result.scalar()
        
    if numMl >= 100:
        return [{
            "potion_type": [100, 0, 0, 0],
            "quantity": 1,
        }]

    # Initial logic: bottle all barrels into red potions.
    else:
        return [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": 0,
                }
            ]
