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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold FROM global_inventory"))
        fr = result.first()
        
        redMl = fr.num_red_ml
        greenMl = fr.num_green_ml
        blueMl = fr.num_blue_ml
        darkMl = fr.num_dark_ml
        gold = fr.gold
        
        for barrel in barrels_delivered:
            if "RED" in barrel.sku:
                redMl += barrel.ml_per_barrel * barrel.quantity
            elif "GREEN" in barrel.sku:
                greenMl += barrel.ml_per_barrel * barrel.quantity
            elif "BLUE" in barrel.sku:
                blueMl += barrel.ml_per_barrel * barrel.quantity
            elif "DARK" in barrel.sku:
                darkMl += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.quantity * barrel.price
            
            
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_red_ml = {redMl}'))
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_green_ml = {greenMl}'))
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_blue_ml = {blueMl}'))
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_dark_ml = {darkMl}'))
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET gold = {gold}'))
        
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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold FROM global_inventory"))
        fr = result.first()
        
        MlArray = []
        redMl = fr.num_red_ml
        MlArray.append(redMl)
        greenMl = fr.num_green_ml
        MlArray.append(greenMl)
        blueMl = fr.num_blue_ml
        MlArray.append(blueMl)
        if largeCatalog is True:
            darkMl = fr.num_dark_ml
            MlArray.append(darkMl)
        gold = fr.gold
        
        goldBreakpoint = 120
        mlBreakpoint = 5000
        buyBarrels = []

    

    # initialize return dictionaries
    SRB = {"sku": "SMALL_RED_BARREL", "quantity": 1, "ml_per_barrel": 500, "potion_type": [100, 0, 0, 0], "price": redSPrice}
    MRB = {"sku": "MEDIUM_RED_BARREL", "quantity": 1, "ml_per_barrel": 2500, "potion_type": [100, 0, 0, 0], "price": 250}
    if largeCatalog is True:
        LRB = {"sku": "LARGE_RED_BARREL", "quantity": 1, "ml_per_barrel": redLMl, "potion_type": [100, 0, 0, 0], "price": redLPrice}
        LGB = {"sku": "LARGE_GREEN_BARREL", "quantity": 1, "ml_per_barrel": greenLMl, "potion_type": [0, 100, 0, 0], "price": greenLPrice}
        LBB = {"sku": "LARGE_BLUE_BARREL","quantity": 1, "ml_per_barrel": blueLMl, "potion_type": [0, 0, 100, 0], "price": blueLPrice}
        LDB = {"sku": "LARGE_DARK_BARREL", "quantity": 1, "ml_per_barrel": darkLMl, "potion_type": [0, 0, 100, 0], "price": darkLPrice}
    
    SGB = {"sku": "SMALL_GREEN_BARREL", "quantity": 1, "ml_per_barrel": 500, "potion_type": [0, 100, 0, 0], "price": 100}
    MGB = {"sku": "MEDIUM_GREEN_BARREL","quantity": 1, "ml_per_barrel": 2500, "potion_type": [0, 100, 0, 0], "price": 250}
    
    
    mBB = {"sku": "MINI_BLUE_BARREL","quantity": 1, "ml_per_barrel": 200, "potion_type": [0, 0, 100, 0], "price": 60}
    SBB = {"sku": "SMALL_BLUE_BARREL","quantity": 1, "ml_per_barrel": 500, "potion_type": [0, 0, 100, 0], "price": 120}
    MBB = {"sku": "MEDIUM_BLUE_BARREL","quantity": 1, "ml_per_barrel": 2500, "potion_type": [0, 0, 100, 0], "price": 300}
    
    
    #SDB = {"sku": "SMALL_DARK_BARREL", "quantity": 1}
    #MDB = {"sku": "MEDIUM_DARK_BARREL", "quantity": 1}
    
    
    
    count = 0
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
        
        # for idx in range(len(MlArray)):
        #     if MlArray[idx] < minVal:
        #        minVal = MlArray[idx]
            
            
        #minMl = MlArray.index(minVal)
        #if minMl == 0:
        #    minMl = 'r'
        #if minMl == 1:
        #    minMl = 'g'
        #if minMl == 2:
        #    minMl = 'b'
        #if minMl == 3:
        #    minMl = 'd'
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
                    redMl += redLMl
                    redLQuantity -= 1
                    
                elif mediumCatalog is True and gold >= redMPrice and redMQuantity > 0:
                    if MRB in buyBarrels:
                        MRB['quantity'] += 1
                    else:
                        buyBarrels.append(MRB)
                    gold -= redMPrice
                    redMl += redMMl
                    redMQuantity -= 1
                    
                elif gold >= redSPrice and redSQuantity > 0:
                    if SRB in buyBarrels:
                        SRB['quantity'] += 1
                    else:
                        buyBarrels.append(SRB)
                    gold -= redSPrice
                    redMl += redSMl
                    redSQuantity -= 1
                    
                MlArray[0] = redMl
                    
            case 'g':
                if largeCatalog is True and gold >= greenLPrice and greenLQuantity > 0:
                    if LGB in buyBarrels:
                        LGB['quantity'] += 1
                    else:
                        buyBarrels.append(LGB)
                    gold -= greenLPrice
                    greenMl += greenLMl
                    greenLQuantity -= 1
                    
                elif mediumCatalog is True and gold >= greenMPrice and greenMQuantity > 0:
                    if MGB in buyBarrels:
                        MGB['quantity'] += 1
                    else:
                        buyBarrels.append(MGB)
                    gold -= greenMPrice
                    greenMl += greenMMl
                    greenMQuantity -= 1
                    
                elif gold >= greenSPrice and greenSQuantity > 0:
                    if SGB in buyBarrels:
                        SGB['quantity'] += 1
                    else:
                        buyBarrels.append(SGB)
                    gold -= greenSPrice
                    greenMl += greenSMl
                    greenSQuantity -= 1
                    
                MlArray[1] = greenMl
                    
            case 'b':
                if largeCatalog is True and gold >= blueLPrice and blueLQuantity > 0:
                    if LBB in buyBarrels:
                        LBB['quantity'] += 1
                    else:
                        buyBarrels.append(LBB)
                    gold -= blueLPrice
                    blueMl += blueLMl
                    blueLQuantity -= 1
                    
                if mediumCatalog is True and gold >= blueMPrice and blueMQuantity > 0:
                    if MBB in buyBarrels:
                        MBB['quantity'] += 1
                    else:
                        buyBarrels.append(MBB)
                    gold -= blueMPrice
                    blueMl += blueMMl
                    blueMQuantity -= 1
                    
                elif gold >= blueSPrice and blueSQuantity > 0:
                    if SBB in buyBarrels:
                        SBB['quantity'] += 1
                    else:
                        buyBarrels.append(SBB)
                    gold -= blueSPrice
                    blueMl += blueSMl
                    blueSQuantity -= 1
                    
                MlArray[2] = blueMl
                    
            case 'd':
                if largeCatalog is True and gold >= darkLPrice and darkLQuantity > 0:
                    if LDB in buyBarrels:
                        LDB['quantity'] += 1
                    else:
                        buyBarrels.append(LDB)
                    gold -= darkLPrice
                    darkMl += darkLMl
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
                
                MlArray[3] = darkMl
        count += 1
    return buyBarrels
                
    #
    
    # with db.engine.begin() as connection:
    #     result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_red_ml, num_green_potions, num_green_ml, num_blue_potions, num_blue_ml, gold FROM global_inventory"))
    #     firstRow = result.first()
        
    #     redMl = firstRow.num_red_potions * 100 + firstRow.num_red_ml
    #     greenMl = firstRow.num_green_potions * 100 + firstRow.num_green_ml
    #     blueMl = firstRow.num_blue_potions * 100 + firstRow.num_blue_ml
    #     gold = firstRow.gold

    # # implement personal logic to decide which type of barrels to buy and their sizes
    # # buy barrel of the potion you have the least of
    # redMMl = float('inf')
    # greenMMl = float('inf')
    # blueMMl = float('inf')
    
    # mediumCatalog = False
    
    # buyBarrels = []
    
    # for barrel in wholesale_catalog:
    #     if barrel.sku == "SMALL_RED_BARREL":
    #         redSPrice = barrel.price
    #         redSMl = barrel.ml_per_barrel
    #     if barrel.sku == "SMALL_GREEN_BARREL":
    #         greenSPrice = barrel.price
    #         greenSMl = barrel.ml_per_barrel
    #     if barrel.sku == "SMALL_BLUE_BARREL":
    #         blueSPrice = barrel.price
    #         blueSMl = barrel.ml_per_barrel
    #     if barrel.sku == "MEDIUM_RED_BARREL":
    #         redMPrice = barrel.price
    #         redMMl = barrel.ml_per_barrel
    #         mediumCatalog = True
    #     if barrel.sku == "MEDIUM_GREEN_BARREL":
    #         greenMPrice = barrel.price
    #         greenMMl = barrel.ml_per_barrel
    #         mediumCatalog = True
    #     if barrel.sku == "MEDIUM_BLUE_BARREL":
    #         blueMPrice = barrel.price
    #         blueMMl = barrel.ml_per_barrel
    #         mediumCatalog = True
    
    # SRB = {
    #             "sku": "SMALL_RED_BARREL",
    #             "quantity": 1,
    #         }
    # MRB = {
    #             "sku": "MEDIUM_RED_BARREL",
    #             "quantity": 1,
    #         }
    # SGB = {
    #             "sku": "SMALL_GREEN_BARREL",
    #             "quantity": 1,
    #         }
    # MGB = {
    #             "sku": "MEDIUM_GREEN_BARREL",
    #             "quantity": 1,
    #         }
    # SBB = {
    #             "sku": "SMALL_BLUE_BARREL",
    #             "quantity": 1,
    #         }
    # MBB = {
    #             "sku": "MEDIUM_BLUE_BARREL",
    #             "quantity": 1,
    #         }
    
    # mBB = {
    #             "sku": "MINI_BLUE_BARREL",
    #             "quantity": 1,
    #         }
    
    # #when min potion is found, add it to dictionary to buy, or increment counter if it already exists
    # while (gold >= 120):
    #     min = 'r'
    #     if greenMl < redMl:
    #         min = 'g'
    #     if blueMl < greenMl:
    #         min = 'b'
    #     match min:
    #         case 'r':
    #             #if mediumCatalog is True and gold >= redMPrice:
    #             #    if MRB in buyBarrels:
    #             #        if MRB['quantity'] == 10:
    #             #            return buyBarrels
    #             #        MRB['quantity'] += 1
    #             #    else:
    #             #        buyBarrels.append(MRB)
    #             #    gold -= redMPrice
    #             #    redMl += redMMl
    #             #elif gold >= redSPrice:
    #             if gold >= redSPrice:
    #                 if SRB in buyBarrels:
    #                     if SRB['quantity'] == 10:
    #                         return buyBarrels
    #                     SRB['quantity'] += 1
    #                 else:
    #                     buyBarrels.append(SRB)
    #                 gold -= redSPrice
    #                 redMl += redSMl
    #         case 'g':
    #             #if mediumCatalog is True and gold >= greenMPrice:
    #             #    if MGB in buyBarrels:
    #             #        if MGB['quantity'] == 10:
    #             #            return buyBarrels
    #             #        MGB['quantity'] += 1
    #             #    else:
    #             #        buyBarrels.append(MGB)
    #             #    gold -= greenMPrice
    #             #    greenMl += greenMMl
    #             #elif gold >= greenSPrice:
    #             if gold >= greenSPrice:
    #                 if SGB in buyBarrels:
    #                     if SGB['quantity'] == 10:
    #                         return buyBarrels
    #                     SGB['quantity'] += 1
    #                 else:
    #                     buyBarrels.append(SGB)
    #                 gold -= greenSPrice
    #                 greenMl += greenSMl
    #         case 'b':
    #             #if mediumCatalog is True and gold >= blueMPrice:
    #             #    if MBB in buyBarrels:
    #             #        if MBB['quantity'] == 10:
    #             #            return buyBarrels
    #             #        MBB['quantity'] += 1
    #             #    else:
    #             #        buyBarrels.append(MBB)
    #             #    gold -= blueMPrice
    #             #    blueMl += blueMMl
    #             #elif gold >= blueSPrice:
    #             if gold >= blueSPrice:
    #                 if SBB in buyBarrels:
    #                     if SBB['quantity'] == 10:
    #                         return buyBarrels
    #                     SBB['quantity'] += 1
    #                 else:
    #                     buyBarrels.append(SBB)
    #                 gold -= blueSPrice
    #                 blueMl += blueSMl
                    
    # if buyBarrels == []:
    #     # if gold >= 100:
    #     #    buyBarrels.append(SRB)
    #     if gold >= 60:
    #         buyBarrels.append(mBB)
                
    # return buyBarrels
    
