from flask import Flask, request, redirect, url_for, flash, send_from_directory, session, render_template
from flask_pymongo import PyMongo
from datetime import datetime
import os
from werkzeug.security import check_password_hash  # for secure password checking
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient
import os
import bcrypt
from bson.objectid import ObjectId
from flask import Flask, request, jsonify
app = Flask(__name__)
from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import traceback
import string
# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Make sure MongoDB is running on this address
db = client["college_library"]  # Your database name here
librarians_collection = db["librarians"]  # Reference to the 'librarians' collection
books_collection = db['books']  # Collection for books
collection = db['users']
issued_books_collection = db['issued_books']

app = Flask(__name__)

# MongoDB URI and Database setup
app.config["MONGO_URI"] = "mongodb://localhost:27017/college_library"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.urandom(24)  # Used for sessions
mongo = PyMongo(app)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Check if file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Route for serving the static admin login page
@app.route('/admin-login', methods=['GET'])
def admin_login_form():
    return send_from_directory('static/Admin', 'admin-login.html')


# Route to serve the static admin registration form
@app.route('/admin-home', methods=['GET'])
def admin_home():
    return send_from_directory('static/Admin', 'admin-home.html')


# Route to serve the static admin registration form
@app.route('/admin-register', methods=['GET'])
def admin_register_form():
    return send_from_directory('static/Admin', 'admin-register.html')

# Route for admin login page
@app.route('/', methods=['GET'])
def admin_index():
    return send_from_directory('static/Admin', 'index.html')

# Route for admin to add books
@app.route('/admin-add-books', methods=['GET'])
def admin_add_books_form():
    return send_from_directory('static/Admin', 'admin-add-books.html')

# Route for admin to add librarian
@app.route('/admin-add-librarian', methods=['GET'])
def admin_add_librarian_form():
    return send_from_directory('static/Admin', 'admin-add-librarian.html')

# Route for librarian login page
@app.route('/librarian-login', methods=['GET'])
def librarian_login_form():
    return send_from_directory('static/Librarian', 'librarian-login.html')

# Route for librarian home page
@app.route('/librarian-home', methods=['GET'])
def librarian_home_form():
    return send_from_directory('static/Librarian', 'librarian-home.html')

# Route for adding student or faculty by librarian
@app.route('/add-student-faculty', methods=['GET'])
def add_student_faculty_form():
    return send_from_directory('static/Librarian', 'add-student-faculty.html')

# Route for library books issue page
@app.route('/library-books-issue', methods=['GET'])
def library_books_issue_form():
    return send_from_directory('static/Librarian', 'library_books_issue.html')

# Route for adding library visit
@app.route('/add-library-visit', methods=['GET'])
def add_library_visit_form():
    return send_from_directory('static/Librarian', 'add-library-visit.html')

# Route for student/faculty login page
@app.route('/login', methods=['GET'])
def student_faculty_login_form():
    return send_from_directory('static/StudentFaculty', 'login.html')

# Route for student/faculty home page
@app.route('/home', methods=['GET'])
def student_faculty_home_form():
    return send_from_directory('static/StudentFaculty', 'home.html')


# Route for handling admin registration
@app.route('/admin-register', methods=['POST'])
def admin_register():
    # Extract form data
    username = request.form.get('username')
    password = request.form.get('password')  # Save the password directly
    name = request.form.get('name')
    email = request.form.get('email')
    mobile = request.form.get('mobile')
    profile_photo = request.files.get('profile_photo')

    # Check if the username already exists
    if mongo.db.admins.find_one({'username': username}):
        flash('Admin already exists')
        return redirect(url_for('admin_register_form'))

    # Save the profile photo if it exists
    profile_photo_filename = None
    if profile_photo:
        # Generate a secure filename with timestamp to avoid conflicts
        profile_photo_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{profile_photo.filename}"
        profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_photo_filename)

        try:
            profile_photo.save(profile_photo_path)
            print("Profile photo saved successfully:", profile_photo_filename)
            flash("Profile photo uploaded successfully.")
        except Exception as e:
            print("Error saving profile photo:", e)
            flash('Error saving profile photo')
            return redirect(url_for('admin_register_form'))

    # Insert a new admin record into the database
    new_admin = {
        'username': username,
        'password': password,  # Directly insert the original password
        'name': name,
        'email': email,
        'mobile': mobile,
        'profile_photo': profile_photo_filename,  # Save the filename in MongoDB
        'created_at': datetime.now()
    }

    mongo.db.admins.insert_one(new_admin)
    flash('Registration successful. Please log in.')
    return redirect(url_for('admin_login'))


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = request.args.get('error')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch the admin user from MongoDB
        admin = mongo.db.admins.find_one({"username": username})

        # Verify if admin exists and if the password matches
        if admin and admin['password'] == password:
            # Set session variables upon successful login
            session['username'] = admin['username']
            session['name'] = admin['name']
            session['email'] = admin['email']
            session['mobile'] = admin['mobile']
            session['profile_photo'] = admin['profile_photo']

            # Redirect to the admin profile page
            return redirect(url_for('admin_profile'))

        # Flash error message for failed login
        flash('Invalid username or password', 'error')
        return redirect(url_for('admin_login', error='invalid'))

    # Render the login page, passing any error message if present
    return render_template('admin_login.html', error=error)



