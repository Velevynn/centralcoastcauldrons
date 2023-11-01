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
            potionIDName = connection.execute(sqlalchemy.text(
                                                        """
                                                            SELECT potion_id, name FROM potions
                                                            WHERE red_ml = :red
                                                            AND green_ml = :green
                                                            AND blue_ml = :blue
                                                            AND dark_ml = :dark
                                                        """),
                                                        [{
                                                            'red': potion.potion_type[0],
                                                            'green': potion.potion_type[1],
                                                            'blue': potion.potion_type[2],
                                                            'dark': potion.potion_type[3]
                                                        }])
            potionIDName = potionIDName.first()
            
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO potion_ledger (potion_id, name, change)
                                                VALUES (:potion_id, :name, :change)
                                            """),
                                            [{
                                                'potion_id': potionIDName.potion_id,
                                                'name': potionIDName.name,
                                                'change': potion.quantity
                                            }])
            
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO ml_ledger (category, red_change, green_change, blue_change, dark_change)
                                                VALUES (:category, :red_change, :green_change, :blue_change, :dark_change)
                                            """
                                            ),
                                            [{
                                                'category': "Bottled %d %s potions of id %s." % (potion.quantity, potionIDName.name, potionIDName.potion_id),
                                                'red_change': potion.potion_type[0] * potion.quantity // -1,
                                                'green_change': potion.potion_type[1] * potion.quantity // -1,
                                                'blue_change': potion.potion_type[2] * potion.quantity // -1,
                                                'dark_change': potion.potion_type[3] * potion.quantity // -1
                                            }])
        
    return "OK"
        
    
    
    

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT potions.potion_id, red_ml, green_ml, blue_ml, dark_ml, COALESCE(SUM(change), 0)::int AS quantity
                                                    FROM potions
                                                    LEFT JOIN potion_ledger ON potions.potion_id = potion_ledger.potion_id
                                                    GROUP BY potions.potion_id
                                                """))
        potionTable = result.fetchall()
        print(potionTable)
        random.shuffle(potionTable)
        
        result = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT
                                                    COALESCE(SUM(red_change), 0)::int as red_change,
                                                    COALESCE(SUM(green_change), 0)::int as green_change,
                                                    COALESCE(SUM(blue_change), 0)::int as blue_change,
                                                    COALESCE(SUM(dark_change), 0)::int as dark_change
                                                    FROM ml_ledger
                                                """))
                
        mlRows = result.first()
        print(mlRows)
        
        totalMlTable = [mlRows.red_change, mlRows.green_change, mlRows.blue_change, mlRows.dark_change]
        print(totalMlTable)
    
        buyPotions = []
        
        for potion in potionTable:
            currPotionQuantity = potion.quantity
            potionDict = {
                        "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
                        "quantity": 1
                    }
            #testing
            while all([potion[idx+1] <= totalMlTable[idx] for idx in range(len(totalMlTable))]) and currPotionQuantity < 20:
                totalMlTable[0] -= potion.red_ml
                totalMlTable[1] -= potion.green_ml
                totalMlTable[2] -= potion.blue_ml
                totalMlTable[3] -= potion.dark_ml
                currPotionQuantity += 1

                if potionDict in buyPotions:
                    potionDict['quantity'] += 1
                else:
                    buyPotions.append(potionDict)
                           
        print(buyPotions) 
    return buyPotions
