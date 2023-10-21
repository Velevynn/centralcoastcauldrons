from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)
    
    with db.engine.begin() as connection:
        
        newInvDict = {
            'red': 0,
            'green': 0,
            'blue': 0,
            'dark': 0,
            'gold': 0,
        }
        
        for barrel in barrels_delivered:
            if "RED" in barrel.sku:
                newInvDict['red'] += barrel.ml_per_barrel * barrel.quantity
                MlType = 'red'
            elif "GREEN" in barrel.sku:
                newInvDict['green'] += barrel.ml_per_barrel * barrel.quantity
                MlType = 'green'
            elif "BLUE" in barrel.sku:
                newInvDict['blue'] += barrel.ml_per_barrel * barrel.quantity
                MlType = 'blue'
            elif "DARK" in barrel.sku:
                newInvDict['dark'] += barrel.ml_per_barrel * barrel.quantity
                MlType = 'dark'
                
            newInvDict['gold'] = barrel.quantity * barrel.price
            
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO gold_ledger (category, change)
                                                VALUES (:category, :change)
                                            """
                                            ),
                                            [{
                                                'category': "Bought %d barrels of %s type" % (barrel.quantity, barrel.sku),
                                                'change': newInvDict['gold'] // -1
                                            }])
            
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO ml_ledger (category, red_change, green_change, blue_change, dark_change)
                                                VALUES (:category, :red_change, :green_change, :blue_change, :dark_change)
                                            """
                                            ),
                                            [{
                                                'category': "Bought %d barrels of %s type" % (barrel.quantity, barrel.sku),
                                                'red_change': barrel.potion_type[0] * barrel.ml_per_barrel * barrel.quantity,
                                                'green_change': barrel.potion_type[1] * barrel.ml_per_barrel * barrel.quantity,
                                                'blue_change': barrel.potion_type[2] * barrel.ml_per_barrel * barrel.quantity,
                                                'dark_change': barrel.potion_type[3] * barrel.ml_per_barrel * barrel.quantity
                                            }])
            
        
        
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    # identify which catalog is presented, and calculate prices + quantity
    mediumCatalog = False
    largeCatalog = False
    barrelDict = {}
    
    for barrel in wholesale_catalog:
        if 'MEDIUM' in barrel.sku:
            mediumCatalog = True
        elif 'LARGE' in barrel.sku:
            largeCatalog = True
        barrelDict[barrel.sku] = barrel
                
    # load ml, gold, and variables
    with db.engine.begin() as connection:
        mlTable = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT
                                                    COALESCE(SUM(red_change), 0)::int as red_change,
                                                    COALESCE(SUM(green_change), 0)::int as green_change,
                                                    COALESCE(SUM(blue_change), 0)::int as blue_change,
                                                    COALESCE(SUM(dark_change), 0)::int as dark_change
                                                    FROM ml_ledger
                                                    
                                                """)).first()             
        print(mlTable)
        
        mlDict = {}
        goldBreakpoint = 100
        buyBarrels = []
        
        mlDict['red'] = mlTable.red_change
        mlDict['green'] = mlTable.green_change
        mlDict['blue'] = mlTable.blue_change
        mlDict['dark'] = mlTable.dark_change
        print(mlDict)
        
        if largeCatalog is not True:
            del mlDict['dark']

        gold = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT COALESCE(SUM(change), 0)::int AS quantity
                                               FROM gold_ledger
                                            """)
                                            ).scalar()

    # while condition to buy is active
    while gold >= goldBreakpoint:
        minVal = float('inf')
        typeList = list(mlDict.keys())
        random.shuffle(typeList)

        for type in typeList:
            if mlDict[type] < minVal:
                minMl = type
                minVal = mlDict[type]

        print(minMl)
        
        match minMl:
            case 'red':
                if largeCatalog is True and gold >= barrelDict['LARGE_RED_BARREL'].price and barrelDict['LARGE_RED_BARREL'].quantity > 0:
                    barrel = {'sku': 'LARGE_RED_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['LARGE_RED_BARREL'].price
                    mlDict['red'] += barrelDict['LARGE_RED_BARREL'].ml_per_barrel
                    barrelDict['LARGE_RED_BARREL'].quantity -= 1
                    
                elif mediumCatalog is True and gold >= barrelDict['MEDIUM_RED_BARREL'].price and barrelDict['MEDIUM_RED_BARREL'].quantity > 0:
                    barrel = {'sku': 'MEDIUM_RED_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['MEDIUM_RED_BARREL'].price
                    mlDict['red'] += barrelDict['MEDIUM_RED_BARREL'].ml_per_barrel
                    barrelDict['MEDIUM_RED_BARREL'].quantity -= 1
                    
                elif gold >= barrelDict['SMALL_RED_BARREL'].price and barrelDict['SMALL_RED_BARREL'].quantity > 0:
                    barrel = {'sku': 'SMALL_RED_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['SMALL_RED_BARREL'].price
                    mlDict['red'] += barrelDict['SMALL_RED_BARREL'].ml_per_barrel
                    barrelDict['SMALL_RED_BARREL'].quantity -= 1
                                        
            case 'green':
                if largeCatalog is True and gold >= barrelDict['LARGE_GREEN_BARREL'].price and barrelDict['LARGE_GREEN_BARREL'].quantity > 0:
                    barrel = {'sku': 'LARGE_GREEN_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['LARGE_RED_BARREL'].price
                    mlDict['green'] += barrelDict['LARGE_RED_BARREL'].ml_per_barrel
                    barrelDict['LARGE_RED_BARREL'].quantity -= 1
                    
                elif mediumCatalog is True and gold >= barrelDict['MEDIUM_GREEN_BARREL'].price and barrelDict['MEDIUM_GREEN_BARREL'].quantity > 0:
                    barrel = {'sku': 'MEDIUM_GREEN_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['MEDIUM_GREEN_BARREL'].price
                    mlDict['green'] += barrelDict['MEDIUM_GREEN_BARREL'].ml_per_barrel
                    barrelDict['MEDIUM_GREEN_BARREL'].quantity -= 1
                    
                elif gold >= barrelDict['SMALL_GREEN_BARREL'].price and barrelDict['SMALL_GREEN_BARREL'].quantity > 0:
                    barrel = {'sku': 'SMALL_GREEN_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['SMALL_GREEN_BARREL'].price
                    mlDict['green'] += barrelDict['SMALL_GREEN_BARREL'].ml_per_barrel
                    barrelDict['SMALL_GREEN_BARREL'].quantity -= 1
                    
            case 'blue':
                if largeCatalog is True and gold >= barrelDict['LARGE_BLUE_BARREL'].price and barrelDict['LARGE_BLUE_BARREL'].quantity > 0:
                    barrel = {'sku': 'LARGE_BLUE_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['LARGE_BLUE_BARREL'].price
                    mlDict['blue'] += barrelDict['LARGE_BLUE_BARREL'].ml_per_barrel
                    barrelDict['LARGE_BLUE_BARREL'].quantity -= 1
                    
                if mediumCatalog is True and gold >= barrelDict['MEDIUM_BLUE_BARREL'].price and barrelDict['MEDIUM_BLUE_BARREL'].quantity > 0:
                    barrel = {'sku': 'MEDIUM_BLUE_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['MEDIUM_BLUE_BARREL'].price
                    mlDict['blue'] += barrelDict['MEDIUM_BLUE_BARREL'].ml_per_barrel
                    barrelDict['MEDIUM_BLUE_BARREL'].quantity -= 1
                    
                elif gold >= barrelDict['SMALL_BLUE_BARREL'].price and barrelDict['SMALL_BLUE_BARREL'].quantity > 0:
                    barrel = {'sku': 'SMALL_BLUE_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['SMALL_BLUE_BARREL'].price
                    mlDict['blue'] += barrelDict['SMALL_BLUE_BARREL'].ml_per_barrel
                    barrelDict['SMALL_BLUE_BARREL'].quantity -= 1
                    
            case 'dark':
                if largeCatalog is True and gold >= barrelDict['LARGE_DARK_BARREL'].price and barrelDict['LARGE_DARK_BARREL'].quantity > 0:
                    barrel = {'sku': 'LARGE_DARK_BARREL', 'quantity': 1}
                    if barrel in buyBarrels:
                        barrel['quantity'] += 1
                    else:
                        buyBarrels.append(barrel)
                    gold -= barrelDict['LARGE_DARK_BARREL'].price
                    mlDict['dark'] += barrelDict['LARGE_DARK_BARREL'].ml_per_barrel
                    barrelDict['LARGE_DARK_BARREL'].quantity -= 1
                
    return buyBarrels
    
# [{ "sku": "MEDIUM_RED_BARREL", "ml_per_barrel": 2500, "potion_type": [1, 0, 0, 0], "price": 250, "quantity": 10 },
# { "sku": "MEDIUM_BLUE_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 0, 1, 0], "price": 300, "quantity": 10 },
# { "sku": "MEDIUM_GREEN_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 1, 0, 0], "price": 250, "quantity": 10 },
# { "sku": "SMALL_RED_BARREL", "ml_per_barrel": 500, "potion_type": [1, 0, 0, 0], "price": 100, "quantity": 10 },
# { "sku": "SMALL_BLUE_BARREL", "ml_per_barrel": 500, "potion_type": [0, 0, 1, 0], "price": 120, "quantity": 10 },
# { "sku": "SMALL_GREEN_BARREL", "ml_per_barrel": 500, "potion_type": [0, 1, 0, 0], "price": 100, "quantity": 10 },
# { "sku": "MINI_RED_BARREL", "ml_per_barrel": 200, "potion_type": [1, 0, 0, 0], "price": 60, "quantity": 1 },
# { "sku": "MINI_BLUE_BARREL", "ml_per_barrel": 200, "potion_type": [0, 0, 1, 0], "price": 60, "quantity": 1 },
# { "sku": "MINI_GREEN_BARREL", "ml_per_barrel": 200, "potion_type": [0, 1, 0, 0], "price": 60, "quantity": 1 }]