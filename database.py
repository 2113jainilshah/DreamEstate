from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import json

username = 'root'
password = ''
host = 'localhost'
dbname = 'cp3'

# Connection string
connect_db = f'mysql+mysqldb://{username}:{password}@{host}/{dbname}'

# Connecting
engine = create_engine(connect_db)

def load_buyers_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM buyer"))
        buyers = []
        rows = result.fetchall()
        columns = result.keys()
        # Convert rows to a list of dictionaries
        buyers = [dict(zip(columns, row)) for row in rows]
        return buyers
    
def load_sellers_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM seller"))
        sellers = []
        rows = result.fetchall()
        columns = result.keys()
        # Convert rows to a list of dictionaries
        sellers = [dict(zip(columns, row)) for row in rows]
        return sellers


def check_email_or_phone_exists(email, phone, role):
    """
    Check if an email or phone number already exists in the specified role's table.
    
    Args:
        email (str): Email address to check.
        phone (str): Phone number to check.
        role (str): 'buyer' or 'seller'.
    
    Returns:
        bool: True if email or phone exists, False otherwise.
    """
    try:
        with engine.connect() as conn:
            query = text(f"""
                SELECT COUNT(*) 
                FROM {role} 
                WHERE email = :email OR phone = :phone
            """)
            result = conn.execute(query, {'email': email.lower(), 'phone': phone})
            count = result.scalar()
            return count > 0
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return False

    
      
def add_user_to_db(data):
    try:
        # Convert the email to lowercase
        data['email'] = data['email'].lower()

        # Determine the table based on the role
        table_name = data['role']  # Expecting 'buyer' or 'seller'
        
        with engine.connect() as conn:
            query = text(f"""
                INSERT INTO {table_name} 
                (name, email, password, phone) 
                VALUES (:name, :email, :password, :phone)
            """)
            conn.execute(query, {
                'name': data['name'],
                'email': data['email'],
                'password': data['password'],
                'phone': data['phone']
            })
            conn.commit()  # Explicitly commit the transaction

    except Exception as e:
        print(f"Error: {e}")



def delete_user_from_db(role, user_id):
    try:
        table_name = role  # Use role to select the appropriate table
        with engine.connect() as conn:
            # Delete the user based on the role and id
            query = text(f"DELETE FROM {table_name} WHERE id = :id")
            result = conn.execute(query, {'id': user_id})
            
            # Commit the transaction
            conn.commit()  # Use conn.commit() only if using a transactional connection

            # Check if the deletion was successful
            if result.rowcount > 0:
                print(f"User with id {user_id} deleted successfully from {table_name}.")
                return True
            else:
                print(f"User with id {user_id} not found in {table_name}.")
                return False

    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return False



def update_user_in_db(id, data, role):
    table_name = role
    try:
        with engine.connect() as conn:
            query = text(f"""
                UPDATE {table_name} 
                SET name = :name, email = :email, phone = :phone
                WHERE id = :id
                """)
            conn.execute(query, {
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone'],
                'id': id
            })
            conn.commit()  # Explicitly commit the transaction
        print('User information updated successfully.')
        print("Test 2 passed....")
    except Exception as e:
        print(f"Error updating user: {e}")
        print('Error updating user information.')


def get_user_by_email(email, role):
    try:
        table_name = role  # Use role to select the appropriate table
        with engine.connect() as conn:
            query = text(f"SELECT * FROM {table_name} WHERE email = :email")
            result = conn.execute(query, {'email': email})
            user = result.fetchone()
            if user:
                # Convert the row to a dictionary
                columns = result.keys()
                user_dict = dict(zip(columns, user))
                return user_dict
            return None
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return None

def get_user_by_id(user_id, role):
    try:
        table_name = role  # Use role to select the appropriate table
        with engine.connect() as conn:
            query = text(f"SELECT * FROM {table_name} WHERE id = :id")
            result = conn.execute(query, {'id': user_id})
            user = result.fetchone()
            if user:
                # Convert the row to a dictionary
                columns = result.keys()
                user_dict = dict(zip(columns, user))
                return user_dict
            return None
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return None