# Admin logout route
@app.route('/admin-logout')
def admin_logout():
    # Clear session to log out admin
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('admin_login'))


@app.route('/admin-profile')
def admin_profile():
    # Ensure the admin is logged in
    if 'username' not in session:
        flash('Please log in to view the profile')
        return redirect(url_for('admin_login'))

    # Retrieve admin data from MongoDB (assuming the admin's username is stored in the session)
    admin_data = mongo.db.admins.find_one({'username': session.get('username')})

    if not admin_data:
        flash('Admin not found.')
        return redirect(url_for('admin_login'))

    # Construct the path for the profile photo stored in the 'uploads' folder
    if admin_data.get('profile_photo'):
        # Retrieve profile photo path
        profile_photo_path = url_for('uploaded_file', filename=admin_data['profile_photo'])
    else:
        # Default image if no profile photo exists
        profile_photo_path = url_for('uploaded_file', filename='default_profile.jpg')  # Use a default profile picture

    # Render the admin profile page with the profile photo and data
    return render_template('Admin/admin-profile.html', admin=admin_data, profile_photo_path=profile_photo_path)

# Serve files from the 'uploads' folder
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

from werkzeug.utils import secure_filename

@app.route('/update-profile', methods=['POST'])
def update_profile():
    # Ensure the admin is logged in
    if 'username' not in session:
        flash('Please log in to update your profile')
        return redirect(url_for('admin_login'))

    # Get the admin data from the session
    username = session.get('username')
    admin_data = mongo.db.admins.find_one({'username': username})

    if not admin_data:
        flash('Admin not found.')
        return redirect(url_for('admin_login'))

    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    mobile = request.form.get('mobile')

    # Handle the profile photo upload
    profile_photo = request.files.get('profile_photo')

    if profile_photo:
        # Secure the filename and save it directly
        filename = secure_filename(profile_photo.filename)
        profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Update the profile photo path in the database
        mongo.db.admins.update_one(
            {'username': username},
            {'$set': {'name': name, 'email': email, 'mobile': mobile, 'profile_photo': filename}}
        )
    else:
        # If no new profile photo is uploaded, just update other details
        mongo.db.admins.update_one(
            {'username': username},
            {'$set': {'name': name, 'email': email, 'mobile': mobile}}
        )

    # Flash success message and redirect to the profile page
    flash('Profile updated successfully')
    return redirect(url_for('admin_profile'))

librarians_collection = db["librarians"]  # Reference to the 'librarians' collection

@app.route('/admin-add-librarian', methods=['GET', 'POST'])
def admin_add_librarian():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        qualification = request.form['qualification']
        
        # Check if the username already exists in the database
        existing_librarian = librarians_collection.find_one({"username": username})
        if existing_librarian:
            return redirect(url_for('admin_add_librarian', error="Username already exists"))

        # Handle profile photo upload
        profile_photo = request.files.get('profile_photo')
        photo_filename = None
        
        if profile_photo and allowed_file(profile_photo.filename):
            # Secure the filename and save it in the uploads folder
            photo_filename = secure_filename(profile_photo.filename)
            photo_filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            
            # Save the file to the uploads folder
            profile_photo.save(photo_filepath)
        
        # Create the librarian data dictionary
        librarian_data = {
            "name": name,
            "username": username,
            "email": email,
            "mobile": mobile,
            "password": password,
            "qualification": qualification,
            "profile_photo": photo_filename  # Store only the filename in DB
        }

        # Insert data into MongoDB
        librarians_collection.insert_one(librarian_data)
        
        # Redirect or show a success message
        return redirect(url_for('admin_add_librarian', success="Librarian added successfully"))

    return render_template("admin_add_librarian.html")


# Route to view all librarians
@app.route('/admin-view-librarians')
def view_librarians():
    librarians = list(librarians_collection.find())
    return render_template('Admin/admin-view-librarians.html', librarians=librarians)

