from flask import Flask , request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

#Para usar fronted
from flask_cors import CORS
#------------------------------

#Para autentificar
from flask_bcrypt import check_password_hash, generate_password_hash
import jwt
import datetime
#------------------------------

app = Flask(__name__)

#Para usar fronted
CORS(app)
#---------

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mypassword@localhost:3306/flaskmysql'
#app.config['SQLALCHEMY_DATABASE_URI'] =  'postgresql://postgres:mypassword@localhost:5432/flaskpostgresql'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db=SQLAlchemy(app)


ma= Marshmallow(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    user= db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))

    def __init__(self, email, user, password):
        self.email = email
        self.user = user
        self.password = password
        
#Task
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user= db.Column(db.String(200))
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))

    def __init__(self, user,title, description):
        self.user = user
        self.title = title
        self.description = description


with app.app_context():
    db.create_all()


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'email', 'user', 'password')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

#Task
class TaskSchema(ma.Schema):
    class Meta:
        fields = ('id','user', 'title', 'description')


task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)



@app.route('/loginup', methods=['POST'])
def create_user():
    email=request.json['email']
    user=request.json['user']
    password = generate_password_hash(request.json['password'])
    existing_user = User.query.filter_by(user=user).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 409
    new_user = User(email, user, password)
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user)

@app.route('/loginup', methods=['GET'])
def get_users():
    all_users=User.query.all()
    result=users_schema.dump(all_users)
    return jsonify(result)                    

@app.route('/loginup/<id>', methods=['GET'])
def get_user(id):
    user=User.query.get(id)
    return user_schema.jsonify(user) 

@app.route('/loginup/<id>', methods=['PUT'])
def update_user(id):
    user_to_update = User.query.get(id)  # Renombrar la variable aquí
    
    email = request.json['email']
    new_user = request.json['user']
    password = generate_password_hash(request.json['password'])

    user_to_update.email = email
    user_to_update.user = new_user  # Renombrar la variable aquí
    user_to_update.password = password
    
    db.session.commit()
    return user_schema.jsonify(user_to_update)



@app.route('/loginup/<id>', methods=['DELETE'])
def delete_user(id):
    user=User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return user_schema.jsonify(user)


#Login IN (Iniciar sesion)
@app.route('/', methods=['POST'])
def login():
    data = request.get_json()
    username = data['user']
    password = data['password']

    user = User.query.filter_by(user=username).first()
    if user and check_password_hash(user.password, password):
        # Las credenciales son válidas, puedes generar un token de autenticación aquí
        token = generate_token(user)  # Ejemplo: función para generar el token

        return jsonify({'token': token ,"user_id": user.id}), 200

    # Las credenciales son incorrectas
    return jsonify({'error': 'Credenciales inválidas'}), 401


def generate_token(user):
    # Definir las opciones y configuraciones del token
    token_payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expira en 1 hora
    }
    secret_key = 'tuclavesecretadeltoken'  # Cambia esto a tu clave secreta real

    # Generar el token JWT utilizando PyJWT
    token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    return token


#------------------------------
#Tasks

@app.route('/tasks', methods=['POST'])
def create_task():
    user=request.json['user']
    title=request.json['title']
    description=request.json['description']

    new_task=Task(user,title, description)
    db.session.add(new_task)
    db.session.commit()
    return task_schema.jsonify(new_task)

@app.route('/tasks', methods=['GET'])
def get_tasks():
    all_tasks = Task.query.all()
    result = tasks_schema.dump(all_tasks)
    return jsonify(result)
                 
"""  --get 
---select title , description
--from Task 
---where user = "haweon";
"""
@app.route('/tasks/<user>', methods=['GET'])
def get_task(user):
    task=Task.query.filter_by(user=user).all()
    return tasks_schema.jsonify(task) 

@app.route('/tasks/<id>', methods=['PUT'])
def update_task(id):
    task=Task.query.get(id)
    user=request.json['user']
    title=request.json['title']
    description=request.json['description']

    task.user=user
    task.title=title
    task.description=description
    db.session.commit()
    return task_schema.jsonify(task)


@app.route('/tasks/<id>', methods=['DELETE'])
def delete_task(id):
    task=Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return task_schema.jsonify(task)

@app.route('/tasks/deleteall/<user>', methods=['DELETE'])
def delete_tasks_all(user):
    tasks = Task.query.filter_by(user=user).all()
    
    for task in tasks:
        db.session.delete(task)
    
    db.session.commit()
    
    return tasks_schema.jsonify(tasks)





@app.route('/tasks/<id>/<user>', methods=['GET'])
def get_task_with_id(id,user):
    task=Task.query.filter_by(id=id ,user=user).all()
    return tasks_schema.jsonify(task) 


#------------------------------
#filters

#------------------------------
""" --get contar 
---SELECT COUNT(title) AS numero, title
--FROM Task
--GROUP BY title
--HAVING user = 'haweon'; """
from sqlalchemy import func

@app.route('/tasks/countsames/<user>')
def get_same_count(user):
    subquery = db.session.query(func.count(Task.title).label('Number of titles'), Task.title)\
        .group_by(Task.title)\
        .having(func.count(Task.title) > 1)\
        .subquery()

    query = db.session.query(func.max(subquery.c['Number of titles']).label('Number of titles'), subquery.c.title)\
        .filter(subquery.c.title.in_(db.session.query(Task.title).filter(Task.user == user)))\
        .group_by(subquery.c.title)\
        .all()

    if not query:
        return jsonify(message="Ningún título coincide con otros usuarios.")

    result = [{'Number of titles': count, 'title': title} for count, title in query]

    return jsonify(result)




#------------------------------

#email igual al titulo
""" SELECT t.title, c.email
FROM Task t
JOIN Cosa c ON t.user = c.user
WHERE t.user = 'haweon'
AND t.title IN (
    SELECT title
    FROM Task
    WHERE user <> 'haweon'
)
GROUP BY t.title, c.email;"""

@app.route('/tasks/countsame/<user>')
def get_same_title_email(user):
    subquery = db.session.query(Task.title)\
        .filter(Task.user == user)\
        .subquery()

    query = db.session.query(Task.title, func.group_concat(User.email).label('emails'))\
        .join(User, Task.user == User.user)\
        .filter(Task.user != user).filter(Task.title.in_(subquery))\
        .group_by(Task.title)\
        .all()

    if not query:
         return jsonify(message="Ningún título coincide con otros usuarios.")

    results = [{'title': row.title, 'emails': row.emails.split(',')} for row in query]

    return jsonify(results)




if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')

#Comands for use docker container mysql
#docker run --name mymysql -e MYSQL_ROOT_PASSWORD=mypassword -p 3306:3306 -d mysql:latest
#docker exec -it mymysql bash
#mysql -u root -p
#create database flaskmysql;