def add_property_to_db(data):
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO property (seller_id, type, price, rent, address, city, status, photo)
                VALUES (:seller_id, :type, :price, :rent, :address, :city, :status, :photo)
            """)
            conn.execute(query, {
                'seller_id': data['seller_id'],
                'type': data['type'],
                'price': data['price'],
                'rent': data['rent'],
                'address': data['address'],
                'city': data['city'],
                'status': data['status'],
                'photo': data['photo']  # Save the file path
            })
            conn.commit()  # Explicitly commit the transaction
    except SQLAlchemyError as e:
        print(f"Database error: {e}")

def load_properties_from_db(page_number, items_per_page, filters):
    with engine.connect() as conn:
        offset = (page_number - 1) * items_per_page

        # Build the query with optional filters
        query = text("""
            SELECT property.*, seller.name AS seller_name, seller.email AS seller_email
            FROM property
            JOIN seller ON property.seller_id = seller.id
            WHERE (:type = '' OR property.type = :type)
            AND (:price_min IS NULL OR property.price >= :price_min)
            AND (:price_max IS NULL OR property.price <= :price_max)
            AND (:rent_min IS NULL OR property.rent >= :rent_min)
            AND (:rent_max IS NULL OR property.rent <= :rent_max)
            AND (:city = '' OR property.city LIKE :city)
            AND (:sold_status = '' OR property.status = :sold_status)
            LIMIT :items_per_page OFFSET :offset
        """)

        result = conn.execute(query, {
            'items_per_page': items_per_page, 'offset': offset,
            'type': filters.get('type', ''),
            'price_min': filters.get('price_min'),
            'price_max': filters.get('price_max'),
            'rent_min': filters.get('rent_min'),
            'rent_max': filters.get('rent_max'),
            'city': f"%{filters.get('city', '')}%",
            'sold_status': filters.get('sold_status', '')
        })

        rows = result.all()
        column_names = result.keys()
        properties = [dict(zip(column_names, row)) for row in rows]
        return properties


def get_properties_count_from_db(filters):
    with engine.connect() as conn:
        query = text("""
            SELECT COUNT(*) FROM property
            WHERE (:type = '' OR property.type = :type)
            AND (:price_min IS NULL OR property.price >= :price_min)
            AND (:price_max IS NULL OR property.price <= :price_max)
            AND (:rent_min IS NULL OR property.rent >= :rent_min)
            AND (:rent_max IS NULL OR property.rent <= :rent_max)
            AND (:city = '' OR property.city LIKE :city)
            AND (:sold_status = '' OR property.status = :sold_status)
        """)

        result = conn.execute(query, {
            'type': filters.get('type', ''),
            'price_min': filters.get('price_min'),
            'price_max': filters.get('price_max'),
            'rent_min': filters.get('rent_min'),
            'rent_max': filters.get('rent_max'),
            'city': f"%{filters.get('city', '')}%",
            'sold_status': filters.get('sold_status', '')
        })
        
        count = result.scalar()
        return count


def load_seller_properties_from_db(seller_id):
    with engine.connect() as conn:
        # Join the property table with the seller table to get the seller's name and email
        query = text("""
            SELECT 
                property.*, 
                seller.name AS seller_name, 
                seller.email AS seller_email 
            FROM 
                property 
            JOIN 
                seller 
            ON 
                property.seller_id = seller.id
            WHERE 
                seller.id = :seller_id
        """)
        # Execute the query with the seller_id parameter
        result = conn.execute(query, {'seller_id': seller_id})
        rows = result.all()
        column_names = result.keys()
        properties = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            properties.append(row_dict)
        return properties



def soldout_property(id):
    try:
        with engine.connect() as conn:
            # Update the status of the property to "Sold Out" where the id matches
            query = text("""
                UPDATE property
                SET status = 'Sold Out'
                WHERE id = :id
            """)
            conn.execute(query, {'id': id})
            conn.commit()
        print(f"Property with ID {id} marked as 'Sold Out'.")
    except Exception as e:
        print(f"An error occurred while updating the property: {e}")

    
def add_blog_to_db(data):
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO blogs (user_id, heading, content, likes, photo)
                VALUES (:user_id, :heading, :content, :likes, :photo)
            """)
            conn.execute(query, {
                'user_id': data['user_id'],
                'heading': data['heading'],
                'content': data['content'],
                'likes': data['like'],
                'photo': data['photo']
            })
            conn.commit()  # Explicitly commit the transaction
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        raise  # Re-raise the exception for handling in the calling function


