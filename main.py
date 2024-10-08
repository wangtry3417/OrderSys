from flask import Flask,render_template,request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO,emit,join_room,leave_room

app = Flask(__name__,template_folder="template")
socketio = SocketIO(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://default:Gd2MsST3QYWF@ep-hidden-salad-a1a7pob9-pooler.ap-southeast-1.aws.neon.tech:5432/verceldb?sslmode=require"
#DataBase setup
db = SQLAlchemy(app)

class Foods(db.Model):
    __tablename__ = 'foods'
    name = db.Column(
        db.String(30), unique=True, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    img = db.Column(
        db.String(100), unique=True, nullable=False)
    description = db.Column(
        db.String(255), nullable=False)
    state = db.Column(
        db.String(10), nullable=False)
 
 
    def __init__(self, name, price, img, description, state):
        self.name = name
        self.price = price
        self.img = img
        self.description = description
        self.state = state

class Orders(db.Model):
    __tablename__ = 'orders'
    name = db.Column(
        db.String(30), unique=True, primary_key=True)
    status = db.Column(
        db.String(10), nullable=False)
 
 
    def __init__(self, name):
        self.name = name
        self.status = "未完成"

#HTTPS
@app.route("/")
def index():
  return render_template("index.html")

@app.route("/order")
def order_page():
  return render_template("order.html")

@app.route("/admin")
def staff_page():
  return render_template("admin.html")

@app.route("/chef")
def chef_page():
  return render_template("cook.html")

#SocketIO
@socketio.on("connect")
def on_connect():
  print("ok")

@socketio.on("get_food")
def get_food():
  foods = Foods.query.all()
  fl = []
  for food in foods:
    fl.append({
        'name': food.name,
        'price': food.price,
        'img': food.img,
        'description': food.description,
        'state': food.state
    })
    emit("food_updated",fl, broadcast=True)

@socketio.on("update_food")
def handle_update_food(data):
    # 假設data是新菜品的字典
    food = Foods(
        name=data['name'],
        price=data['price'],
        img=data['img'],
        description=data['description'],
        state=data['state']
    )
    db.session.add(food)
    db.session.commit()
    
    # 通知所有客戶端更新
    emit("food_updated", {
        'name': food.name,
        'price': food.price,
        'img': food.img,
        'description': Foods.description,
        'state': food.state
    }, broadcast=True)

@socketio.on("update_food_state")
def handle_update_food_state(data):
    # 根據菜品名更新狀態
    food = Foods.query.filter_by(name=data['name']).first()
    if food:
        food.state = data['state']
        db.session.commit()
        
        # 通知所有客戶端更新
        emit("food_state_updated", {
            'name': food.name,
            'state': food.state
        }, broadcast=True)

@socketio.on("join")
def on_join_team(team):
  return join_room(team)

@socketio.on("leave")
def on_leave_team(team):
  return leave_room(team)

@socketio.on("send_food")
def recv_food_name(foodName):
  food_obj = Orders(foodName,"未完成")
  db.session.add(food_obj)
  db.session.commit()

@socketio.on("get_orders")
def get_orders():
  orders = Orders.query.all()
  ol = []
  for o in orders:
    ol.append({
      "name":o.name,
      "status":o.status
    })
    emit("updated_order",ol,room="cook")

@socketio.on("delete_dang")
def de_dang(foodName):
  order = Orders.query.filter_by(name=foodName).first()
  db.session.delete(Orders(foodName,order.status))
  db.session.commit()

socketio.run(app,host="0.0.0.0",port=5000,allow_unsafe_werkzeug=True)
