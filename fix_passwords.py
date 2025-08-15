from pymongo import MongoClient
import bcrypt

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['family_tree_db']
users_collection = db['users']

# Update all passwords
for user in users_collection.find():
    if isinstance(user['password'], str):  # If the password is stored as a string
        new_hashed_password = bcrypt.hashpw(user['password'].encode('utf-8'), bcrypt.gensalt())
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'password': new_hashed_password}}
        )
print("All passwords updated successfully.")
