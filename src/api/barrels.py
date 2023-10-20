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
                                                INSERT INTO ml_ledger (ml_type, change)
                                                VALUES (:ml_type, :change)
                                            """
                                            ),
                                            [{
                                                'ml_type': MlType,
                                                'change': barrel.ml_per_barrel * barrel.quantity
                                            }])
            
            
        # connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_red_ml = num_red_ml + :redMl'), [{'redMl': newInvDict['red']}])
        # connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_green_ml = num_green_ml + :greenMl'), [{'greenMl': newInvDict['green']}])
        # connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_blue_ml = num_blue_ml + :blueMl'), [{'blueMl': newInvDict['blue']}])
        # connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_dark_ml = num_dark_ml + :darkMl'), [{'darkMl': newInvDict['dark']}])
        # connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET gold = gold - :gold'), [{'gold': newInvDict['gold']}])
        
        
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    # identify which catalog is presented, and calculate prices + quantity
    mediumCatalog = False
    largeCatalog = False
    for barrel in wholesale_catalog:
        if "SMALL" in barrel.sku:
            if "RED" in barrel.sku:
                redSPrice = barrel.price
                redSMl = barrel.ml_per_barrel
                redSQuantity = barrel.quantity
            elif "GREEN" in barrel.sku:
                greenSPrice = barrel.price
                greenSMl = barrel.ml_per_barrel
                greenSQuantity = barrel.quantity
            elif "BLUE" in barrel.sku:
                blueSPrice = barrel.price
                blueSMl = barrel.ml_per_barrel
                blueSQuantity = barrel.quantity
            elif "DARK" in barrel.sku:
                darkSPrice = barrel.price
                darkSMl = barrel.ml_per_barrel
                darkSQuantity = barrel.quantity
        elif "MEDIUM" in barrel.sku: 
            mediumCatalog = True
            if "RED" in barrel.sku:
                redMPrice = barrel.price
                redMMl = barrel.ml_per_barrel
                redMQuantity = barrel.quantity
            elif "GREEN" in barrel.sku:
                greenMPrice = barrel.price
                greenMMl = barrel.ml_per_barrel
                greenMQuantity = barrel.quantity
            elif "BLUE" in barrel.sku:
                blueMPrice = barrel.price
                blueMMl = barrel.ml_per_barrel
                blueMQuantity = barrel.quantity
            elif "DARK" in barrel.sku:
                darkMPrice = barrel.price
                darkMMl = barrel.ml_per_barrel
                darkMQuantity = barrel.quantity
        elif "LARGE" in barrel.sku: 
            largeCatalog = True
            if "RED" in barrel.sku:
                redLPrice = barrel.price
                redLMl = barrel.ml_per_barrel
                redLQuantity = barrel.quantity
            elif "GREEN" in barrel.sku:
                greenLPrice = barrel.price
                greenLMl = barrel.ml_per_barrel
                greenLQuantity = barrel.quantity
            elif "BLUE" in barrel.sku:
                blueLPrice = barrel.price
                blueLMl = barrel.ml_per_barrel
                blueLQuantity = barrel.quantity
            elif "DARK" in barrel.sku:
                darkLPrice = barrel.price
                darkLMl = barrel.ml_per_barrel
                darkLQuantity = barrel.quantity
                
    # load ml, gold, and variables
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT SUM (change)
                                                    FROM ml_ledger
                                                    GROUP BY ml_type
                                                    ORDER BY ml_type
                                                """))
        mlTable = result.all()  
             
        MlArray = []
        totalMlTable = [int(str(mlTable[3]).split("'")[1]), int(str(mlTable[2]).split("'")[1]), int(str(mlTable[0]).split("'")[1]), int(str(mlTable[1]).split("'")[1])]
        
        MlArray.append(totalMlTable[3])
        MlArray.append(totalMlTable[2])
        MlArray.append(totalMlTable[0])
        
        if largeCatalog is True:
            MlArray.append(totalMlTable[1])

        goldCursor = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT SUM (change)
                                                    FROM gold_ledger
                                                """
                                                ))
        
        gold = goldCursor.scalar()

        goldBreakpoint = 120
        mlBreakpoint = 10000
        buyBarrels = []

    

    # initialize return dictionaries
    SRB = {"sku": "SMALL_RED_BARREL", "quantity": 1, "ml_per_barrel": redSMl, "potion_type": [100, 0, 0, 0], "price": redSPrice}
    SGB = {"sku": "SMALL_GREEN_BARREL", "quantity": 1, "ml_per_barrel": greenSMl, "potion_type": [0, 100, 0, 0], "price": greenSPrice}
    SBB = {"sku": "SMALL_BLUE_BARREL","quantity": 1, "ml_per_barrel": blueSMl, "potion_type": [0, 0, 100, 0], "price": blueSPrice}
    
    mBB = {"sku": "MINI_BLUE_BARREL","quantity": 1, "ml_per_barrel": 200, "potion_type": [0, 0, 100, 0], "price": 60}

    
    if mediumCatalog is True:
        MRB = {"sku": "MEDIUM_RED_BARREL", "quantity": 1, "ml_per_barrel": redMMl, "potion_type": [100, 0, 0, 0], "price": redMPrice}
        MGB = {"sku": "MEDIUM_GREEN_BARREL","quantity": 1, "ml_per_barrel": greenMMl, "potion_type": [0, 100, 0, 0], "price": greenMPrice}
        MBB = {"sku": "MEDIUM_BLUE_BARREL","quantity": 1, "ml_per_barrel": blueMMl, "potion_type": [0, 0, 100, 0], "price": blueMPrice}

    if largeCatalog is True:
        LRB = {"sku": "LARGE_RED_BARREL", "quantity": 1, "ml_per_barrel": redLMl, "potion_type": [100, 0, 0, 0], "price": redLPrice}
        LGB = {"sku": "LARGE_GREEN_BARREL", "quantity": 1, "ml_per_barrel": greenLMl, "potion_type": [0, 100, 0, 0], "price": greenLPrice}
        LBB = {"sku": "LARGE_BLUE_BARREL","quantity": 1, "ml_per_barrel": blueLMl, "potion_type": [0, 0, 100, 0], "price": blueLPrice}
        LDB = {"sku": "LARGE_DARK_BARREL", "quantity": 1, "ml_per_barrel": darkLMl, "potion_type": [0, 0, 100, 0], "price": darkLPrice}
    
   
    if gold < goldBreakpoint and gold >= 100:
        return [SRB]
    
    # while condition to buy is active
    while gold >= goldBreakpoint and any([MlArray[idx] < mlBreakpoint for idx in range(len(MlArray))]):
        # find color of lowest mL 
        minVal = float('inf')
        
        typeList = ['r', 'g', 'b']
        
        MlDict = {}
        MlDict['r'] = MlArray[0]
        MlDict['g'] = MlArray[1]
        MlDict['b'] = MlArray[2]
        if largeCatalog is True:
            MlDict['d'] = MlArray[3]
            typeList.append('d')

        random.shuffle(typeList)

        for type in typeList:
            if MlDict[type] < minVal:
                minMl = type
                minVal = MlDict[type]

        print(minMl)
        # add highest possible barrel of min color
        
        match minMl:
            case 'r':
                if largeCatalog is True and gold >= redLPrice and redLQuantity > 0:
                    if LRB in buyBarrels:
                        LRB['quantity'] += 1
                    else:
                        buyBarrels.append(LRB)
                    gold -= redLPrice
                    MlArray[0] += redLMl
                    redLQuantity -= 1
                    
                elif mediumCatalog is True and gold >= redMPrice and redMQuantity > 0:
                    if MRB in buyBarrels:
                        MRB['quantity'] += 1
                    else:
                        buyBarrels.append(MRB)
                    gold -= redMPrice
                    MlArray[0] += redMMl
                    redMQuantity -= 1
                    
                elif gold >= redSPrice and redSQuantity > 0:
                    if SRB in buyBarrels:
                        SRB['quantity'] += 1
                    else:
                        buyBarrels.append(SRB)
                    gold -= redSPrice
                    MlArray[0] += redSMl
                    redSQuantity -= 1
                                        
            case 'g':
                if largeCatalog is True and gold >= greenLPrice and greenLQuantity > 0:
                    if LGB in buyBarrels:
                        LGB['quantity'] += 1
                    else:
                        buyBarrels.append(LGB)
                    gold -= greenLPrice
                    MlArray[1] += greenLMl
                    greenLQuantity -= 1
                    
                elif mediumCatalog is True and gold >= greenMPrice and greenMQuantity > 0:
                    if MGB in buyBarrels:
                        MGB['quantity'] += 1
                    else:
                        buyBarrels.append(MGB)
                    gold -= greenMPrice
                    MlArray[1] += greenMMl
                    greenMQuantity -= 1
                    
                elif gold >= greenSPrice and greenSQuantity > 0:
                    if SGB in buyBarrels:
                        SGB['quantity'] += 1
                    else:
                        buyBarrels.append(SGB)
                    gold -= greenSPrice
                    MlArray[1] += greenSMl
                    greenSQuantity -= 1
                    
            case 'b':
                if largeCatalog is True and gold >= blueLPrice and blueLQuantity > 0:
                    if LBB in buyBarrels:
                        LBB['quantity'] += 1
                    else:
                        buyBarrels.append(LBB)
                    gold -= blueLPrice
                    MlArray[2] += blueLMl
                    blueLQuantity -= 1
                    
                if mediumCatalog is True and gold >= blueMPrice and blueMQuantity > 0:
                    if MBB in buyBarrels:
                        MBB['quantity'] += 1
                    else:
                        buyBarrels.append(MBB)
                    gold -= blueMPrice
                    MlArray[2] += blueMMl
                    blueMQuantity -= 1
                    
                elif gold >= blueSPrice and blueSQuantity > 0:
                    if SBB in buyBarrels:
                        SBB['quantity'] += 1
                    else:
                        buyBarrels.append(SBB)
                    gold -= blueSPrice
                    MlArray[2] += blueSMl
                    blueSQuantity -= 1
                    
            case 'd':
                if largeCatalog is True and gold >= darkLPrice and darkLQuantity > 0:
                    if LDB in buyBarrels:
                        LDB['quantity'] += 1
                    else:
                        buyBarrels.append(LDB)
                    gold -= darkLPrice
                    MlArray[3] += darkLMl
                    darkLQuantity -= 1
                    
                # elif mediumCatalog is True and gold >= darkMPrice and darkMQuantity > 0:
                #     if MDB in buyBarrels:
                #         MDB['quantity'] += 1
                #     else:
                #         buyBarrels.append(MDB)
                #     gold -= darkMPrice
                #     darkMl += darkMMl
                #     darkMQuantity
                    
                # elif gold >= redSPrice and redSQuantity > 0:
                #     if SDB in buyBarrels:
                #         SDB['quantity'] += 1
                #     else:
                #         buyBarrels.append(SDB)
                #     gold -= darkSPrice
                #     darkMl += darkSMl
                #     darkSQuantity
                
    return buyBarrels
    
#[{ "sku": "MEDIUM_RED_BARREL", "ml_per_barrel": 2500, "potion_type": [1, 0, 0, 0], "price": 250, "quantity": 10 },
#{ "sku": "MEDIUM_BLUE_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 0, 1, 0], "price": 300, "quantity": 10 },
#{ "sku": "MEDIUM_GREEN_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 1, 0, 0], "price": 250, "quantity": 10 },
#{ "sku": "SMALL_RED_BARREL", "ml_per_barrel": 500, "potion_type": [1, 0, 0, 0], "price": 100, "quantity": 10 },
#{ "sku": "SMALL_BLUE_BARREL", "ml_per_barrel": 500, "potion_type": [0, 0, 1, 0], "price": 120, "quantity": 10 },
#{ "sku": "SMALL_GREEN_BARREL", "ml_per_barrel": 500, "potion_type": [0, 1, 0, 0], "price": 100, "quantity": 10 },
#{ "sku": "MINI_RED_BARREL", "ml_per_barrel": 200, "potion_type": [1, 0, 0, 0], "price": 60, "quantity": 1 },
#{ "sku": "MINI_BLUE_BARREL", "ml_per_barrel": 200, "potion_type": [0, 0, 1, 0], "price": 60, "quantity": 1 },
#{ "sku": "MINI_GREEN_BARREL", "ml_per_barrel": 200, "potion_type": [0, 1, 0, 0], "price": 60, "quantity": 1 }]