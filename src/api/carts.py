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

class Cart():
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)
    
    def __init__(self, customer, cart_id, items, checkout):
        self.customer = customer
        self.cart_id = cart_id
        self.items = items
        self.checkout = checkout
        
    def __repr__(self):
        return f"Cart(customer={self.customer}, id={self.id}, items={self.items})"

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
    
    return {"cart_id": counter}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    # use cart_id as key to get cart object instance from cartDict
    # return cartDict
    global cartDict
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
    cart[2].append([item_sku, cart_item])
    
    
    #return cart
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    # get cart from cart_id
    cartPair = get_cart(cart_id)
    cart = cartPair.get(cart_id)
    
    # iterate through cart item list and add up total potion quantity
    quantity = 0
    for item in cart[2]:
        quantity += item[1].quantity
    
    # multiply quantity by cost
    cost = quantity * 50
    
    with db.engine.begin() as connection:
        currPotions = connection.execute(sqlalchemy.text(f"SELECT num_red_potions FROM global_inventory"))
        currPotions = currPotions.scalar()
        
        if currPotions <= 0:
            return {"total_potions_bought": 0, "total_gold_paid": 0}
        
        finalPotions = currPotions - quantity
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {finalPotions}"))
        
        currGold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory"))
        currGold = currGold.scalar()
        finalGold = currGold + cost
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {finalGold}"))
        
        return {"total_potions_bought": quantity, "total_gold_paid": cost}