#[{ "sku": "LARGE_RED_BARREL", "ml_per_barrel": 10000, "potion_type": [1, 0, 0, 0], "price": 250, "quantity": 10 },
#{ "sku": "MEDIUM_BLUE_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 0, 1, 0], "price": 300, "quantity": 10 },
#{ "sku": "MEDIUM_GREEN_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 1, 0, 0], "price": 250, "quantity": 10 },
#{ "sku": "SMALL_RED_BARREL", "ml_per_barrel": 500, "potion_type": [1, 0, 0, 0], "price": 100, "quantity": 10 },
#{ "sku": "SMALL_BLUE_BARREL", "ml_per_barrel": 500, "potion_type": [0, 0, 1, 0], "price": 120, "quantity": 10 },
#{ "sku": "SMALL_GREEN_BARREL", "ml_per_barrel": 500, "potion_type": [0, 1, 0, 0], "price": 100, "quantity": 10 },
#{ "sku": "MINI_RED_BARREL", "ml_per_barrel": 200, "potion_type": [1, 0, 0, 0], "price": 60, "quantity": 1 },
#{ "sku": "MINI_BLUE_BARREL", "ml_per_barrel": 200, "potion_type": [0, 0, 1, 0], "price": 60, "quantity": 1 },
#{ "sku": "MINI_GREEN_BARREL", "ml_per_barrel": 200, "potion_type": [0, 1, 0, 0], "price": 60, "quantity": 1 },

