from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

username = 'root'
password = ''
host = 'localhost'
dbname = 'cp3'

# Connection string
connect_db = f'mysql+mysqldb://{username}:{password}@{host}/{dbname}'


# Set the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = connect_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking modifications for performance

# Initialize the database
db = SQLAlchemy(app)

class Property(db.Model):
    __tablename__ = 'property'  # Name of your table in the database
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    rent = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    photo = db.Column(db.String(255), nullable=False)

