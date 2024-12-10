from flask import Flask, render_template, jsonify, request, redirect, url_for,  flash, session
from database import load_buyers_from_db, load_sellers_from_db, add_user_to_db, get_user_by_email, get_user_by_id, add_property_to_db, load_properties_from_db, delete_user_from_db, update_user_in_db, load_seller_properties_from_db, soldout_property, add_blog_to_db, load_blogs_from_db, get_properties_count_from_db, add_enquiry_to_db, get_enquiries_for_seller, store_verification_code, get_stored_verification_code, mark_user_as_verified, add_payment_to_db, check_email_or_phone_exists
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from werkzeug.utils import secure_filename  # Secure the File Uploads
from flask_mail import Mail, Message
import random
import string
from urllib.parse import quote_plus, quote  
from werkzeug.datastructures import CombinedMultiDict, ImmutableMultiDict
import json
import razorpay
from datetime import datetime
import shutil


app = Flask(__name__)

# Configure Flask-Mail for Gmail SMTP
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dreamestate1212@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'wcje wqik iquf pmsa'  # Your Gmail password (or App Password)
app.config['MAIL_DEFAULT_SENDER'] = 'dreamestate1212@gmail.com'

mail = Mail(app)


# Login (session):
app.secret_key = 'secret_key_1234'  #secure key
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect users to 'login' route if not authenticated