#{ "sku": "MEDIUM_BLUE_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 0, 1, 0], "price": 300, "quantity": 10 },
#{ "sku": "MEDIUM_GREEN_BARREL", "ml_per_barrel": 2500, "potion_type": [0, 1, 0, 0], "price": 250, "quantity": 10 },
#{ "sku": "SMALL_RED_BARREL", "ml_per_barrel": 500, "potion_type": [1, 0, 0, 0], "price": 100, "quantity": 10 },
#{ "sku": "SMALL_BLUE_BARREL", "ml_per_barrel": 500, "potion_type": [0, 0, 1, 0], "price": 120, "quantity": 10 },
#{ "sku": "SMALL_GREEN_BARREL", "ml_per_barrel": 500, "potion_type": [0, 1, 0, 0], "price": 100, "quantity": 10 },
#{ "sku": "MINI_RED_BARREL", "ml_per_barrel": 200, "potion_type": [1, 0, 0, 0], "price": 60, "quantity": 1 },
#{ "sku": "MINI_BLUE_BARREL", "ml_per_barrel": 200, "potion_type": [0, 0, 1, 0], "price": 60, "quantity": 1 },
#{ "sku": "MINI_GREEN_BARREL", "ml_per_barrel": 200, "potion_type": [0, 1, 0, 0], "price": 60, "quantity": 1 }]
