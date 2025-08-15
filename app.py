from flask import Flask, Response, render_template, request, redirect, session, flash, url_for, jsonify
import json
from flask_pymongo import PyMongo
import bcrypt
from PIL import Image  # Import Image from Pillow for image validation
from bson.objectid import ObjectId  # Required for MongoDB ObjectId conversion
import os
from werkzeug.utils import secure_filename
import base64
from bson import ObjectId
from PIL import Image
from io import BytesIO

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace this with a strong secret key

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/your_database_name"
mongo = PyMongo(app)
users_collection = mongo.db.users
family_collection = mongo.db.family_members  # Collection for family tree data
photos_collection = mongo.db.photos  # Collection for storing photo filenames
videos_collection = mongo.db.videos  # Collection for storing video filenames

# File Upload Configuration
PHOTO_UPLOAD_FOLDER = 'static/uploads/photos'
VIDEO_UPLOAD_FOLDER = 'static/uploads/videos'

# Ensure upload folders exist
os.makedirs(PHOTO_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_UPLOAD_FOLDER, exist_ok=True)

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
    family_members = list(family_collection.find({'user_id': session['user_id']}))

    # Fetch uploaded photos and videos
    photos = list(photos_collection.find({'user_id': session['user_id']}))
    videos = list(videos_collection.find({'user_id': session['user_id']}))

    return render_template('dashboard.html', email=email, family_members=family_members, photos=photos, videos=videos)


# ------------------------- UPLOAD PHOTO -------------------------


@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file selected.', 'error')
            return redirect('/dashboard')

        files = request.files.getlist('photo')  # Allows multiple file selection

        allowed_extensions = {'jpg','jpeg', 'png', 'gif'}
        
        for file in files:
            if file.filename == '':
                flash('No selected file.', 'error')
                continue

            extension = file.filename.rsplit('.', 1)[-1].lower()
            if extension not in allowed_extensions:
                flash('Invalid file type. Please upload JPG, JPEG, WEBP, PNG, or GIF.', 'error')
                continue

            try:
                # Read file and convert to binary (base64)
                image_data = file.read()

                # Validate image using Pillow
                try:
                    img = Image.open(BytesIO(image_data))
                    img.verify()  # Ensure image integrity
                except Exception:
                    flash('Invalid image file.', 'error')
                    continue

                # Save photo details in MongoDB
                photos_collection.insert_one({
                    'user_id': session['user_id'],
                    'photo_data': base64.b64encode(image_data).decode('utf-8'),  # Store image as Base64
                    'content_type': file.content_type  # Store file type
                })
                flash('Photo uploaded successfully!', 'success')

            except Exception as e:
                flash(f'Error uploading photo: {str(e)}', 'error')

        return redirect('/dashboard')

    return render_template('upload_photo.html')



@app.route('/get_photo/<photo_id>')
def get_photo(photo_id):
    photo = photos_collection.find_one({'_id': ObjectId(photo_id)})
    
    if not photo:
        return "Photo not found", 404

    # Convert base64 to binary and send as response
    image_binary = base64.b64decode(photo['photo_data'])
    return Response(image_binary, mimetype=photo['content_type'])


# ------------------------- DELETE PHOTO -------------------------
@app.route('/delete_photo/<photo_id>', methods=['POST'])
def delete_photo(photo_id):
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    photo = photos_collection.find_one({'_id': ObjectId(photo_id), 'user_id': session['user_id']})
    if photo:
        try:
            os.remove(os.path.join(PHOTO_UPLOAD_FOLDER, photo['filename']))
        except Exception:
            flash('Error deleting file.', 'error')

        photos_collection.delete_one({'_id': ObjectId(photo_id)})
        flash('Photo deleted successfully!', 'success')
    else:
        flash('Photo not found or unauthorized.', 'error')

    return redirect('/dashboard')

# ------------------------- UPLOAD VIDEO -------------------------
import base64
from bson import ObjectId
from io import BytesIO

