from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bson.objectid import ObjectId
from db import products_collection
from db import users_collection
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
    product_id: int
    quantity: int


class UserCart(BaseModel):
    user_id: int
    cart_id: int
    item: Item

class ProductModel(BaseModel):
    stock:Item
    name: str
    description: str
    price: float
    

@app.get("/")
def get_home():
    return {"message": "Welcome to our E-commerce API"}



# List of sample products
@app.get("/products")
def get_products():
    # get all products from database
    products = products_collection.find().to_list()
    tidy__products =[]
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


#  User authentication routes
@app.post("/register")
def register_user(user: User):
    # insert user into database
    users_collection.insert_one(user.model_dump())
    # Checking if user with thesame details already exist
    for existing_user in users:
        if (
            existing_user["username"] == user.username
            or existing_user["email"] == user.email
        ):
            raise HTTPException(
                status_code=400, detail="Username or email already registered"
            )

    # Assigning a new ID and adding the user to the list

    new_id = len(users) + 1
    new_user = user.model_dump()
    new_user["id"] = new_id
    users.append(new_user)

    return {"message": "User registered successfully", "user": new_user}


@app.post("/login")
def login_user(user_name: str, user_password: str):
    # search through users to find a match
    for user in users:
        if (user["username"] == user_name or user["email"] == user_name) and user[
            "password"
        ] == user_password:
            return {"message": "Login successful"}

    # If no match is found
    raise HTTPException(status_code=401, detail="Invalid credentials")


# Shopping cart routes
@app.post("/cart")
def add_to_cart(user_cart: UserCart):
    cart = []
    get_product_by_id(user_cart.item.product_id)
    cart.append(user_cart.model_dump())
    return {"message": "Item added to cart", "cart": cart}