# Route to edit librarian
@app.route('/admin-edit-librarian/<username>', methods=['GET', 'POST'])
def edit_librarian(username):
    librarian = librarians_collection.find_one({'username': username})
    
    if librarian is None:
        return redirect(url_for('admin_home'))  # Redirect if librarian not found

    if request.method == 'POST':
        # Get the updated data from the form
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        qualification = request.form['qualification']
        password = request.form['password']
     
        
       
        
        # Update the librarian details in the database
        librarians_collection.update_one(
            {'username': username},
            {'$set': {
                'name': name,
                'email': email,
                'mobile': mobile,
                'qualification': qualification,
                'password': password,
               
            }}
        )
        
        return redirect(url_for('view_librarians'))  # Redirect to the list of librarians

    return render_template('Admin/admin-edit-librarian.html', librarian=librarian)



@app.route('/admin-add-book', methods=['POST'])
def add_book():
    try:
        # Get form data
        book_id = request.form['book_id']
        book_name = request.form['book_name']
        book_type = request.form['book_type']
        number_of_books = int(request.form['number_of_books'])
        availability = int(request.form['availability'])
        author = request.form['author']
        edition = request.form['edition']
        isbn = request.form['isbn']
        published_year = int(request.form['published_year'])

        # Check if book_id already exists in the database
        existing_book = books_collection.find_one({'book_id': book_id})
        if existing_book:
            return jsonify({'success': False, 'message': 'Book ID already exists!'}), 400

        # Handle file uploads
        cover_image = request.files['cover_image']
        preview_image_1 = request.files['preview_image_1']
        preview_image_2 = request.files['preview_image_2']
        preview_image_3 = request.files['preview_image_3']

        # Ensure files are valid and save them
        if cover_image and allowed_file(cover_image.filename):
            cover_image_filename = secure_filename(cover_image.filename)
            cover_image.save(os.path.join(app.config['UPLOAD_FOLDER'], cover_image_filename))
        else:
            return jsonify({'success': False, 'message': 'Invalid cover image file.'}), 400

        preview_image_1_filename = preview_image_2_filename = preview_image_3_filename = None
        
        if preview_image_1 and allowed_file(preview_image_1.filename):
            preview_image_1_filename = secure_filename(preview_image_1.filename)
            preview_image_1.save(os.path.join(app.config['UPLOAD_FOLDER'], preview_image_1_filename))
        
        if preview_image_2 and allowed_file(preview_image_2.filename):
            preview_image_2_filename = secure_filename(preview_image_2.filename)
            preview_image_2.save(os.path.join(app.config['UPLOAD_FOLDER'], preview_image_2_filename))
        
        if preview_image_3 and allowed_file(preview_image_3.filename):
            preview_image_3_filename = secure_filename(preview_image_3.filename)
            preview_image_3.save(os.path.join(app.config['UPLOAD_FOLDER'], preview_image_3_filename))

        # Create book data dictionary
        book_data = {
            'book_id': book_id,
            'book_name': book_name,
            'book_type': book_type,
            'number_of_books': number_of_books,
            'availability': availability,
            'author': author,
            'edition': edition,
            'isbn': isbn,
            'published_year': published_year,
            'cover_image': cover_image_filename,
            'preview_image_1': preview_image_1_filename,
            'preview_image_2': preview_image_2_filename,
            'preview_image_3': preview_image_3_filename,
        }

        # Insert book into MongoDB collection
        books_collection.insert_one(book_data)

        return jsonify({'success': True, 'message': 'Book added successfully!'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    


@app.route('/admin-view-books')
def view_books():
    # Retrieve all books from the MongoDB collection
    books = list(books_collection.find())
    return render_template('Admin/admin-view-books.html', books=books)

@app.route('/search-books', methods=['GET'])
def search_books():
    book_type = request.args.get('book_type')
    books = books_collection.find({'book_type': book_type})
    return render_template('Admin/admin-view-books.html', books=books)

@app.route('/search-books2', methods=['GET'])
def search_books_by_name():
    book_name = request.args.get('book_name')
    books = books_collection.find({'book_name': book_name})
    return render_template('Admin/admin-view-books.html', books=books)

@app.route('/search-books3', methods=['GET'])
def search_books_by_id():
    book_id = request.args.get('book_id')
    books = books_collection.find({'_id': book_id})
    return render_template('Admin/admin-view-books.html', books=books)

@app.route('/search-books4', methods=['GET'])
def search_books_by_author():
    author = request.args.get('author')
    books = books_collection.find({'author': author})
    return render_template('Admin/admin-view-books.html', books=books)

@app.route('/delete-book/<book_id>')
def delete_book(book_id):
    try:
        # Find the book with the given book_id and delete it
        result = books_collection.delete_one({'book_id': book_id})

        if result.deleted_count == 1:
            # Redirect to the page where all books are listed
            return redirect(url_for('view_books'))
        else:
            return "Book not found", 404
    except Exception as e:
        return f"Error occurred: {str(e)}", 500


# Route to render edit book page
@app.route("/admin-edit-book/<book_id>")
def edit_book(book_id):
    # Fetch the book details from MongoDB by book_id
    book = books_collection.find_one({"book_id": book_id})
    return render_template("Admin/admin-edit-book.html", book=book)
from werkzeug.utils import secure_filename

@app.route("/update-book/<book_id>", methods=["POST"])
def update_book(book_id):
    # Get updated data from the form
    book_name = request.form.get("book_name")
    book_type = request.form.get("book_type")
    author = request.form.get("author")
    edition = request.form.get("edition")
    isbn = request.form.get("isbn")
    published_year = int(request.form.get("published_year"))
    number_of_books = int(request.form.get("number_of_books"))
    availability = request.form.get("availability")

    # Handle image uploads (preview images and cover image)
    cover_image = request.files.get("cover_image")
    preview_image_1 = request.files.get("preview_image_1")
    preview_image_2 = request.files.get("preview_image_2")
    preview_image_3 = request.files.get("preview_image_3")

    # Fetch the current book data to keep unchanged fields
    current_book = books_collection.find_one({"book_id": book_id})

    # Handle cover image
    if cover_image:
        cover_image_filename = secure_filename(cover_image.filename)
        cover_image.save(f"./uploads/{cover_image_filename}")
    else:
        cover_image_filename = current_book.get("cover_image")

    # Handle preview image 1
    if preview_image_1:
        preview_image_1_filename = secure_filename(preview_image_1.filename)
        preview_image_1.save(f"./uploads/{preview_image_1_filename}")
    else:
        preview_image_1_filename = current_book.get("preview_image_1")

    # Handle preview image 2
    if preview_image_2:
        preview_image_2_filename = secure_filename(preview_image_2.filename)
        preview_image_2.save(f"./uploads/{preview_image_2_filename}")
    else:
        preview_image_2_filename = current_book.get("preview_image_2")

    # Handle preview image 3
    if preview_image_3:
        preview_image_3_filename = secure_filename(preview_image_3.filename)
        preview_image_3.save(f"./uploads/{preview_image_3_filename}")
    else:
        preview_image_3_filename = current_book.get("preview_image_3")

    # Prepare updated data
    updated_book = {
        "book_name": book_name,
        "book_type": book_type,
        "author": author,
        "edition": edition,
        "isbn": isbn,
        "published_year": published_year,
        "number_of_books": number_of_books,
        "availability": availability,
        "cover_image": cover_image_filename,
        "preview_image_1": preview_image_1_filename,
        "preview_image_2": preview_image_2_filename,
        "preview_image_3": preview_image_3_filename,
    }

    # Update the book in the database
    result = books_collection.update_one({"book_id": book_id}, {"$set": updated_book})

    # Check if the update was successful
    if result.modified_count > 0:
        return redirect(url_for("view_books", success="Book details updated successfully"))
    else:
        return redirect(url_for("view_books", error="Failed to update book details"))




@app.route('/librarian-login', methods=['GET', 'POST'])
def librarian_login():
    error = request.args.get('error')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch the librarian document from MongoDB using the username
        librarian = librarians_collection.find_one({"username": username})

        # Verify if the librarian exists and if the password matches
        if librarian and librarian['password'] == password:
            # Set session variables upon successful login
            session['username'] = librarian['username']
            session['name'] = librarian['name']
            session['email'] = librarian['email']
            session['password'] = librarian['password']
            session['mobile'] = librarian['mobile']
            session['qualification'] = librarian['qualification']
            session['profile_photo'] = librarian.get('profile_photo', 'default_profile.jpg')  # Default if missing

            # Redirect to the librarian profile page
            return redirect(url_for('librarian_profile'))

        # Redirect back with an error message if login fails
        return redirect(url_for('librarian_login', error='invalid'))

    return render_template('librarian_login.html', error=error)
from flask import send_from_directory
@app.route('/librarian-profile')
def librarian_profile():
    # Check if the librarian is logged in
    if 'username' not in session:
        return redirect(url_for('librarian_login'))  # Redirect to login if not logged in
    
    # Retrieve librarian's profile data from session
    librarian_data = {
        'name': session.get('name'),
        'email': session.get('email'),
        'mobile': session.get('mobile'),
        'qualification': session.get('qualification'),  # Add qualification field
        'profile_photo': session.get('profile_photo'),
        'password': session.get('password'),
       
    }

    # Default profile photo if not available
    if not librarian_data['profile_photo']:
        librarian_data['profile_photo'] = 'default_profile.jpg'  # Update as needed
    
    # Construct profile photo URL
    profile_photo_path = url_for('uploaded_file', filename=librarian_data['profile_photo'])
    
    # Render profile page
    return render_template('Librarian/librarian_profile.html', librarian=librarian_data, profile_photo_path=profile_photo_path)

@app.route('/edit-librarian-profile', methods=['POST'])
def edit_librarian_profile():
    # Retrieve form data
    name = request.form['name']
    email = request.form['email']
    mobile = request.form['mobile']
    password = request.form['password']  # Consider hashing this password in production
    profile_photo = request.files.get('profilePhoto')

    # Handle file upload for profile photo
    if profile_photo:
        profile_photo_filename = secure_filename(profile_photo.filename)
        profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_photo_filename))
    else:
        profile_photo_filename = session.get('profile_photo')  # Use existing photo if no new file is uploaded

    # Update librarian's data in MongoDB using the username
    username = session.get('username')  # Assuming username is stored in session
    updated_data = {
        "name": name,
        "email": email,
        "mobile": mobile,
        "password": password,  # Ensure secure storage for passwords
        "profile_photo": profile_photo_filename
    }
    
    librarians_collection.update_one({"username": username}, {"$set": updated_data})

    # Update the session data with new values
    session['name'] = name
    session['email'] = email
    session['mobile'] = mobile
    session['profile_photo'] = profile_photo_filename

    # Redirect to the profile page
    return redirect(url_for('librarian_profile'))