class User(UserMixin):
    def __init__(self, id, name, email, phone=None, role=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.role = role

    @staticmethod
    def from_db_row(row):
        return User(
            id=row['id'], 
            name=row['name'], 
            email=row['email'],  
            phone=row.get('phone'), 
            role=row.get('role')
        )
    
@login_manager.user_loader
def load_user(user_id):
    # Retrieve role from the session
    role = session.get('role')
    user_data = get_user_by_id(user_id, role)
    if user_data:
        return User.from_db_row(user_data)
    return None

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form.to_dict()  # Convert ImmutableMultiDict to a regular dict

        email = request.form['email']
        password = request.form['password']
        role = data.get('role')

        # Debug print to verify role
        print(f"Role received: {role}")

        # Check for missing fields
        if not email or not password or not role:
            flash('Missing required fields.')
            return render_template('login.html')  # Render login page with flash message

        # Validate user credentials
        user_data = get_user_by_email(email, role)
        if user_data and user_data['password'] == password:  # Basic check; use hashing in production
            user = User.from_db_row(user_data)
            login_user(user)
            session['role'] = role  # Store the role in the session
            return redirect(url_for('home'))  # Redirect to a protected route
        else:
            flash('Invalid email or password.')
            return render_template('login.html')  # Render login page with flash message

    return render_template('login.html')  # Render login page for GET requests



# @app.route('/login')
# def login():
#     return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    user_data = get_user_by_id(current_user.id, role) 
    return render_template('dashboard.html', user=user_data, role=role)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/')
def home():
    # Check if the user is logged in
    if current_user.is_authenticated:
        user_name = current_user.name 
        role = session.get('role')  # Get the role from the session
    else:
        user_name = None
        role = None

    return render_template('home.html', user_name=user_name, role=role)



@app.route('/set_flash_message', methods=['POST'])
def set_flash_message():
    data = request.json
    message = data.get('message')
    category = data.get('category', 'info')  # Default category is 'info'
    flash(message, category)
    return jsonify({'success': True})


@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/check-email', methods=['POST'])
def check_email():
    data = request.json
    email = data.get('email')
    phone = data.get('phone')
    role = data.get('role')
    
    email_exists = check_email_or_phone_exists(email, role)
    
    return jsonify({'exists': email_exists})

@app.route('/buyer/registration', methods=['POST'])
def register_user():
    data = request.form.to_dict()

    try:
        # Check if email or phone already exists in the database
        if check_email_or_phone_exists(data['email'], data['phone'], data['role']):
            flash('Email or phone number already exists. Please use different details.')
            return redirect(url_for('signup'))

        # Generate a verification code (random string)
        verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        # Send verification email
        email = data['email']
        send_verification_email(email, verification_code)

        # Store the verification code in the temporary verification table
        store_verification_code(email, data['role'], verification_code)

        # Store the data and verification code in the session
        session['registration_data'] = data
        session['verification_code'] = verification_code

        # Redirect to the verify_email route, passing the email and code
        return redirect(url_for('verify_email', email=email))

    except Exception as e:
        # Log the error 
        print(f"Registration error: {e}")
        flash('An error occurred during registration. Please try again.')
        return redirect(url_for('signup'))

@app.route('/verify-email')
def verify_email():
    # Get the email and code from the request arguments
    email = request.args.get('email')
    code = request.args.get('code')

    # Render the verify_email.html template, passing the email and code
    return render_template('verify_email.html', email=email, code=code)

@app.route('/verify/<email>/<code>', methods=['GET'])
def verify_account(email, code):
    # Retrieve the verification code for this email from the user_verifications table
    # stored_code = get_stored_verification_code(email)
    stored_code = session.get('verification_code')
    data = session.get('registration_data')
    
    if stored_code and stored_code == code:

        # Add the user data to the appropriate table (buyer or seller)
        add_user_to_db(data)

        print(f"stored_code: {stored_code}")
        print(f"code: {code}")

        # Mark the user as verified in the user_verifications table
        mark_user_as_verified(email)

        flash("Your account has been verified. You can now log in.")
        return redirect(url_for('login'))
    else:
        return "Invalid verification code", 400

def send_verification_email(email, verification_code):
    # Generate the correct URL with both email and code
    verification_url = url_for('verify_account', email=email, code=verification_code, _external=True)
    print(f"Generated verification URL: {verification_url}")  # Check generated URL

    msg = Message("Email Verification", recipients=[email])
    msg.body = f"Your verification code is {verification_code}."
    mail.send(msg)


# def send_verification_email(email, verification_code):
#     # encoded_email = quote(email)  # Encode email to ensure it's URL-safe
#     verification_url = url_for('verify_account', email=email, code=verification_code, _external=True)
#     print(f"Generated verification URL: {verification_url}")  # Debugging

#     msg = Message("Email Verification", recipients=[email])
#     msg.body = f"Your verification code is {verification_code}."
#     try:
#         mail.send(msg)
#     except Exception as e:
#         print(f"Error sending email: {e}")





 
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Fetch the admin user data by email and role
        user_data = get_user_by_email(email, 'admin')

        # Verify the user's credentials
        if user_data and user_data['password'] == password:
            user = User.from_db_row(user_data)
            login_user(user)
            session['role'] = 'admin'
            flash('Admin logged in successfully.')
            return redirect(url_for('admin'))
        else:
            flash('Invalid admin credentials.')
            return render_template('admin_login.html')

    return render_template('admin_login.html')
 



@app.route('/sell_property')
def sell_property():
    return render_template('sell_property.html')

UPLOAD_FOLDER = 'static/properties'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route('/submit_property', methods=['POST'])
# def submit_property():
#     # Check if the user is logged in
#     if not current_user.is_authenticated:
#         return redirect(url_for('login'))  # Redirect to login if not authenticated

#     # Retrieve form data
#     # property_type = request.form['property_type']
#     # address = request.form['address']
#     # rent = request.form['rent']
#     # price = request.form['price']
#     # property_images = request.files['property_images']

#     # Set the status internally 
#     status = 'not sold'

#     file = request.files['property_images']

#     # Check if a file was uploaded and if it's allowed
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(file_path)
        
#         # Save the property details to the database
#         data = {
#             'seller_id': current_user.id,  # Get seller_id from the current logged-in user
#             'type': request.form['property_type'],
#             'price': request.form['price'],
#             'rent': request.form['rent'],
#             'address': request.form['address'],
#             'city': request.form['city'],
#             'status': 'not sold',  # Default status
#             'photo': file_path  # Save the file path in the database
#         }

#         add_property_to_db(data)

#         return redirect(url_for('home')) 
    
#     else:
#         flash('Invalid file type')
#         return "File type not allowed"



@app.route('/properties')
@login_required
def properties():
    page = request.args.get('page', 1, type=int)
    items_per_page = 4

    # Retrieve filter parameters
    filters = {
        "type": request.args.get('type', ''),
        "price_min": request.args.get('price_min', type=int),
        "price_max": request.args.get('price_max', type=int),
        "rent_min": request.args.get('rent_min', type=int),
        "rent_max": request.args.get('rent_max', type=int),
        "city": request.args.get('city', ''),
        "sold_status": request.args.get('sold_status', default='not sold', type=str)
    }

    # Apply filters to count and load properties
    total_properties = get_properties_count_from_db(filters)
    property_list = load_properties_from_db(page, items_per_page, filters)

    total_pages = (total_properties + items_per_page - 1) // items_per_page
    if page > total_pages:
        page = total_pages

    return render_template('properties.html', properties=property_list, page=page, total_pages=total_pages, filters=filters)


@app.route('/send_enquiry', methods=['GET', 'POST'])
@login_required
def send_enquiry():
    # Retrieve the form data and current user details
    property_id = request.form['property_id']
    seller_id = request.form['seller_id']
    buyer_id = current_user.id  # Get the logged-in buyer's ID
    user_message = request.form['user_message']

    print(property_id, seller_id, buyer_id, user_message)
    # Store the inquiry in the enquires table
    add_enquiry_to_db(seller_id=seller_id, buyer_id=buyer_id, property_id=property_id, message=user_message)

    # Provide feedback to the user
    flash("Your enquiry has been sent successfully!", "success")
    return render_template('home.html')


@app.route('/seller_enquires')
def seller_enquires():
    role = session.get('role')
    user_data = get_user_by_id(current_user.id, role) 
    # Query to get enquiries for the current seller
    enquires = get_enquiries_for_seller(current_user.id)
    return render_template('seller_enquires.html', user=user_data, role=role, enquires=enquires)




#Admin:
@app.route('/admin')
def admin():
    buyers = load_buyers_from_db()
    sellers = load_sellers_from_db()
    return render_template('admin.html', buyers=buyers, sellers=sellers)


# @app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
# def edit_user(id):
#     # Fetch the role from the query parameters
#     role = request.args.get('role')


@app.route('/edit_user_form/<int:id>')
def edit_user_form(id):
    id = id
    return render_template('edit_user_from.html', id=id)


@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    data = request.form.to_dict()  # Convert ImmutableMultiDict to regular dict
    id = id
    role = session.get('role')
    # Ensure the user has the right to edit
    if role not in ['admin', 'buyer', 'seller']:
        return redirect(url_for('dashboard'))
    update_user_in_db(id, data, role)
    return redirect(url_for('dashboard'))


@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    # Fetch the role from the query parameters
    role = request.args.get('role')
    if role not in ['buyer', 'seller']:
        return redirect(url_for('dashboard'))
    delete_user_from_db(role, id)
    return redirect(url_for('admin'))



@app.route('/myproperties')
def myproperties():
    id = current_user.id
    role = session.get('role')
    property_list = load_seller_properties_from_db(id)  # Fetch the properties for current seller
    return render_template('seller_specific_properties.html', properties=property_list, role=role)


@app.route('/soldout/<int:property_id>')
@login_required
def soldout(property_id):
    soldout_property(property_id)
    return redirect(url_for('myproperties'))




@app.route('/write_blog')
@login_required
def write_blog():
    return render_template('write_blog.html')



@app.route('/blogs')
@login_required
def blogs():
    blog_list = load_blogs_from_db()
    return render_template('blogs.html', blogs=blog_list)



UPLOAD_FOLDER_BLOG = 'static/blogs_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER_BLOG'] = UPLOAD_FOLDER_BLOG