def load_blogs_from_db():
    with engine.connect() as conn:
        # Query to select all data from the blogs table
        query = text("""
            SELECT * FROM blogs
        """)
        result = conn.execute(query)
        
        # Fetch all rows and column names
        rows = result.all()
        column_names = result.keys()
        
        # Convert each row into a dictionary using zip
        blogs = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            blogs.append(row_dict)
        
        return blogs




# Function to add a new inquiry to the enquires table
def add_enquiry_to_db(seller_id, buyer_id, property_id, message):
    with engine.connect() as conn:
        query = text("""
            INSERT INTO enquires (seller_id, buyer_id, property_id, date, message)
            VALUES (:seller_id, :buyer_id, :property_id, NOW(), :message)
        """)
        conn.execute(query, {
            'seller_id': seller_id,
            'buyer_id': buyer_id,
            'property_id': property_id,
            'message': message
        })
        conn.commit()


def get_enquiries_for_seller(seller_id):
    with engine.connect() as conn:
        query = text("""
            SELECT e.seller_id, e.buyer_id, e.property_id, e.message, e.date, p.address, b.name AS buyer_name, b.phone AS buyer_phone
            FROM enquires e
            JOIN property p ON e.property_id = p.id
            JOIN buyer b ON e.buyer_id = b.id
            WHERE e.seller_id = :seller_id
        """)
        result = conn.execute(query, {'seller_id': seller_id})
        # Fetch all the rows and return
        return result.fetchall()


def store_verification_code(email, role, code):
    """Store the verification code temporarily in the user_verifications table."""
    with engine.connect() as conn:
        query = text("""
            INSERT INTO user_verifications (email, role, verified, verification_code)
            VALUES (:email, :role, FALSE, :code)
            ON DUPLICATE KEY UPDATE verification_code = :code
        """)
        conn.execute(query, {'email': email, 'role': role, 'code': code})
        conn.commit()

def get_stored_verification_code(email):
    with engine.connect() as conn:
        query = text("SELECT verification_code FROM user_verifications WHERE email = :email")
        result = conn.execute(query, {'email': email}).fetchone()
    
    if result:
        return result[0]
    else:
        return None

def mark_user_as_verified(email):
    """Mark the user as verified in the respective table (buyer or seller)."""
    with engine.connect() as conn:
        # Update the user_verifications table to mark as verified
        query = text("""
            UPDATE user_verifications
            SET verified = TRUE
            WHERE email = :email
        """)
        conn.execute(query, {'email': email})

        # Fetch the role from the user_verifications table
        query = text("SELECT role FROM user_verifications WHERE email = :email")
        result = conn.execute(query, {'email': email}).fetchone()
        if result:
            role = result[0]  # Access the first (and only) element of the tuple
        else:
            role = None

        # Update the buyer or seller table based on role
        if role == 'buyer':
            query = text("UPDATE buyer SET verified = TRUE WHERE email = :email")
        elif role == 'seller':
            query = text("UPDATE seller SET verified = TRUE WHERE email = :email")
        else:
            return "Role not found", 400

        conn.execute(query, {'email': email})
        conn.commit()


def add_payment_to_db(data):
    try:
        print(f"Storing payment data: {data}")  # Debugging
        with engine.connect() as conn:
            query = text("""
                INSERT INTO property_payments 
                (seller_id, razorpay_order_id, razorpay_payment_id, amount, status)
                VALUES (:seller_id, :razorpay_order_id, :razorpay_payment_id, :amount, :status)
            """)
            conn.execute(query, data)
            conn.commit()
            print("Payment data stored successfully")
    except SQLAlchemyError as e:
        print(f"Database error in add_payment_to_db: {e}")
        # Optional: you might want to re-raise the exception
        raise
