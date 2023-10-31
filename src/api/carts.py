from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from sqlalchemy import MetaData


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
    """
    
    
    
    
    with db.engine.begin() as connection:
        # events = db.carts.join(db.cart_items, db.carts.c.cart_id == db.cart_items.c.cart_id)
        # events = events.join(db.potions, db.potions.c.potion_id == db.cart_items.c.item_id)
        
        
        # stmt = (
        #     """
        #         With Orders AS (
        #             SELECT
        #                 carts.customer AS customer_name,
        #                 potions.item_sku AS item_sku,
        #                 cart_items.quantity AS quantity,
        #                 potions.price AS price,
        #                 carts.created_at AS timestamp
        #             FROM carts
        #             JOIN cart_items on carts.cart_id = cart_items.cart_id
        #             JOIN potions on potions.potion_id = cart_items.item_id
        #         )
        #         SELECT
        #             customer_name,
        #             item_sku,
        #             quantity,
        #             (price * quantity) AS line_item_total,
        #             timestamp
        #         FROM Orders
        #     """
        # )

        # stmtList = [{}]
            
        # if customer_name != "":
        #     stmt += "WHERE customer_name LIKE Concat('%', :customer_name, '%') "
        #     stmtList[0]['customer_name'] = customer_name
        #     if potion_sku != "":
        #         stmt += "AND item_sku LIKE Concat('%', :item_sku, '%') "
        #     stmtList[0]['item_sku'] = potion_sku
        # else:
        #     if potion_sku != "":
        #         stmt += "WHERE item_sku LIKE Concat('%', :item_sku, '%') "
        #     stmtList[0]['item_sku'] = potion_sku
            

        # stmt += """
        #         ORDER BY :sort_col :sort_order
        #         LIMIT 5
        #         """
        # stmtList[0]['sort_col'] = sort_col.value
        # stmtList[0]['sort_order'] = sort_order.value
        
        
        #
        
        stmt = (
            f"""
                SELECT
                    carts.customer AS customer_name,
                    potions.item_sku AS item_sku,
                    cart_items.quantity AS quantity,
                    cart_items.quantity * potions.price AS line_item_total,
                    carts.created_at AS timestamp
                FROM 
                    carts
                JOIN cart_items on carts.cart_id = cart_items.cart_id
                JOIN potions on potions.potion_id = cart_items.item_id
                """
        )
        
        stmtList = [{}]
            
        if customer_name != "":
            stmt += "WHERE carts.customer ILIKE Concat('%', :customer_name, '%') "
            stmtList[0]['customer_name'] = customer_name
            if potion_sku != "":
                stmt += "AND potions.item_sku ILIKE Concat('%', :potion_sku, '%') "
            stmtList[0]['potion_sku'] = potion_sku
        else:
            if potion_sku != "":
                stmt += "WHERE potions.item_sku ILIKE Concat('%', :potion_sku, '%') "
            stmtList[0]['potion_sku'] = potion_sku
            

        stmt += f"""
                ORDER BY {sort_col.value} {sort_order.value}
                """
        
        
        previous = ""
        next = ""
        offset = 0

        if search_page != "":
            offset = (int(search_page)) * 5
            stmt += "OFFSET :offset "
            stmtList[0]['offset'] = offset
            if int(search_page) > 0:
                previous = "%d" % (int(search_page) - 1)
        
        data = connection.execute(sqlalchemy.text(stmt), stmtList).all()

        if len(data) > offset:
            next = "%d" % (int(search_page) + 1)
            
        i = 0
        finalList = []

        
        while i < 5 and offset + i < len(data):
            finalList.append(
                {
                    "line_item_id": offset + i,
                    "item_sku": "%d %s" % (data[i].quantity, data[i].item_sku),
                    "customer_name": data[i].customer_name,
                    "line_item_total": data[i].line_item_total,
                    "timestamp": data[i].timestamp
                }
            )
            i += 1
                                
        # Customer name from carts.customer
        # Item sku from cart_item associated with customer name's cart_id
        # gold = price from potions table * quantity from cart_item
        # FROM carts 
        # JOIN cart_items ON cart_id = cart_id
        # JOIN potions on potion_id = item_id
    
    return {
        "previous": previous,
        "next": next,
        "results": finalList
    }

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
        cart_id = connection.execute(sqlalchemy.text(
                                        """
                                            INSERT INTO carts (customer)
                                            VALUES (:customer)
                                            RETURNING carts.cart_id
                                        """),
                                        [{
                                          'customer': new_cart.customer
                                        }]).scalar()
    
    return {"cart_id": cart_id}


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