# Route to handle the "Add Student/Faculty" form submission
@app.route('/add-student-faculty', methods=['POST'])
def add_student_faculty():
    try:
        # Retrieve form data
        name = request.form['name']
        username = request.form['username']
        user_type = request.form['type']
        gmail = request.form['gmail']
        mobile = request.form['mobile']
        address = request.form['address']
        password = request.form['password']
        branch = request.form['branch']
        
        # Check if the username or email already exists in the database
        if collection.find_one({"$or": [{"username": username}, {"gmail": gmail}]}):
            return "Username or Gmail already exists.", 400

        # Handle profile photo upload
        profile_photo = request.files['profilePhoto']
        if profile_photo:
            filename = secure_filename(profile_photo.filename)  # Save only the filename
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
        else:
            filename = None  # No photo uploaded

        # Save to MongoDB
        user_data = {
            "name": name,
            "username": username,
            "type": user_type,
            "gmail": gmail,
            "mobile": mobile,
            "address": address,
            "password": password,
            "branch": branch,
            "profile_photo": filename  # Store only the filename in MongoDB
        }
        collection.insert_one(user_data)

        return "Student/Faculty added successfully.", 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    

@app.route('/view-users')
def view_users():
    users = list(collection.find())  # Fetch all users from the database
    return render_template('Librarian/view_users.html', users=users)  # Pass 'users' to the template



