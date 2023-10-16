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
    def __init__(self, id, items):
        self.id = id
        self.items = items
    

#TODO:
# Create dictionary to track cart-ids.
# cart-id is key
# cart class (containing shopping info) is value

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                        INSERT INTO carts (customer)
                                        VALUES (:customer)"""),
                                        [{
                                          'customer': new_cart.customer
                                        }])
    
    return {"OK"}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    # use cart_id as key to get cart object instance from cartDict
    # return cartDict
    global cartDict
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT cart_id, item_id, quantity FROM cart_items WHERE cart_id = :cart_id"), [{'cart_id': cart_id}])
        cartItemList = result.fetchall()
        print(cartItemList)
        
        
        newCart = Cart(cartItemList[0], [{'item_sku': cart[1], 'quantity': cart[2]} for cart in cartItemList])
        
        return newCart
        

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
                                                    SELECT quantity
                                                    FROM potions
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
        # get rows from cart_items associated with the given cart_id
        # could maybe join cart_items and potions on item_id = potion_id?
        #   no need to select price, but still need a separate call to update potions
        result = connection.execute(sqlalchemy.text(
                                                """
                                                    SELECT cart_id, item_id, quantity
                                                    FROM cart_items
                                                    WHERE cart_id  = :cart_id
                                                """),
                                                [{
                                                    'cart_id': cart_id
                                                }])
        itemTable = result.all()
        print(itemTable)
        
        
        
        # for item in itemTable:
        #     quantityCheck = connection.execute(sqlalchemy.text(
        #                                         """
        #                                             SELECT quantity
        #                                             FROM potions
        #                                             WHERE potion_id = :potion_id
        #                                         """
        #                                         ),
        #                                         [{
        #                                             'potion_id': item[1]
        #                                         }])
        #     quantityCheck = quantityCheck.scalar()
        #     quantity = quantityCheck
        #     if item[2] > quantity:
                
            
        for item in itemTable:
            connection.execute(sqlalchemy.text(
                                            """
                                                UPDATE potions
                                                SET
                                                quantity = quantity - :sold
                                                WHERE potion_id = :item_id
                                            """),
                                            [{
                                                'sold': item[2],
                                                'item_id': item[1]
                                            }])
            price = connection.execute(sqlalchemy.text(
                                                    """
                                                        SELECT price
                                                        FROM potions
                                                        WHERE potion_id = :item_id
                                                    """),
                                                    [{
                                                        'item_id': item[1]
                                                    }])
            price = price.scalar()
            connection.execute(sqlalchemy.text(
                                            """
                                                UPDATE global_inventory
                                                SET gold = gold + :price * :quantity
                                            """),
                                            [{
                                                'price': price,
                                                'quantity': item[2]
                                            }])
            
            totalSold += item[2]
            goldGained += price * item[2]
            
    return {"total_potions_bought": totalSold, "total_gold_paid": goldGained}
            
        # for each cart item:
        #   reduce quantity of corresponding potion in potions table
        #   increase gold in global_inventory by appropriate amount
        # if potions not available, rollback the entire transaction