from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_pymongo import PyMongo
import bcrypt
import openai
from bson.objectid import ObjectId  # Required for MongoDB ObjectId conversion

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace this with a strong secret key

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/your_database_name"
mongo = PyMongo(app)
users_collection = mongo.db.users
family_collection = mongo.db.family_members  # Collection for family tree data

# ------------------------- HOME ROUTE -------------------------
@app.route('/')
def home():
    if 'user_id' in session:  # Check if user is logged in
        return redirect('/dashboard')
    return redirect('/login')

# ------------------------- SIGNUP ROUTE -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Check if the email already exists in the database
        if users_collection.find_one({'email': email}):
            flash('Email already exists. Please log in.', 'error')
            return redirect('/login')

        # Insert user into MongoDB
        users_collection.insert_one({'email': email, 'password': hashed_password})
        flash('Signup successful! Please log in.', 'success')
        return redirect('/login')

    return render_template('signup.html')

# ------------------------- LOGIN ROUTE -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email})

        if user:
            hashed_password = user['password']
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                session['user_id'] = str(user['_id'])
                session['email'] = email
                flash('Login successful!', 'success')
                return redirect('/dashboard')

        flash('Invalid email or password.', 'error')
        return redirect('/login')

    return render_template('login.html')

# ------------------------- DASHBOARD ROUTE -------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:  # Redirect if not logged in
        flash('You must log in first.', 'error')
        return redirect('/login')

    email = session.get('email', 'Unknown User')

    # Fetch family members for the logged-in user
    family_member = family_collection.find({'user_id': session['user_id']})
    return render_template('dashboard.html', email=email, family_members=family_member)

# ------------------------- ADD FAMILY MEMBER ROUTE -------------------------
@app.route('/add_member', methods=['POST'])
def add_member():
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    # Extract form data safely
    member_name = request.form.get('member_name')
    relationship = request.form.get('relationship')
    parent_name = request.form.get('parent_name', '')

    # Validate inputs
    if not member_name or not relationship:
        flash('Please provide all required fields.', 'error')
        return redirect('/dashboard')

    # Insert data into MongoDB collection
    family_member = {
        'user_id': session['user_id'],  # Associate with logged-in user
        'member_name': member_name,
        'relationship': relationship,
        'parent_name': parent_name
    }
    result = family_collection.insert_one(family_member)  # Add to DB

    flash('Family member added successfully!', 'success')
    return redirect('/dashboard')

# ------------------------- OVERVIEW ROUTE -------------------------
@app.route('/overview', methods=['GET', 'POST'])
def overview():
    if 'user_id' not in session:  # Ensure user is logged in
        flash('You must log in first.', 'error')
        return redirect('/login')

    if request.method == 'POST':  # Add new family member
        member_name = request.form.get('member_name')
        relationship = request.form.get('relationship')
        parent_name = request.form.get('parent_name', '')

        if not member_name or not relationship:  # Validate input
            flash('Please provide all required fields.', 'error')
            return redirect('/overview')

        # Insert new member into MongoDB
        new_member = {
            'user_id': session['user_id'],  # Associate with logged-in user
            'member_name': member_name,
            'relationship': relationship,
            'parent_name': parent_name
        }
        family_collection.insert_one(new_member)
        flash('Family member added successfully!', 'success')
        return redirect('/overview')  # Refresh the page to display updated data

    # Fetch all family members for the logged-in user
    family_members = list(family_collection.find({'user_id': session['user_id']}))
    return render_template('overview.html', family_members=family_members)

# ------------------------- PROFILE ROUTE -------------------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    # Fetch user details using ObjectId
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        flash('User not found.', 'error')
        return redirect('/logout')  # Logout if user record is missing

    if request.method == 'POST':
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        # Validate inputs
        if not new_email or not new_password:
            flash('Email and password are required.', 'error')
            return render_template('profile.html', user=user)

        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Update user details in the database
        users_collection.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'email': new_email, 'password': hashed_password}}
        )
        session['email'] = new_email  # Update session email
        flash('Profile updated successfully!', 'success')

    return render_template('profile.html', user=user)

# ------------------------- LOGOUT ROUTE -------------------------
@app.route('/logout')
def logout():
    session.clear()  # Clear session
    flash('You have been logged out.', 'info')
    return redirect('/login')

# ------------------------- CHATBOT ROUTES -------------------------
@app.route('/chatbot')
def chatbot():
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')
    return render_template('chatbot.html')

@app.route('/chatbot-response', methods=['POST'])
def chatbot_response():
    user_input = request.json.get('message')

    # OpenAI API call for chatbot responses
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"User: {user_input}\nAI:",
        max_tokens=150
    )
    return jsonify({'response': response.choices[0].text.strip()})

# ------------------------- MAIN FUNCTION -------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
