from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, gold FROM global_inventory"))
        fr = result.first()
        
        redMl = fr.num_red_ml
        greenMl = fr.num_green_ml
        blueMl = fr.num_blue_ml
        gold = fr.gold
        
        for barrel in barrels_delivered:
            if "RED" in barrel.sku:
                redMl += barrel.ml_per_barrel * barrel.quantity
            elif "GREEN" in barrel.sku:
                greenMl += barrel.ml_per_barrel * barrel.quantity
            elif "BLUE" in barrel.sku:
                blueMl += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.quantity * barrel.price
            
            
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_red_ml = {redMl}'))
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_red_ml = {greenMl}'))
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET num_red_ml = {blueMl}'))
        connection.execute(sqlalchemy.text(f'UPDATE global_inventory SET gold = {gold}'))
        
    return "OK"

def find_min_potions(red, green, blue):
    
    
    return min

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_red_ml, num_green_potions, num_green_ml, num_blue_potions, num_blue_ml, gold FROM global_inventory"))
        firstRow = result.first()
        
        redMl = firstRow.num_red_potions * 100 + firstRow.num_red_ml
        greenMl = firstRow.num_green_potions * 100 + firstRow.num_green_ml
        blueMl = firstRow.num_blue_potions * 100 + firstRow.num_blue_ml
        gold = firstRow.gold

    # implement personal logic to decide which type of barrels to buy and their sizes
    # buy barrel of the potion you have the least of
    
    
    
    buyBarrels = []
    
    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            redSPrice = barrel.price
            redSMl = barrel.ml_per_barrel
        if barrel.sku == "SMALL_GREEN_BARREL":
            greenSPrice = barrel.price
            greenSMl = barrel.ml_per_barrel
        if barrel.sku == "SMALL_BLUE_BARREL":
            blueSPrice = barrel.price
            blueSMl = barrel.ml_per_barrel
        if barrel.sku == "MEDIUM_RED_BARREL":
            redMPrice = barrel.price
            redMMl = barrel.ml_per_barrel
        if barrel.sku == "MEDIUM_GREEN_BARREL":
            greenMPrice = barrel.price
            greenMMl = barrel.ml_per_barrel
        if barrel.sku == "MEDIUM_BLUE_BARREL":
            blueMPrice = barrel.price
            blueMMl = barrel.ml_per_barrel
    
    SRB = {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
    MRB = {
                "sku": "MEDIUM_RED_BARREL",
                "quantity": 1,
            }
    SGB = {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
    MGB = {
                "sku": "MEDIUM_GREEN_BARREL",
                "quantity": 1,
            }
    SBB = {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
            }
    MBB = {
                "sku": "MEDIUM_BLUE_BARREL",
                "quantity": 1,
            }
    
    #when min potion is found, add it to dictionary to buy, or increment counter if it already exists
    while gold >= 220:
        min = 'r'
        if greenMl < redMl:
            min = 'g'
        if blueMl < greenMl:
            min = 'b'
        match min:
            case 'r':
                if gold >= redMPrice:
                    if MRB in buyBarrels:
                        if MRB['quantity'] == 10:
                            return buyBarrels
                        MRB['quantity'] += 1
                    else:
                        buyBarrels.append(MRB)
                    gold -= redMPrice
                    redMl += redMMl
                elif gold >= redSPrice:
                    if SRB in buyBarrels:
                        if SRB['quantity'] == 10:
                            return buyBarrels
                        SRB['quantity'] += 1
                    else:
                        buyBarrels.append(SRB)
                    gold -= redSPrice
                    redMl += redSMl
            case 'g':
                if gold >= greenMPrice:
                    if MGB in buyBarrels:
                        if MGB['quantity'] == 10:
                            return buyBarrels
                        MGB['quantity'] += 1
                    else:
                        buyBarrels.append(MGB)
                    gold -= greenMPrice
                    greenMl += greenMMl
                elif gold >= greenSPrice:
                    if SGB in buyBarrels:
                        if SGB['quantity'] == 10:
                            return buyBarrels
                        SGB['quantity'] += 1
                    else:
                        buyBarrels.append(SGB)
                    gold -= greenSPrice
                    greenMl += greenSMl
            case 'b':
                if gold >= blueMPrice:
                    if MBB in buyBarrels:
                        if MBB['quantity'] == 10:
                            return buyBarrels
                        MBB['quantity'] += 1
                    else:
                        buyBarrels.append(MBB)
                    gold -= blueMPrice
                    blueMl += blueMMl
                elif gold >= blueSPrice:
                    if SBB in buyBarrels:
                        if SBB['quantity'] == 10:
                            return buyBarrels
                        SBB['quantity'] += 1
                    else:
                        buyBarrels.append(SBB)
                    gold -= blueSPrice
                    blueMl += blueSMl
                
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
