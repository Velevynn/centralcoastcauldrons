from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, num_red_ml, num_green_ml, num_blue_ml, gold FROM global_inventory"))
        fr = result.first()
        
        redPot = fr.num_red_potions
        greenPot = fr.num_green_potions
        bluePot = fr.num_blue_potions

        redMl = fr.num_red_ml
        greenMl = fr.num_green_ml
        blueMl = fr.num_blue_ml
        
        gold = fr.gold
        
    return {"number_of_potions": (redPot + greenPot + bluePot), "ml_in_barrels": (redMl + greenMl + blueMl), "gold": gold}


class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool


# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