@app.route('/upload_video', methods=['GET', 'POST'])
def upload_video():
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No file selected.', 'error')
            return redirect('/dashboard')

        file = request.files['video']

        allowed_extensions = {'mp4', 'mov', 'avi', 'mkv'}
        
        if file.filename == '':
            flash('No selected file.', 'error')
            return redirect('/dashboard')

        extension = file.filename.rsplit('.', 1)[-1].lower()
        if extension not in allowed_extensions:
            flash('Invalid file type. Please upload MP4, MOV, AVI, or MKV.', 'error')
            return redirect('/dashboard')

        try:
            # Read file as binary and encode to Base64
            video_data = file.read()

            # Save video data in MongoDB
            videos_collection.insert_one({
                'user_id': session['user_id'],
                'video_data': base64.b64encode(video_data).decode('utf-8'),  # Store video as Base64
                'content_type': file.content_type  # Store file type
            })
            flash('Video uploaded successfully!', 'success')

        except Exception as e:
            flash(f'Error uploading video: {str(e)}', 'error')

        return redirect('/dashboard')

    return render_template('upload_video.html')


from flask import Response

@app.route('/get_video/<video_id>')
def get_video(video_id):
    video = videos_collection.find_one({'_id': ObjectId(video_id)})
    
    if not video:
        return "Video not found", 404

    # Convert Base64 back to binary and send as response
    video_binary = base64.b64decode(video['video_data'])
    return Response(video_binary, mimetype=video['content_type'])


# ------------------------- DELETE VIDEO -------------------------
@app.route('/delete_video/<video_id>', methods=['POST'])
def delete_video(video_id):
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    video = videos_collection.find_one({'_id': ObjectId(video_id), 'user_id': session['user_id']})

    if video:
        videos_collection.delete_one({'_id': ObjectId(video_id)})
        flash('Video deleted successfully!', 'success')
    else:
        flash('Video not found or unauthorized.', 'error')

    return redirect('/dashboard')




# ------------------------- ADD & VIEW FAMILY MEMBERS ROUTE -------------------------
@app.route('/member', methods=['GET', 'POST'])
def member():
    if 'user_id' not in session:  # Ensure user is logged in
        flash('You must log in first.', 'error')
        return redirect('/login')

    if request.method == 'POST':  # Add new family member
        member_name = request.form.get('name')
        relationship = request.form.get('relation')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')

        if not member_name or not relationship:
            flash('Please provide all required fields.', 'error')
            return redirect('/member')

        new_member = {
            'user_id': session['user_id'],
            'name': member_name,
            'relation': relationship,
            'phone': phone,
            'address': address
        }
        family_collection.insert_one(new_member)
        flash('Family member added successfully!', 'success')
        return redirect('/dashboard')

    family_members = list(family_collection.find({'user_id': session['user_id']}))
    return render_template('member.html', family_members=family_members)

# ------------------------- DELETE FAMILY MEMBER ROUTE -------------------------
@app.route('/delete_member/<member_id>', methods=['POST'])
def delete_member(member_id):
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    try:
        result = family_collection.delete_one({'_id': ObjectId(member_id), 'user_id': session['user_id']})
        if result.deleted_count > 0:
            flash('Family member deleted successfully!', 'success')
        else:
            flash('Member not found or unauthorized.', 'error')
    except Exception as e:
        flash('Error deleting member.', 'error')

    return redirect('/dashboard')



# ------------------------- PROFILE ROUTE -------------------------



@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You must log in first.', 'error')
        return redirect('/login')

    # Fetch only email from the database
    user = users_collection.find_one(
        {'_id': ObjectId(session['user_id'])},
        {'email': 1, '_id': 0}  # Fetch only email, exclude _id
    )

    if not user:
        flash('User not found.', 'error')
        return redirect('/dashboard')

    return render_template('profile.html', user=user)


