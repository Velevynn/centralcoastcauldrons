from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str
    
class Cart:
    def __init__(self, items):
        self.items = items
    

#TODO:
# Create dictionary to track cart-ids.
# cart-id is key
# cart class (containing shopping info) is value

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
                                        """
                                            INSERT INTO carts (customer)
                                            VALUES (:customer)
                                            RETURNING carts.cart_id
                                        """),
                                        [{
                                          'customer': new_cart.customer
                                        }])
    
    return {"cart_id": result.scalar()}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    # use cart_id as key to get cart object instance from cartDict
    # return cartDict
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT cart_id, item_id, quantity FROM cart_items WHERE cart_id = :cart_id"), [{'cart_id': cart_id}])
        cartItemList = result.fetchall()
        
        print(cartItemList)
        
        
        itemList = []
        
        for cart in cartItemList:
            newItemID = cart[1]
            newItemQuantity = cart[2]
            newItem = {newItemID: newItemQuantity}
            itemList.append(newItem)
        
        print(itemList)
        return  Cart(itemList)
        

class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    
    # cart = get_cart(cart_id)
    # print(cart.id, cart.items)
    
    with db.engine.begin() as connection:
        
        quantityCheck = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT COALESCE(SUM(change), 0)::int
                                                    FROM potions
                                                    LEFT JOIN potion_ledger
                                                    ON potions.potion_id = potion_ledger.potion_id
                                                    WHERE item_sku = :item_sku
                                                """
                                                ),
                                                [{
                                                    'item_sku': item_sku
                                                }])
        quantityCheck = quantityCheck.scalar()
        quantity = quantityCheck
        if cart_item.quantity > quantity:
            return "NOT ENOUGH POTIONS"
            
        connection.execute(sqlalchemy.text(
                            """
                                INSERT INTO cart_items (cart_id, item_id, quantity)
                                SELECT :cart_id, potions.potion_id, :quantity
                                FROM potions WHERE potions.item_sku = :item_sku
                            """
                            ),
                            [{
                                "cart_id": cart_id,
                                "quantity": cart_item.quantity,
                                "item_sku": item_sku
                            }])
           
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    # get cart from cart_id
    
    print(cart_checkout.payment)
    cart = get_cart(cart_id)
    totalSold = 0
    goldGained = 0
    
    with db.engine.begin() as connection:
        cartCheckedOut = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT checked_out
                                                    FROM carts
                                                    WHERE cart_id = :cart_id
                                                """
                                                ),
                                                [{
                                                    'cart_id': cart_id
                                                }]).scalar()
        
        if cartCheckedOut is True:
            return "Invalid Selection"
        
        itemTable = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT cart_id, item_id, quantity
                                                    FROM cart_items
                                                    WHERE cart_id  = :cart_id
                                                """
                                                ),
                                                [{
                                                    'cart_id': cart_id
                                                }]).all()
        print(itemTable)
        
        
        for item in itemTable:
            quantityCheck = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT COALESCE(SUM(change), 0)::int
                                                    FROM potions
                                                    LEFT JOIN potion_ledger
                                                    ON potions.potion_id = potion_ledger.potion_id
                                                    WHERE potions.potion_id = :potion_id
                                                """
                                                ),
                                                [{
                                                    'potion_id': item.item_id
                                                }]).scalar()
            if item[2] > quantityCheck:
                return "Invalid Request"
                
            
        for item in itemTable:
            priceName = connection.execute(sqlalchemy.text(
                                                    """
                                                        SELECT price, name
                                                        FROM potions
                                                        WHERE potion_id = :item_id
                                                    """),
                                                    [{
                                                        'item_id': item.item_id
                                                    }]).first()
            print(priceName)
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO potion_ledger (potion_id, name, change)
                                                VALUES (:potion_id, :name, :sold)
                                            """
                                            ),
                                            [{
                                                'potion_id': item.item_id,
                                                'name': priceName.name,
                                                'sold': item.quantity // -1
                                            }])
            
            connection.execute(sqlalchemy.text(
                                            """
                                                INSERT INTO gold_ledger (category, change)
                                                VALUES (:category, :goldGained)
                                            """
                                            ),
                                            [{
                                                'category': "Sold %d %s potions of id %d" % (item.quantity, priceName.name, item.item_id),
                                                'goldGained': priceName.price * item.quantity
                                            }])
            
            
            totalSold += item.quantity
            goldGained += priceName.price * item.quantity
            
        connection.execute(sqlalchemy.text(
                                        """
                                            UPDATE carts
                                            SET checked_out = :true
                                            WHERE cart_id = :cart_id
                                        """
                                        ),
                                        [{
                                            'true': True,
                                            'cart_id': cart_id
                                        }])
        
        
            
    return {"total_potions_bought": totalSold, "total_gold_paid": goldGained}
            
        # for each cart item:
        #   reduce quantity of corresponding potion in potions table
        #   increase gold in global_inventory by appropriate amount
        # if potions not available, rollback the entire transaction