@app.route('/edit-member/<username>', methods=['GET', 'POST'])
def edit_member(username):
    # Fetch user data from the database based on username
    user = collection.find_one({"username": username})

    if request.method == 'POST':
        # Get updated form data
        updated_name = request.form['name']
        updated_gmail = request.form['gmail']
        updated_mobile = request.form['mobile']
        updated_address = request.form['address']
        updated_branch = request.form['branch']

        # Handle profile photo upload
        profile_photo = request.files.get('profile_photo')

        if profile_photo and allowed_file(profile_photo.filename):
            # Save the new profile photo to the 'uploads' folder
            photo_filename = secure_filename(profile_photo.filename)
            photo_filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)

            # Ensure the 'uploads' folder exists, create if not
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            # Save the image directly
            profile_photo.save(photo_filepath)
            photo_filepath = photo_filename  # Only save the filename (not the full path)
        else:
            # Keep the existing photo if no new one is uploaded
            photo_filepath = user.get('profile_photo')

        # Update user record in the database
        collection.update_one(
            {"username": username},
            {"$set": {
                "name": updated_name,
                "gmail": updated_gmail,
                "mobile": updated_mobile,
                "address": updated_address,
                "branch": updated_branch,
                "profile_photo": photo_filepath  # Store only the filename
            }}
        )

        # Redirect to the view users page or another appropriate page
        return redirect(url_for('view_users'))  # Adjust as per your route

    return render_template('Librarian/edit-member.html', user=user)


