# DreamEstate
Real Estate Website

DreamEstate is a web application designed to facilitate property transactions, including buying, selling, and renting. The platform provides a user-friendly interface for buyers, sellers, and administrators to manage real estate listings seamlessly.

## Features
Property Listings: Buyers can view properties listed by sellers.
User Roles: Three distinct user roles - Admin, Buyer, and Seller.
Seller Functionality: Sellers can directly list their properties without admin approval.
Buyer Functionality: Buyers can search properties by type (House, Apartment, Commercial) and inquire about listings.
Dynamic Banner: The homepage features a full-width banner that updates every 30 seconds.
Interactive Maps: Google Maps integration to display property locations.
User Authentication: Login system with role-based redirection.

## Tech Stack
Frontend: HTML, CSS, JavaScript
Backend: Python (Flask)
Database: MySQL
APIs: Google Maps API

### Installation
1. Clone the repository.
git clone https://github.com/yourusername/DreamEstate.git  
cd DreamEstate

2. Set up a Python virtual environment.
python -m venv venv  
source venv/bin/activate  # On Windows, use venv\Scripts\activate

3. Install dependencies.
pip install -r requirements.txt  
Set up the MySQL database and update the configuration in config.py.

4. Run the Flask application.
flask run

## Usage
Access the application at http://localhost:5000.
Navigate through the roles and explore features tailored for buyers, sellers, and admins.

## Contributors
Jainil Shah

## License
This project is licensed under the MIT License.







