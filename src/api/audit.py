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
        gold = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT SUM(change) 
                                               FROM gold_ledger
                                            """)
                                            )
        gold = gold.scalar()
        
        potionNum = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT SUM(change) 
                                               FROM potion_ledger
                                            """)
                                            )
        potionNum = potionNum.scalar()
        if potionNum is None:
            potionNum = 0
        
        redMl = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT SUM(change) 
                                               FROM ml_ledger
                                               WHERE ml_type = 'red'
                                            """)
                                            )
        redMl = redMl.scalar()
        if redMl is None:
            redMl = 0
        
        greenMl = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT SUM(change) 
                                               FROM ml_ledger
                                               WHERE ml_type = 'green'
                                            """)
                                            )
        greenMl = greenMl.scalar()
        if greenMl is None:
            greenMl = 0
        
        blueMl = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT SUM(change) 
                                               FROM ml_ledger
                                               WHERE ml_type = 'blue'
                                            """)
                                            )
        blueMl = blueMl.scalar()
        if blueMl is None:
            blueMl = 0
        
        darkMl = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT SUM(change) 
                                               FROM ml_ledger
                                               WHERE ml_type = 'dark'
                                            """)
                                            )
        darkMl = darkMl.scalar()
        if darkMl is None:
            darkMl = 0
        
        print(potionNum, (redMl, greenMl, blueMl, darkMl), gold)
        
        return {"number_of_potions": (potionNum), "ml_in_barrels": (redMl + greenMl + blueMl + darkMl), "gold": gold}
        
        
    #    result = connection.execute(sqlalchemy.text("SELECT quantity FROM potions"))
        
    #     potionQuantities = result.fetchall()
    #     print(potionQuantities)
    #     potionNum = 0
        
    #     for potion in potionQuantities:
    #         potionNum += potion[0]
            
    #     result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml from global_inventory"))
    #     fr = result.first()
    #     gold = fr.gold
    #     redMl = fr.num_red_ml
    #     greenMl = fr.num_green_ml
    #     blueMl = fr.num_blue_ml
    #     darkMl = fr.num_dark_ml
        
    #     print(potionNum, (redMl, greenMl, blueMl, darkMl), gold)
    
        
    # return {"number_of_potions": (potionNum), "ml_in_barrels": (redMl + greenMl + blueMl + darkMl), "gold": gold}


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
