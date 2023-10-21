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
                                                            SELECT potion_id FROM potions
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
            potionIDPrice = potionIDPrice.scalar()
            
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO potion_ledger (potion_id, change)
                                                VALUES (:potion_id, :change)
                                            """),
                                            [{
                                                'potion_id': potionIDPrice,
                                                'change': potion.quantity
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
                                                    SELECT potions.potion_id, red_ml, green_ml, blue_ml, dark_ml, COALESCE(SUM(change), 0)::int
                                                    FROM potions
                                                    LEFT JOIN potion_ledger ON potions.potion_id = potion_ledger.potion_id
                                                    GROUP BY potions.potion_id
                                                """))
        potionTable = result.fetchall()
        print(potionTable)
        random.shuffle(potionTable)
        
        result = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT ml_type, COALESCE(SUM (change), 0)::int
                                                    FROM ml_ledger
                                                    GROUP BY ml_type
                                                """))
                
        mlRows = result.all()
        print(mlRows)
        
        totalMlTable = [0, 0, 0, 0]
        for pair in mlRows:
            if pair[0] == 'red':
                totalMlTable[0] = pair[1]
            elif pair[0] == 'green':
                totalMlTable[1] = pair[1]
            elif pair[0] == 'blue':
                totalMlTable[2] = pair[1]
            elif pair[0] == 'dark':
                totalMlTable[3] = pair[1]
        print(totalMlTable)
    
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