# ------------------------- CHATBOT ROUTE -------------------------

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if 'user_id' not in session:
        return jsonify({"response": "Please log in to ask about your family members and media."})

    data = request.get_json()
    user_message = data.get("message", "").strip().lower()
    
    user_id = session['user_id']
    
    # Fetch user details from database
    user_data = users_collection.find_one({'_id': ObjectId(user_id)}, {'email': 1})
    family_members = list(family_collection.find({'user_id': user_id}))
    photo_count = photos_collection.count_documents({'user_id': user_id})
    video_count = videos_collection.count_documents({'user_id': user_id})

    response_message = "Sorry, I'm unable to reply."

    #  ** Greeting Response**
    if any(greet in user_message for greet in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        response_message = "Hello! How can I assist you today?"

    #  ** User's Email Query**
    elif any(keyword in user_message for keyword in ["email", "email id", "my email"]):
        response_message = f"Your registered email ID is {user_data.get('email', 'Not available')}."

    #  ** Query for Total Number of Family Members**
    elif any(keyword in user_message for keyword in ["how many family members", "number of family members", "total family members"]):
        response_message = f"You have {len(family_members)} family members recorded."
    
    #  ** Query for Number of Present Members**
    elif any(keyword in user_message for keyword in ["how many members are present", "number of members present", "total members present"]):
        present_members = [member for member in family_members if member.get('present', False)]
        response_message = f"Currently, {len(present_members)} family members are present."

    #  ** Query for Listing All Family Members with Relationships**
    elif any(keyword in user_message for keyword in ["list all family members", "name all family members", "who are my family members", "give all family member names"]):
        if family_members:
            family_details = ", ".join([f"{member['name']} ({member['relation']})" for member in family_members])
            response_message = f"Your family members are: {family_details}."
        else:
            response_message = "You haven't recorded any family members yet."

    #  ** Query for Listing All Relationships**
    elif any(keyword in user_message for keyword in ["relationship of all family members", "list relationships", "what are the relationships"]):
        if family_members:
            relationships = ", ".join(set(member['relation'] for member in family_members))
            response_message = f"The relationships in your family are: {relationships}."
        else:
            response_message = "You haven't recorded any family members yet."

    #  ** Query for Finding a Family Member by Relationship**
    elif any(keyword in user_message for keyword in ["who is my", "find my", "name of my", "give"]):
        relationship_match = [member['name'] for member in family_members if member['relation'].lower() in user_message]
        if relationship_match:
            response_message = f" {', '.join(relationship_match)}."
        else:
            response_message = "I couldn't find a family member with that relationship."

    #  ** Query for Finding a Present Family Member by Relationship**
    elif any(keyword in user_message for keyword in ["name of present", "who is present"]):
        for relation in ["son", "daughter", "father", "mother", "brother", "sister"]:  
            if relation in user_message:
                present_members = [member['name'] for member in family_members if member['relation'].lower() == relation and member.get('present', False)]
                if present_members:
                    response_message = f"The present {relation}(s) in your family: {', '.join(present_members)}."
                else:
                    response_message = f"There are no present {relation}(s) recorded."
                break

    #  ** Query for Counting Present Members by Relationship**
    elif any(keyword in user_message for keyword in ["how many present family members", "number of family members"]):
        for relation in ["son", "daughter", "father", "mother", "brother", "sister"]:
            if relation in user_message:
                present_count = sum(1 for member in family_members if member['relation'].lower() == relation and member.get('present', False))
                response_message = f"There are {present_count} present {relation}(s) recorded."
                break

    #  ** Query About a Specific Family Member**
    elif any(member['name'].lower() in user_message for member in family_members):
        matching_members = []
        for member in family_members:
            if member['name'].lower() in user_message:
                details = f"{member['name']} ({member['relation']})"
                if 'phone' in member:
                    details += f", Phone: {member['phone']}"
                if 'address' in member:
                    details += f", Address: {member['address']}"
                matching_members.append(details)

        if matching_members:
            response_message = "Here is what I found: " + ", ".join(matching_members)

    #  ** Queries About Media Uploads (Photos & Videos)**
    elif any(keyword in user_message for keyword in ["how many photos are present", "number of photos present", "total photos present"]):
        response_message = f"You have {photo_count} photos present."

    elif any(keyword in user_message for keyword in ["how many videos are present", "number of videos present", "total videos present"]):
        response_message = f"You have {video_count} videos present."

    elif "photos" in user_message or "pictures" in user_message:
        response_message = f"You have uploaded {photo_count} photos."

    elif "videos" in user_message:
        response_message = f"You have uploaded {video_count} videos."

    elif "do i have any photo" in user_message or "have i uploaded a photo" in user_message:
        response_message = "Yes, you have uploaded photos." if photo_count > 0 else "No, you haven't uploaded any photos yet."

    elif "do i have any video" in user_message or "have i uploaded a video" in user_message:
        response_message = "Yes, you have uploaded videos." if video_count > 0 else "No, you haven't uploaded any videos yet."

    return jsonify({"response": response_message})




# ------------------------- LOGOUT ROUTE -------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')

# ------------------------- MAIN FUNCTION -------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