@app.route('/librarian-view-books')
def librarian_view_books():
    # Retrieve all books from the MongoDB collection
    books = list(books_collection.find())
    return render_template('Librarian/librarian-view-books.html', books=books)


@app.route('/search-bar1', methods=['GET'])
def search_book():
    book_type = request.args.get('book_type')
    books = books_collection.find({'book_type': book_type})
    return render_template('Librarian/librarian-view-books.html', books=books)

@app.route('/search-bar2', methods=['GET'])
def search_books_name():
    book_name = request.args.get('book_name')
    books = books_collection.find({'book_name': book_name})
    return render_template('Librarian/librarian-view-books.html', books=books)

@app.route('/search-bar3', methods=['GET'])
def search_books_id():
    book_id = request.args.get('book_id')
    books = books_collection.find({'_id': book_id})
    return render_template('Librarian/librarian-view-books.html', books=books)

@app.route('/search-bar4', methods=['GET'])
def search_books_author():
    author = request.args.get('author')
    books = books_collection.find({'author': author})
    return render_template('Librarian/librarian-view-books.html', books=books)




# Replace student_faculty_collection with collection
collection = db['users']
library_visit_collection = db['LibraryVisit']

# Helper function to calculate time difference in HH:MM:SS
def calculate_time_difference(start_time, end_time):
    start = datetime.strptime(start_time, "%H:%M:%S")
    end = datetime.strptime(end_time, "%H:%M:%S")
    time_diff = end - start
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Route to handle library visit logging
@app.route('/add-library-visit', methods=['POST'])
def add_library_visit():
    try:
        username = request.json.get('username')
        current_date = datetime.now().strftime("%Y-%m-%d")  # Format: YYYY-MM-DD
        current_time = datetime.now().strftime("%H:%M:%S")  # Format: HH:MM:SS

        # Check if the username exists in the users collection
        user = collection.find_one({'username': username})
        if not user:
            return jsonify({'error': 'Invalid username'}), 400  # Send error message

        # Check for an existing entry with the username and today's date, without an exit time
        visit = library_visit_collection.find_one({'username': username, 'visit_date': current_date, 'exit_time': None})

        if visit:
            # If found, update the exit time and calculate time spent
            time_spent = calculate_time_difference(visit['entry_time'], current_time)
            library_visit_collection.update_one(
                {'_id': visit['_id']},
                {'$set': {'exit_time': current_time, 'time_spent': time_spent}}
            )
            return jsonify({'message': 'Exit time updated successfully with time spent in library.'})  # Send success message
        else:
            # Otherwise, create a new entry with the entry time
            new_visit = {
                'username': username,
                'visit_date': current_date,
                'entry_time': current_time
            }
            library_visit_collection.insert_one(new_visit)
            return jsonify({'message': 'Entry time logged successfully.'})  # Send success message

    except Exception as error:
        print(f"Error logging visit: {error}")
        return jsonify({'error': 'An error occurred while logging the visit.'}), 500  # Send error message
    

@app.route('/view-library-visits')
def library_visits():
    # Assuming you're using MongoDB and 'library_visit_collection' stores the library visit data
    library_visit_collection = db['LibraryVisit']  # Reference to the collection storing the library visits
    visits = list(library_visit_collection.find())  # Fetch all the visits from the collection
    
    # Pass the visits data to the template
    return render_template('Librarian/view-library-visits.html', visits=visits)



