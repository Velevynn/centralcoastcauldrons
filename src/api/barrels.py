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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"));
        numMl = result.scalar();
        
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        gold = result.scalar();
        
        for barrel in barrels_delivered:
            numMl += (barrel.ml_per_barrel) * barrel.quantity
            gold -= barrel.price * barrel.quantity
            
        connection.execute(sqlalchemy.text('UPDATE global_inventory SET num_red_ml = :numMl'))
        connection.execute(sqlalchemy.text('UPDATE global_inventory SET gold = :gold'))
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        numPotions = result.scalar();


    if numPotions < 10:
        return [{
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }]
        
    
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 0,
        }
    ]
