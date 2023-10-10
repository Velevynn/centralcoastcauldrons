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

#TODO:
# Create dictionary to track cart-ids.
# cart-id is key
# cart class (containing shopping info) is value
global cartDict
cartDict = {}
global counter
counter = 0

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    
    # create cart
    # add it to cartDict
    # return cartID
    # hashID = hash(new_cart.customer)
    global cartDict
    global counter
    counter += 1
    cartDict[counter] = [new_cart.customer, counter, [], 0]
    
    
    # with db.engine.begin() as connection:
    #     connection.execute(sqlalchemy.text(f"INSERT INTO carts (id, customer) VALUES ({counter}, {new_cart.customer})"))
    
    return {"cart_id": counter}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    # use cart_id as key to get cart object instance from cartDict
    # return cartDict
    global cartDict
    # with db.engine.begin() as connection:
    #     result = connection.execute(sqlalchemy.text(f"SELECT id, customer FROM carts"))
    #     fr = result.first()
    #     id = fr.id
        
    #     return {cart_id: id}
        
    return {cart_id: cartDict[cart_id]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    # return single cart id + object pair
    cartPair = get_cart(cart_id)
    cart = cartPair.get(cart_id)
    # modify items list to add item name and quantities
            
    print(item_sku, cart_item.quantity)
    if any(item[0] == item_sku for item in cart[2]):
        for item in cart[2]:
            if item[0] == item_sku:
                item[1].quantity += cart_item.quantity
    else:
        cart[2].append([item_sku, cart_item])
        
    
    
    #return cart
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    # get cart from cart_id
    print(cart_checkout.payment)
    cartPair = get_cart(cart_id)
    cart = cartPair.get(cart_id)
    
    # iterate through cart item list and add up total potion quantity
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, gold FROM global_inventory"))
        fr = result.first()
        
        currRed = fr.num_red_potions
        currGreen = fr.num_green_potions
        currBlue = fr.num_blue_potions
        currGold = fr.gold
        
        redPrice = 30
        greenPrice = 30
        bluePrice = 40
        sold = 0
        newGold = 0
        
        itemList = cart[2]
        print("before")
        print("r:", currRed, "g:", currGreen, "b:", currBlue, "gold:", currGold)
    
        for item in itemList:
            if item[0] == "RED_POTION_0":
                if currRed >= item[1].quantity:
                    currRed -= item[1].quantity
                    sold += item[1].quantity
                    newGold += item[1].quantity * redPrice
                else:
                    sold += currRed
                    newGold += currRed * redPrice
                    currRed = 0

            if item[0] == "GREEN_POTION_0":
                if currGreen >= item[1].quantity:
                    currGreen -= item[1].quantity
                    sold += item[1].quantity
                    newGold += item[1].quantity * greenPrice
                else:
                    sold += currGreen
                    newGold += currGreen * greenPrice
                    currGreen = 0

            if item[0] == "BLUE_POTION_0":
                if currBlue >= item[1].quantity:
                    currBlue -= item[1].quantity
                    sold += item[1].quantity
                    newGold += item[1].quantity * bluePrice
                else:
                    sold += currBlue
                    newGold += currBlue * bluePrice
                    currBlue = 0

        currGold += newGold
        print("after")
        print("r:", currRed, "g:", currGreen, "b:", currBlue, "gold:", currGold)
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {currRed}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {currGreen}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {currBlue}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {currGold}"))
        
        return {"total_potions_bought": sold, "total_gold_paid": newGold}
