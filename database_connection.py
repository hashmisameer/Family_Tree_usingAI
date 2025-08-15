import pymongo

# MongoDB connection string (adjust this for your local or cloud MongoDB)
MONGO_URI = "mongodb://localhost:27017"

# Connect to MongoDB
try:
    client = pymongo.MongoClient(MONGO_URI)
    # Check if the connection is successful
    print("Connected to MongoDB successfully!")
except Exception as e:
    print("Error connecting to MongoDB:", e)

# Create or connect to a database named "family_tree_db"
db = client["family_tree_db"]

# Create or connect to a collection named "family_members"
family_collection = db["family_members"]

# Sample function to insert data into MongoDB
def add_family_member(member):
    try:
        result = family_collection.insert_one(member)
        print("Family member added with ID:", result.inserted_id)
    except Exception as e:
        print("Error adding family member:", e)

# Example data to insert
member_data = {
    "name": "John Doe",
    "relation": "Father",
    "birthdate": "1970-05-14",
    "children": ["Jane Doe", "Sam Doe"]
}
{
    "name": "dvsd",
    "relation": "son",
    "birthdate": "1960-04-01",
    "children": ["wrg", "jjkh"]
}

# Insert sample data
add_family_member(member_data)

# Retrieve and print all family members
def fetch_family_members():
    members = family_collection.find()
    for member in members:
        print(member)

fetch_family_members()