# Function to generate a random 6-character alphanumeric ID for issued books
def generate_issued_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Route to issue or return a book
@app.route('/issue-book', methods=['POST'])
def issue_book():
    data = request.get_json()

    username = data.get('username')
    book_id = data.get('bookid')
    issued_id = data.get('issuedId')

    try:
        # Check if the user exists
        user = collection.find_one({"username": username})
        if not user:
            return jsonify({"message": "Invalid username"}), 400

        # Check if the book exists
        book = books_collection.find_one({"book_id": book_id})
        if not book:
            return jsonify({"message": "Book not found"}), 404

        # Check if the user is returning the book
        existing_issued_book = issued_books_collection.find_one({
            "username": username,
            "bookId": book_id,
            "returnDate": None  # This means the book is still not returned
        })

        if existing_issued_book:
            # Calculate fine if returning late
            return_limit_date = existing_issued_book["returnLimitDate"]
            current_date = datetime.now()
            fine = 0

            if current_date > return_limit_date:
                days_late = (current_date - return_limit_date).days
                fine = days_late * 5  # Assuming fine of $5 per day late

            # Update book status to "Returned"
            issued_books_collection.update_one(
                {"_id": existing_issued_book["_id"]},
                {"$set": {
                    "returnDate": current_date,
                    "fine": fine,
                    "status": "Returned"
                }}
            )

            # Increment the book's availability
            books_collection.update_one(
                {"book_id": book_id},
                {"$inc": {"availability": 1}}
            )

            return jsonify({
                "message": f"Book returned successfully!{' Fine amount: $' + str(fine) if fine > 0 else ''}"
            })

       
        # Check if the user has any unreturned books
        unreturned_book = issued_books_collection.find_one({
            "username": username,
            "returnDate": None  # Any book that is not returned yet
        })
        
        if unreturned_book:
         # Check if the unreturned book is damaged
            if unreturned_book.get("status") == "Damaged":
              return jsonify({"message": "You cannot issue a new book because you have a damaged book that hasn't been returned yet."}), 400
            else:
        # Book is unreturned but not marked as damaged
              return jsonify({"message": "You cannot issue a new book until you return the previous one."}), 400

        # Check if there are available copies of the book
        if book["availability"] <= 0:
            return jsonify({"message": "No copies available for this book"}), 400

        # Calculate the return limit date (10 days from issue date)
        return_limit_date = datetime.now() + timedelta(days=10)

        # Issue the book
        issued_book = {
            "issuedId": issued_id or generate_issued_id(),
            "username": username,
            "bookId": book_id,
            "issuedDate": datetime.now(),
            "returnLimitDate": return_limit_date,
            "status": 'Issued'
        }

        # Save the issued book details
        issued_books_collection.insert_one(issued_book)

        # Decrement the book's availability
        books_collection.update_one(
            {"book_id": book_id},
            {"$inc": {"availability": -1}}
        )

        return jsonify({"message": "Book issued successfully!"})

    except Exception as e:
        print(f"Error issuing or returning book: {e}")
        return jsonify({"message": "Internal Server Error"}), 500



@app.route('/view-issued-books')
def view_issued_books():
    try:
        # Fetch all issued books from the 'issued_books' collection
        issued_books = list(issued_books_collection.find())

        # Convert datetime fields to string for easier rendering in HTML
        for book in issued_books:
            book['issuedDate'] = book['issuedDate'].strftime('%Y-%m-%d') if book['issuedDate'] else 'N/A'
            book['returnLimitDate'] = book['returnLimitDate'].strftime('%Y-%m-%d') if book['returnLimitDate'] else 'N/A'
            book['returnDate'] = book['returnDate'].strftime('%Y-%m-%d') if book['returnDate'] else 'Not Returned'

        return render_template('Librarian/view-issued-books.html', issued_books=issued_books)

    except Exception as e:
        print(f"Error fetching issued books: {e}")
        return render_template('Librarian/view-issued-books.html', issued_books=issued_books)
  
@app.route('/update-status', methods=['POST'])
def update_status():
    data = request.get_json()
    issued_id = data.get('issuedId')
    status = data.get('status')

    try:
        # Find the issued book record by issuedId
        issued_book = issued_books_collection.find_one({"issuedId": issued_id})
        if not issued_book:
            return jsonify({"message": "Issued book not found"}), 404

        # Prepare the update fields
        update_fields = {"status": status}

        # Set the returnDate if the status is 'Returned', or reset if 'Damaged'
        if status == 'Returned':
            update_fields["returnDate"] = datetime.now()
        elif status == 'Damaged':
            update_fields["returnDate"] = None

        # Update the issued book status and save
        result = issued_books_collection.update_one(
            {"issuedId": issued_id},
            {"$set": update_fields}
        )

        # Check if the document was updated successfully
        if result.matched_count > 0:
            return jsonify({"message": "Status updated successfully"})
        else:
            return jsonify({"message": "Failed to update status"}), 500

    except Exception as e:
        print(f"Error updating status: {e}")
        return jsonify({"message": "Internal Server Error"}), 500
    

@app.route('/librarian-logout')
def librarian_logout():
    # Clear the session
    session.clear()

    # Redirect to the login page
    return redirect(url_for('librarian_login'))

