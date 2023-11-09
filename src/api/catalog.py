from fastapi import APIRouter
import sqlalchemy
from src import database as db
import random


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    
    with db.engine.begin() as connection:
        # Create sliding view to offer potions according to what has been sold recently
        recentPotionIds = connection.execute(sqlalchemy.text(
            """
                WITH recent_transactions AS (
                    SELECT potion_ledger.potion_id, potion_ledger.transaction_id, potion_ledger.change AS sold
                    FROM potion_ledger
                    WHERE potion_ledger.change < 0
                    ORDER BY transaction_id DESC
                    LIMIT 30
                )
                SELECT DISTINCT potions.potion_id::int AS id, SUM(recent_transactions.sold)::int AS sold, potions.red_ml, potions.green_ml, potions.blue_ml, potions.dark_ml
                FROM recent_transactions
                INNER JOIN potions ON recent_transactions.potion_id = potions.potion_id
                WHERE potions.price > 1
                GROUP BY potions.potion_id
                ORDER BY sold ASC
                
            """
            )).all()
        
        print(recentPotionIds)
        idList = []
        totalSold = 0
        for potion in recentPotionIds:
            totalSold += (potion.sold // -1)
        for potion in recentPotionIds:
            if potion.id not in idList and len(idList) < 3 and (potion.sold // -1) >= totalSold * .2:
                idList.append((potion.id))

        result = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT potions.potion_id, item_sku, potions.name, red_ml, green_ml, blue_ml, dark_ml, price, COALESCE(SUM(change), 0)::int AS quantity
                                                    FROM potions
                                                    LEFT JOIN potion_ledger ON potions.potion_id = potion_ledger.potion_id
                                                    WHERE potions.price > 1
                                                    GROUP BY potions.potion_id
                                                """))
        
        potionTable = result.all()
        
        potionCatalog = []
            
        for potion in potionTable:
            if potion.potion_id in idList:
                if potion.quantity > 0:
                    potionCatalog.append(
                    {
                        'sku': potion.item_sku,
                        'name': potion.name,
                        'quantity': potion.quantity,
                        'price': potion.price,
                        'potion_type': [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml]
                    }
                )
        
        random.shuffle(potionTable)
    
        for potion in potionTable:
            if len(potionCatalog) == 6 or potion.potion_id in idList:
                continue
            if potion.quantity > 0:
                potionCatalog.append(
                    {
                        'sku': potion.item_sku,
                        'name': potion.name,
                        'quantity': potion.quantity,
                        'price': potion.price,
                        'potion_type': [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml]
                    }
                )
        print(potionCatalog)
        return potionCatalog
