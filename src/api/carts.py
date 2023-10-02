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

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    return {"cart_id": 1}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    
    with db.engine.begin() as connection:
        numPotions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        numPotions = numPotions.scalar()
        
        if numPotions < 1:
            return {"total_potions_bought": 0, "total_gold_paid": 0}
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold+150"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions-1"))
    
    return {"total_potions_bought": 1, "total_gold_paid": 150}
