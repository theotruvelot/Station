from importlib.metadata import requires
from flask import Flask, render_template, request, session
from flask_bootstrap import Bootstrap
import bcrypt
import pymysql
import logging
from datetime import date
import json, requests
today = date.today()
d1 = today.strftime("%d%m%Y")
logging.basicConfig(filename='logs_'+d1+'.log', level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s : %(message)s')

try:
    db = pymysql.connect(host='192.168.8.192',
                         port=3306,
                         user='root',
                         password='root',
                         database='weatherstation')
    logging.info("Database connection successful")
except pymysql.Error as err:
    logging.error(err)
    print(err)
    exit()

app = Flask(__name__)
Bootstrap(app)


@app.route("/")
def home():
    return render_template("home.html")
    
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/register",  methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        prenom = request.form['prenom']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
        sql = "INSERT INTO USERS (USE_NOM, USE_PRENOM, USE_EMAIL, USE_PASS) VALUES (%s, %s, %s, %s);"
        sql1 = "SELECT USE_ID FROM USERS WHERE USE_EMAIL = %s"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                cursor.execute(sql1, email)
                emails = cursor.fetchall()
                if len(emails) >= 1:
                    return "Y'a déjà cet email bg go te login"
                else:
                    cursor.execute(sql, (name, prenom, email, hash_password))
                    db.commit()
                    session['name'] = name
                    session['prenom'] = prenom
                    session['email'] = email
                    return render_template("home.html")

            except db.Error as err:
                print(err)
                return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        sql = "SELECT * FROM USERS WHERE USE_EMAIL = %s"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                cursor.execute(sql, email)
                user = cursor.fetchone()
                if len(user) > 1:
                    if bcrypt.hashpw(password, user['USE_PASS'].encode('utf-8')) == user['USE_PASS'].encode('utf-8'):
                        session['name'] = user['USE_NOM']
                        session['prenom'] = user['USE_PRENOM']
                        session['email'] = user['USE_EMAIL']
                        session['admin'] = user['USE_ADMIN']
                        return render_template("home.html")
                    else:
                        return "Error password and email doesnt match"
                else:
                    return "Error password and email doesnt match"
            except db.Error as err:
                print(err)
        return render_template("home.html")
    else:
        return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return render_template("home.html")

@app.route("/sondes")
def sondes():
    sonde = requests.get('http://localhost:5010/sondes')
    sondes = json.loads(sonde.content)
    
    return render_template("sondes.html", sondes=sondes)

@app.route("/sonde/data/<string:id>")
def data(id):
    data = requests.get("http://localhost:5010/sonde/data/" + id)
    datas = json.loads(data.content)
    return render_template("data.html",  datas = datas)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404
            
if __name__ == "__main__":
    app.secret_key = "123456789"
    app.run(debug=True, threaded=True, host='0.0.0.0', port="5011")
