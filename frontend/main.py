from importlib.metadata import requires
from flask import Flask, render_template, request, session, flash
from flask_bootstrap import Bootstrap
import pymysql
import logging
from datetime import date
import json, requests
today = date.today()
d1 = today.strftime("%d%m%Y")
logging.basicConfig(filename='logs_'+d1+'.log', level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s : %(message)s')
useid = []
try:
    db = pymysql.connect(host='localhost',
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

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        prenom = request.form['prenom']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        r = requests.post('http://localhost:5010/register', json={
            "email":str(email),
            "name":str(name),
            "prenom":str(prenom),
            "password":str(password)
        })
        if r.status_code == 201:
            datas = json.loads(r.content)
            print(datas)
            admin = []
            name = [row['name'] for row in datas]
            prenom = [row['prenom'] for row in datas]
            email = [row['email'] for row in datas]
            session['name'] = name[0]
            session['prenom'] = prenom[0]
            session['email'] = email[0]
            session['admin'] = admin
            return render_template("home.html")
        else: 
            return {"Déjà cette email"}, 401


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        r = requests.post('http://localhost:5010/login', json={
            "email": str(email),
            "password":str(password)
        })
        print(password)
        print(r.status_code)
        if r.status_code == 201:
            datas = json.loads(r.content)
            print(datas)
            useid = [row['useid'] for row in datas]
            name = [row['name'] for row in datas]
            prenom = [row['prenom'] for row in datas]
            email = [row['email'] for row in datas]
            admin = [row['admin'] for row in datas]
            session['useid'] = useid[0]
            session['name'] = name[0]
            session['prenom'] = prenom[0]
            session['email'] = email[0]
            session['admin'] = admin[0]
            return render_template("home.html")
        else:
            flash('Identifiants Incorrects')
            return {"erreur dans le login"}
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
@app.route('/sonde/create', methods=['POST'])
def post():
        location = request.form["location"]
        r = requests.post("http://localhost:5010/sonde/create", json={
            "useid":useid[0],
            "location":location
        })
        if r.status_code == 201: 
            return{"Création OK"}
        else: 
            return {"Création Error"}
@app.route("/sonde/data/<string:id>")
def data(id):
    data = requests.get("http://localhost:5010/sonde/data/" + id)
    datas = json.loads(data.content)
    date = [row['releve_date'] for row in datas]
    temp = [row['releve_temp'] for row in datas]
    humi = [row['releve_humi'] for row in datas]
    return render_template("data.html",  datas = datas, temp = temp, date = date, humi = humi)
@app.route("/admin/sonde/set")
def put(): 
    r = request.put("http://localhost:5010/admin/sonde/set", json={
        "idsonde":request.form['idsonde'],
        "status":request.form['status']
    })
    if r.status_code == 201:
        return{"OK"}
    else:
        return{"NOK"}

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404
            
if __name__ == "__main__":
    app.secret_key = "123456789"
    app.run(debug=True, threaded=True, host='0.0.0.0', port="5011")