@app.route('/submit_blog',  methods=['POST'])
def submit_blog():
    # Retrieve form data
    # heading = request.form['heading']
    # content = request.form['content']
    # like = request.form['like_count']

    file = request.files['property_images']

    # Check if a file was uploaded and if it's allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER_BLOG'], filename)
        file.save(file_path)

        # Save the blog details to the database
        data = {
            'user_id': current_user.id,
            'heading': request.form['heading'],
            'content': request.form['content'],
            'like': request.form['like_count'],
            'photo': file_path  # Save the file path in the database
        }

        print(f"User ID: {data['user_id']}, Heading: {data['heading']}, Content: {data['content']}, Photo: {data['photo']}")

        add_blog_to_db(data)

        return redirect(url_for('home')) 
    
    else:
        flash('Invalid file type')
        return "File type not allowed"




# Configure Razorpay credentials
RAZORPAY_KEY_ID = 'rzp_test_FSiMV6Pb0lNpmj'
RAZORPAY_KEY_SECRET = 'mIcnh2bhhhBOJ7wOuvnSFLb5'


# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def generate_unique_filename(original_filename):
    """Generate a unique filename using timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(original_filename)
    return f"{name}_{timestamp}{ext}"

@app.route('/create_property_listing_order', methods=['POST'])
@login_required
def create_property_listing_order():
    try:
        # Create a dictionary with all form fields
        form_data = {
            'type': request.form.get('property_type'),  # Make sure this matches your form field name
            'price': request.form.get('price'),
            'rent': request.form.get('rent'),
            'address': request.form.get('address'),
            'city': request.form.get('city')
        }
        
        # Handle file separately
        if 'property_images' in request.files:
            file = request.files['property_images']
            if file and allowed_file(file.filename):
                # Generate unique filename
                unique_filename = generate_unique_filename(secure_filename(file.filename))
                
                # Create temporary directory if it doesn't exist
                temp_dir = os.path.join('static', 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Save file to temporary location with unique filename
                temp_path = os.path.join(temp_dir, unique_filename)
                file.save(temp_path)
                form_data['temp_file_path'] = temp_path
                form_data['original_filename'] = unique_filename

        # Store form data in session
        session['property_form_data'] = form_data

        # Create Razorpay Order
        amount = 10000  # Amount in paise (₹100)
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': f'property_listing_{current_user.id}',
            'notes': {
                'seller_id': current_user.id,
                'purpose': 'Property Listing Fee'
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        return jsonify({
            'key': RAZORPAY_KEY_ID,
            'amount': amount,
            'order_id': order['id'],
            'currency': 'INR',
            'name': 'Dream Estate',
            'description': 'Property Listing Fee',
            'prefill': {
                'name': current_user.name,
                'email': current_user.email
            }
        })
    
    except Exception as e:
        app.logger.error(f"Error creating order: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify_payment', methods=['POST'])
@login_required
def verify_payment():
    try:
        # Get payment verification details
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')

        # Verify payment signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            payment_status = 'success'
        except Exception as e:
            app.logger.error(f"Payment verification failed: {str(e)}")
            return jsonify({'error': 'Payment verification failed'}), 400

        if payment_status == 'success':
            # Retrieve property data from session
            property_data = session.get('property_form_data')
            if not property_data:
                return jsonify({'error': 'Property data not found'}), 400

            # Move file from temp to final location if it exists
            final_path = None
            if 'temp_file_path' in property_data:
                temp_path = property_data['temp_file_path']
                if os.path.exists(temp_path):
                    try:
                        # Ensure the destination directory exists
                        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                        
                        # Generate the destination path using the unique filename
                        final_path = os.path.join(
                            app.config['UPLOAD_FOLDER'], 
                            property_data['original_filename']
                        )
                        
                        # Use shutil.move instead of os.rename for cross-device operations
                        shutil.move(temp_path, final_path)
                        
                    except Exception as e:
                        app.logger.error(f"Error moving file: {str(e)}")
                        # Clean up temp file if move fails
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        return jsonify({'error': 'Error processing image file'}), 500

            # Store payment details
            payment_data = {
                'seller_id': current_user.id,
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'amount': 100,
                'status': payment_status
            }
            add_payment_to_db(payment_data)

            # Prepare property data for database
            db_property_data = {
                'seller_id': current_user.id,
                'type': property_data.get('type'),
                'price': property_data.get('price'),
                'rent': property_data.get('rent'),
                'address': property_data.get('address'),
                'city': property_data.get('city'),
                'status': 'not sold',
                'photo': final_path if final_path else None
            }

            # Add property to database
            add_property_to_db(db_property_data)

            # Clear session data
            session.pop('property_form_data', None)

            return jsonify({'success': True, 'message': 'Property listed successfully'})

    except Exception as e:
        app.logger.error(f"Error processing payment verification: {str(e)}")
        # Clean up any temporary files if they exist
        try:
            temp_path = session.get('property_form_data', {}).get('temp_file_path')
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500

# Cleanup function to remove old temporary files
def cleanup_temp_files():
    """Remove temporary files older than 1 hour"""
    temp_dir = os.path.join('static', 'temp')
    if not os.path.exists(temp_dir):
        return
        
    current_time = datetime.now()
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        if (current_time - file_modified_time).seconds > 3600:  # 1 hour
            try:
                os.remove(filepath)
            except Exception as e:
                app.logger.error(f"Error cleaning up temp file {filepath}: {str(e)}")

# Add this to your app initialization
@app.before_request
def before_request():
    cleanup_temp_files()



@app.route('/submit_property', methods=['GET', 'POST'])
@login_required
def submit_property():
    # Check if the user is logged in
    if not current_user.is_authenticated:
        flash('You need to log in to list a property.', 'error')
        return redirect(url_for('login'))

    # Check if property submission data exists in the session
    if 'property_submission_data' not in session:
        flash('Complete the payment first before listing the property.', 'error')
        return redirect(url_for('sell_property'))

    # Retrieve property submission data from session
    data = session['property_submission_data']
    temp_file_path = data.get('file_path')  # Get the temporary file path

    # Ensure the temporary file exists before proceeding
    if not temp_file_path or not os.path.exists(temp_file_path):
        flash('The uploaded file is missing or invalid. Please try again.', 'error')
        return redirect(url_for('sell_property'))

    # Move the file from temp to final storage
    final_file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(temp_file_path))
    try:
        os.rename(temp_file_path, final_file_path)
    except Exception as e:
        flash(f'Error processing the uploaded file: {e}', 'error')
        return redirect(url_for('sell_property'))

    # Save the property details to the database
    try:
        property_data = {
            'seller_id': current_user.id,
            'type': data['type'],
            'price': data['price'],
            'rent': data['rent'],
            'address': data['address'],
            'city': data['city'],
            'status': 'not sold',
            'photo': final_file_path
        }
        add_property_to_db(property_data)

        # Clear the session data after successful submission
        session.pop('property_submission_data', None)

        flash('Property listed successfully!', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        flash(f'Error saving property details: {e}', 'error')
        return redirect(url_for('sell_property'))



#Json:
@app.route('/api/users')
def list_buyers():
    buyers = load_buyers_from_db()
    return jsonify(buyers)


# @app.route('/admin_login')
# def admin_login():
#     return render_template('admin_login.html')



#---------------------------------------------------WORKING ON---------------------------------------------------------# 

# All work is done. (12/10/2024 - 10:00 PM) Jainil J Shah  DreamEstate ......

#----------------------------------------------------------------------------------------------------------------------# 