@app.route('/user-login', methods=['POST'])
def user_login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Check for user credentials in the database
    user = collection.find_one({"username": username, "password": password})
    if user:
        session['username'] = user['username']  # Save username in session for logged-in user
        # Send the profile URL in the response
        return jsonify({"message": "Login successful", "redirect_url": url_for('user_profile')}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401



@app.route('/user-profile')
def user_profile():
    if 'username' not in session:
        return redirect(url_for('student_faculty_login_form'))  # Redirect to login if not logged in

    # Retrieve user details from the database
    user = collection.find_one({"username": session['username']})

    # Set default profile photo if not available
    if not user.get('profile_photo'):
        user['profile_photo'] = 'default_profile.jpg'  # Update with your default photo path

    # Construct profile photo URL
    profile_photo_path = url_for('uploaded_file', filename=user['profile_photo'])
    
    # Render profile page
    return render_template('StudentFaculty/user-profile.html', user=user, profile_photo_path=profile_photo_path)



@app.route('/logout')
def user_logout():
    # Clear the session (remove the 'username' key specifically)
    session.pop('username', None)

    # Optionally, you can also clear all session data with session.clear(), but removing the specific key is safer
    # session.clear()

    # Redirect to the login page
    return redirect(url_for('student_faculty_login_form'))  # Redirect to login page (use your correct route name)

@app.route('/user-view-books')
def user_view_books():
    # Retrieve all books from the MongoDB collection
    books = list(books_collection.find())
    return render_template('StudentFaculty/user-view-books.html', books=books)


@app.route('/search-1', methods=['GET'])
def search_1():
    book_type = request.args.get('book_type')
    books = books_collection.find({'book_type': book_type})
    return render_template('StudentFaculty/user-view-books.html', books=books)

@app.route('/search-2', methods=['GET'])
def search_2():
    book_name = request.args.get('book_name')
    books = books_collection.find({'book_name': book_name})
    return render_template('StudentFaculty/user-view-books.html', books=books)

@app.route('/search-3', methods=['GET'])
def search_book_id():
    book_id = request.args.get('book_id')
    books = books_collection.find({'_id': book_id})
    return render_template('StudentFaculty/user-view-books.html', books=books)

@app.route('/search-4', methods=['GET'])
def search_book_author():
    author = request.args.get('author')
    books = books_collection.find({'author': author})
    return render_template('StudentFaculty/user-view-books.html', books=books)



@app.route('/user-library-visits', methods=['GET'])
def user_library_visits():
    try:
        # Get the username from the session (assuming the user is logged in)
        username = session.get('username')

        if not username:
            return redirect(url_for('login'))  # Redirect to login if the user is not logged in

        # Retrieve library visits for the logged-in user
        visits_cursor = library_visit_collection.find({'username': username})

        # If no visits are found, return an empty list or a message
        visits_list = list(visits_cursor)  # Convert cursor to list

        if not visits_list:
            return render_template('Student/Faculty/user-library-visits.html', visits=[], message="No library visits found.")

        # Prepare the visits data to pass to the template
        formatted_visits = []
        for visit in visits_list:
            visit_data = {
                'visit_date': visit['visit_date'],
                'entry_time': visit['entry_time'],
                'exit_time': visit.get('exit_time', 'N/A'),  # Default to 'N/A' if exit_time is not available
                'time_spent': visit.get('time_spent', 'N/A')  # Default to 'N/A' if time_spent is not available
            }
            formatted_visits.append(visit_data)

        # Render the template with the visits data
        return render_template('StudentFaculty/user-library-visits.html', visits=formatted_visits)

    except Exception as error:
        print(f"Error retrieving library visits: {error}")
        # In case of an error, render the template with an error message
        return render_template('StudentFaculty/user-library-visits.html', visits=[], message="An error occurred while retrieving your visits.")

@app.route('/books-taken', methods=['GET'])
def books_taken():
    # Get the username of the logged-in user from the session
    username = session.get('username')  # Assuming the logged-in username is stored in the session

    if not username:
        # If the user is not logged in, redirect to the login page
        return redirect('/login')

    # Find all issued books for the logged-in user (no filter for returnDate)
    issued_books = issued_books_collection.find({"username": username})  # Get all issued books for the user

    # Convert MongoDB Cursor to a list of books
    issued_books_list = []
    for book in issued_books:
        # Ensure that the dates are properly formatted as strings
        issued_date = book["issuedDate"].strftime('%Y-%m-%d') if isinstance(book["issuedDate"], datetime) else book["issuedDate"]
        return_limit_date = book["returnLimitDate"].strftime('%Y-%m-%d') if isinstance(book["returnLimitDate"], datetime) else 'N/A'
        return_date = book.get("returnDate", 'N/A')
        fine = book.get("fine", 0)
        status = book.get("status", "N/A")

        issued_books_list.append({
            "issuedId": book["issuedId"],
            "bookId": book["bookId"],
            "issuedDate": issued_date,
            "returnLimitDate": return_limit_date,
            "returnDate": return_date,
            "fine": fine,
            "status": status
        })

    # Render the template with the list of issued books
    return render_template('StudentFaculty/books-taken.html', issuedBooks=issued_books_list)




if __name__ == '__main__':
    app.run(debug=True)