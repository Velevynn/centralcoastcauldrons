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
                                               SELECT COALESCE(SUM(change), 0)::int AS quantity
                                               FROM gold_ledger
                                            """)
                                            ).scalar()
        
        potionNum = connection.execute(sqlalchemy.text(
                                            """
                                               SELECT COALESCE(SUM(change), 0)::int AS quantity
                                               FROM potion_ledger
                                            """)
                                            ).scalar()
        
        mlTable = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT ml_type, COALESCE(SUM(change), 0)::int AS quantity
                                                    FROM ml_ledger
                                                    GROUP BY ml_type
                                                    ORDER BY ml_type
                                                """)).all()             
        print(mlTable)
        
        mlDict = {}
        
        for pair in mlTable:
            mlDict[pair.ml_type] = pair.quantity
        
        print(potionNum, (mlDict['red'], mlDict['green'], mlDict['blue'], mlDict['dark']), gold)
        
        return {"number_of_potions": (potionNum), "ml_in_barrels": (mlDict['red']+ mlDict['green'] + mlDict['blue'] + mlDict['dark']), "gold": gold}
        
        
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
