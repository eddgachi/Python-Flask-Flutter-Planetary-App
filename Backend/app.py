from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'planets.db')

app.config['JWT_SECRET_KEY'] = 'supersecret'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Datbase Created!!!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Datbase Dropped!!!')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(
        planet_name='Mercury',
        planet_type='Class D',
        home_star='Sol',
        mass=3.258e23,
        radius=1516,
        distance=35.98e6
    )

    venus = Planet(
        planet_name='Venus',
        planet_type='Class K',
        home_star='Sol',
        mass=4.867e24,
        radius=3760,
        distance=67.24e6
    )

    db.session.add(mercury)
    db.session.add(venus)

    test_user = User(
        f_name='William',
        l_name='Herschel',
        email='test@gmail.com',
        password='tester123'
    )

    db.session.add(test_user)
    db.session.commit()
    print('Database Seeded!!')


@app.route('/')
def hello_world():
    return 'Hello World'


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)

# @app.route('/planet_details/<int:planet_id>', methods=['GET'])
# def planet_details(planet_id, int):


@app.route('/register', methods=['POST'])
def register():
    email = request.json['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='The email already exists'), 409
    else:
        f_name = request.json['f_name']
        l_name = request.json['l_name']
        password = request.json['password']
        new_user = User(f_name=f_name, l_name=l_name,
                        email=email, password=password
                        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message='User created successfully'), 201


@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded', access_token=access_token)
    else:
        return jsonify(message='You entered a bad email or password'), 401


@app.route('/retrieve_password', methods=['GET'])
def retrieve_password():
    email = request.json['email']
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('Your planetary app password is ' +
                      user.password, sender='admin@planetaryapp.com',
                      recipients=[email]
                      )
        mail.send(msg)
        return jsonify(message='Password sent to ' + email)
    else:
        return jsonify(message='That email doesn\'t exist')


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    f_name = Column(String)
    l_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'

    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'f_name', 'l_name', 'email', 'password')


class PlanetsSchema(ma.Schema):
    class Meta:
        fields = (
            'planet_id',
            'planet_name',
            'planet_type',
            'home_star',
            'mass',
            'radius',
            'distance',
        )


user_schema = UserSchema()
user_schema = UserSchema(many=True)

planets_schema = PlanetsSchema()
planets_schema = PlanetsSchema(many=True)

if __name__ == '__main__':
    app.run(debug=True)
