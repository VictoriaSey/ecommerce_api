from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bson.objectid import ObjectId
from db import products_collection
from db import users_collection
from db import carts_collection
from utils import replace_mongo_id


app = FastAPI()

# A list to store my registered users
users = []


# Pydantic models for request
class User(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class Item(BaseModel):
    product_id: str
    quantity: int


class UserCart(BaseModel):
    user_id: int
    item: Item

class ProductModel(BaseModel):
    stock: int
    name: str
    description: str
    price: float

# Home route

@app.get("/")
def get_home():
    return {"message": "Welcome to our E-commerce API"}


# List of sample products
@app.get("/products")
def get_products():
    # get all products from database
    products = products_collection.find().to_list()
    tidy__products = []
    for product in products:
        product["id"] = str(product["_id"])
        del product["_id"]
        tidy__products.append(product)

    # return response
    return {"data": tidy__products}


@app.post("/products")
def post_product(product: ProductModel):
    # Insert product into database
    products_collection.insert_one(product.model_dump())
    # return response
    return {"message": "Product added successfully"}


@app.get("/products/{product_id}")
def get_product_by_id(product_id):
    # Get product from database by id
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    # return response
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"data": replace_mongo_id(product)}

@app.patch("/products/{product_id}")
def update_product(product_id: str, product_data: ProductModel):
    # Update product in database by id 
    get_product_by_id(product_id)
    updates_dict = product_data.model_dump()
    return{"message": "Product updated successfully", "data": updates_dict  }

@app.delete("/products/{product_id}")
def delete_product_by_id(product_id: str):
    # Delete product from database by id
    get_product_by_id(product_id)
    products_collection.delete_one({"_id": ObjectId(product_id)})
    return {"message": "Product deleted successfully"}

#  User authentication routes
@app.post("/register")
def register_user(user: User):
    # insert user into database
    users_collection.insert_one(user.model_dump())
    return {"message": "User registered successfully"}


@app.post("/login")
def login_user(user_name: str, user_password: str):
    # search through users to find a match
    user = users_collection.find_one(
        {
            "$or": [{"username": user_name}, {"email": user_name}],
            "password": user_password,
        }
    )
    # If a match is found
    if user:
        return {"message": "Login successful", "user": replace_mongo_id(user)}
    # If no match is found
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# Shopping cart routes
@app.post("/cart/{user_id}")
def add_to_cart(user_id: str, item: Item):
    try:
        product_object_id = ObjectId(item.product_id)
        product = products_collection.find_one({"_id": product_object_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    stock_info = product.get("stock", 0)
    if isinstance(stock_info, dict):
        available_stock = stock_info.get("quantity", 0)
    else:
        available_stock = stock_info if isinstance(stock_info, int) else 0
    if item.quantity > available_stock:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Only {product.get('stock', 0)} items left.")
    # check if user alrready has an item in their cart
    existing_cart_item = carts_collection.find_one(
        {"user_id": user_id, "product_id": item.product_id}
    )
    if existing_cart_item:
        new_quantity = existing_cart_item.get("quantity", 0) + item.quantity
        if new_quantity > product.get("stock", 0):
            raise HTTPException(status_code=400, detail="Adding this quantity would exceed available stock.")
        carts_collection.update_one(
            {"_id": existing_cart_item["_id"]},
            {"$set": {"quantity": new_quantity}},
        )
        return {"message": "Cart updated successfully"}
    else:
        new_cart_document = {
            "user_id": user_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
        }
        carts_collection.insert_one(new_cart_document)
        return {"message": "Item added to cart successfully"}
    

@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    # Retrieve user's cart from the database
    cart_items = list(carts_collection.find({"user_id": user_id}))

    if not cart_items:
        return {"message": "User's cart is empty"}
    
    enriched_cart_items = []
    grand_total = 0.0

#  Enrich cart items with product details
    for item in cart_items:
        try:
            product_id = ObjectId(item["product_id"])
        except Exception:
        # Skip this cart item if the product_id is invalid
            continue
        
    product = products_collection.find_one({"_id": product_id})
    
    if product:
        # Safely get price, default to 0.0 if not found
        price = product.get("price", 0.0)
        subtotal = price * item["quantity"]
        grand_total += subtotal
        
        enriched_cart_items.append({
            "cart_item_id": str(item["_id"]),
            "product_id": item["product_id"],
            "name": product.get("name"),
            "price": price,
            "quantity": item["quantity"],
            "subtotal": subtotal
        })
        
    return {
    "data": {
        "items": enriched_cart_items,
        "total_price": grand_total
    }
}

