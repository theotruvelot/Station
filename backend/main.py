from flask import Flask, request, session
from flask_restx import Resource, Api, fields
import logging
from datetime import date
import pymysql
import string
import random
import bcrypt


# récuperation de la date pour les logs.

today = date.today()
d1 = today.strftime("%d%m%Y")

# ajout des informations sur l'API
app = Flask(__name__)
api = Api(app=app, version="0.1", doc="/api", title="API WeatherApp", description="This is the Weather Station API", default="API WeatherStation", default_label='This is the Weather Station API', validate=True)

# système de logs.
logging.basicConfig(filename='logs_'+d1+'.log', level=logging.INFO, format=f'%(asctime)s %(levelname)s : %(message)s')

# connexion a la base de données
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
    
postsonde = api.model('POST DATA', {
    'id': fields.String(required=True),
    'key': fields.String(required=True),
    'temp': fields.Float(required=True), 
    'humi': fields.Float(required=True),
})
createsond= api.model('POST CREATE SOND', {
    'useid': fields.String(required=True),
    'location': fields.String(required=True)
})
updatesond= api.model('PUT SONDE STATUS', {
    'idsonde': fields.String(required=True),
    'status': fields.String(required=True)
})
login = api.model('LOGIN', {
    'email': fields.String(required=True),
    'password': fields.String(required=True)
})
register = api.model('REGISTER', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
    'name':fields.String(required=True),
    'prenom':fields.String(required=True)
})
createsond = api.model('POST CREATE SOND', {
    'useid': fields.String(required=True),
    'location': fields.String(required=True)
})
# test de l'API avec un ping

@api.route("/ping") 
class Ping(Resource):
    @api.response(200, 'API Ping : Success')
    def get(self):
        return {'response':'pong'}, 200

# test de requêtes SQL avec la récupération de toutes les sondes

@api.route("/sondes")
class Sondes(Resource):
        def get(self):
            sql = "select SON_ID, SON_STATUS  from sondes ;"
            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                try:
                    db.connect()
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    sond_list = []
                    for list in result:
                            print(list)
                            sond_list.append({
                            "sonde_id":list['SON_ID'],
                            "sonde_status":list['SON_STATUS']
                            })
                    db.close()
                    return sond_list, 200
                except db.Error as err:
                    logging.error(err)
                    print(err)

# récuperation des données envoyé par les sondes, vérification de sa clé, envoie dans la db

@api.route("/post/sonde", methods=["POST"]) 
@api.expect(postsonde)
class Temp(Resource):
    def post(self): 
        print (request.is_json)
        content = request.get_json()
        print (content)
        print(content['id'])
        print (content['key'])
        print (content['temp'])
        idsonde = content['id']
        key = content['key']
        temp = content['temp']
        humi = content['humi']
        sql_sondekey = "SELECT SON_KEY, SON_STATUS FROM SONDES WHERE SON_ID=%s"
        sql = "INSERT INTO MESURES (MES_TEMP, MES_HUMI, SON_ID) VALUES (%s, %s, %s)"
        sqllast = "UPDATE SONDES SET SON_LAST_MESURE=now() where SON_ID=%s"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                db.connect
                # récupération de la clé dans la db 
                cursor.execute(sql_sondekey, idsonde)
                sondks = cursor.fetchone()
                # gestion du cas ou l'id de la sonde est inconnue 
                if str(sondks['SON_KEY']) == None:
                    logging.warning("A probe wan't to inject with a wrong ID")
                    db.close()
                    return{'Error': 'Check your probe ID'}, 403
                else: 
                # vérification si la clé reçu correspond bien à la clé de la sonde
                    if str(sondks['SON_KEY']) == str(key) and str(sondks['SON_STATUS']) == "1":
                        try:
                            # envoie de la commande sql pour l'injection
                            cursor.execute(sqllast, idsonde)
                            cursor.execute(sql, (temp, humi, idsonde))
                            db.commit()
                            last_id = cursor.lastrowid
                            logging.info('Temp injected with probe ID : ' + idsonde + ', temp : ' + str(temp) )
                            return {'Temp injected with ID':str(last_id), 'id': idsonde, 'temp': temp, 'humi': humi, 'key': key}, 201 
                        except pymysql.Error as err:
                            logging.error(err)
                            return {'Error in temp injection'}, 500
                    else:
                        logging.warning("Sonde ID : " + idsonde + " want to inject with the wrong key or the status of probe = 0")
                        return{'Error': 'Check your API key or the status of the probe is down'}, 403
            except (pymysql.Error):
                logging.error("Error for ckecking probe ID")
                return{'Error': 'for checking probe ID'}, 500

# mise a jour du status d'une sonde
@api.route("/admin/sonde/set", methods=["PUT"])
@api.expect(updatesond)
class admin(Resource):
    def put():
        content = request.get_json()
        idsonde = content.get['idsonde']
        status = content.get['status']
        #  commande pour la récupération du status / vérification l'existance de l'ID
        sql1 = "SELECT SON_ID, SON_STATUS FROM SONDES WHERE SON_ID=%s"
        # commande pour mettre a jour le status de la sonde
        sql2 = "UPDATE SONDES SET SON_STATUS=%s WHERE SON_ID=%s"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                db.connect()
                cursor.execute(sql1, idsonde)
                sondverif = cursor.fetchone()
                # vérification si la sonde existe / si son status n'est pas = à celui demandé
                if sondverif == None or sondverif['SON_STATUS'] == str(status):
                    logging.warning("Someone want change status of unknow probe")
                    db.close()
                    return{'Error': 'Check your probe ID or the status or the status of the probe is already set'}, 403
                else :
                    # envoie de la commande de mise a jour
                    cursor.execute(sql2, (status, idsonde))
                    db.commit()
                    db.close()
                    logging.info("Probe status with probe ID : " + idsonde + " was updated to : " + status)
                    return{'Probe updated with ID':str(idsonde), 'and status':str(status)} , 201              
            except pymysql.Error as err:
                db.close()
                logging.error(err)
                return {'Error in update probe status'}, 500

@api.route("/sonde/create", methods=["POST"])
@api.expect(createsond)
class sonde(Resource):
    def post(self):
        content = request.get_json()
        useid = content['useid']
        location = content['location']
        length_of_string = 50
        key = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length_of_string))
        print(key)
        sql = "INSERT INTO SONDES (SON_LOCATION, SON_KEY) VALUES (%s, %s)"
        sql1 = "INSERT INTO POSSEDE (SON_ID, USE_ID) VALUES (%s, %s)"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                db.connect()
                cursor.execute(sql, (location, key))
                last_id = cursor.lastrowid
                cursor.execute(sql1, (last_id, useid))
                db.commit()
                return {'Sonde created with id:':str(last_id)}, 200
            except pymysql.Error as err:
                db.close()
                logging.error(err)
                return{'Erreur dans la création de la sonde'}, 500


@api.route("/user/sondes/<string:userid>", methods=["GET"])
class usondes(Resource):
    def get(self, userid):
        sql = "SELECT POSSEDE.SON_ID, SONDES.SON_STATUS, SONDES.SON_LAST_MESURE, SONDES.SON_LOCATION , SONDES.SON_KEY  FROM POSSEDE INNER JOIN SONDES ON POSSEDE.SON_ID = SONDES.SON_ID  WHERE USE_ID = %s"
        sondes_list = []
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
                try:
                    db.connect()
                    cursor.execute(sql, userid)
                    sondes = cursor.fetchall()
                    if sondes == None:
                        db.close()
                        logging.warning("Connais pas")
                    else:
                        db.connect()
                    for releve in sondes:
                        print(releve)
                        sondes_list.append({
                                "sonde_id":releve['SON_ID'],
                                "sonde_status":str(releve['SON_STATUS']),
                                "sonde_lastmes":str(releve['SON_LAST_MESURE']),
                                "sonde_loca":releve['SON_LOCATION'],
                                "sonde_key":releve['SON_KEY']
                        })
                        logging.info("recuperation des temps de la sondes %s", sondes_list)
                    return sondes_list, 200
                except pymysql.Error as err:
                    db.close()
                    logging.error(err)
                    return{'Erreur dans la récupération des sondes'}, 500
@api.route("/login", methods=["POST"])
@api.expect(login)

class login(Resource):
    def post(self):
        content = request.get_json()
        email = content['email']
        password = content['password']
        print(email, password)
        sql = "SELECT * FROM USERS WHERE USE_EMAIL = %s"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                cursor.execute(sql, email)
                user = cursor.fetchone()
                if len(user) >= 1:
                    passd = password.encode('utf-8')
                    print(bcrypt.hashpw(passd, user['USE_PASS'].encode('utf-8')))
                    print(user['USE_PASS'].encode('utf-8'))
                    if bcrypt.hashpw(passd, user['USE_PASS'].encode('utf-8')) == user['USE_PASS'].encode('utf-8'):
                        idenfiants = []
                        idenfiants.append({
                                "useid":user['USE_ID'],
                                "name":user['USE_NOM'],
                                "prenom":user['USE_PRENOM'],
                                "email":user['USE_EMAIL'],
                                "admin":user['USE_ADMIN'],
                        })
                        logging.info('IDENTIFICATION USER : ' + str(user['USE_ID']) )
                        return idenfiants, 201
                    else:
                        return "Error password and email doesnt match", 401
                else:
                    return "Error password and email doesnt match", 401
            except db.Error as err:
                print(err)

@api.route("/register", methods=["POST"])
@api.expect(register)

class register(Resource):
    def post(self):
        content = request.get_json()
        print(content)
        prenom = content['prenom']
        name = content['name']
        email = content['email']
        password = content['password'].encode('utf8')
        print(prenom)
        print(name, email, password)
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
        sql = "INSERT INTO USERS (USE_NOM, USE_PRENOM, USE_EMAIL, USE_PASS) VALUES (%s, %s, %s, %s);"
        sql1 = "SELECT USE_ID FROM USERS WHERE USE_EMAIL = %s"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                cursor.execute(sql1, email)
                emails = cursor.fetchall()
                last_id = cursor.lastrowid()
                print(emails)
                if emails == None:
                    return{"Y'a déjà cet email bg go te login"}
                else:
                    try:
                        idenfiants = [{
                                    "useid":last_id,
                                    "name": name,
                                    "prenom":prenom,
                                    "email":email
                            }]
                        cursor.execute(sql, (name, prenom, email, hash_password))
                        db.commit()
                        print(idenfiants)
                        return idenfiants, 201
                    except db.Error as err:
                        print(err)
            except db.Error as err:
                print(err)
                return{"error":err.message}
# récupere tout les temp prisent par une sonde 
@api.route("/sonde/data/<string:idsonde>", methods=["GET"])
class temp(Resource):
    def get(self, idsonde):
        releve_list = []
        sql = 'SELECT * FROM MESURES WHERE SON_ID = %s'
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                db.connect()
                cursor.execute(sql, idsonde)
                sondtemp = cursor.fetchall()
                if sondtemp == None:
                    db.close()
                    logging.warning("Connais pas")
                else:
                    db.connect()
                    for releve in sondtemp:
                        print(releve)
                        releve_list.append({
                                "releve_id":releve['MES_ID'],
                                "releve_date":str(releve['MES_DATE']),
                                "releve_temp":str(releve['MES_TEMP']),
                                "releve_sonde":releve['SON_ID'],
                                "releve_humi":releve['MES_HUMI']
                        })
                        logging.info("recuperation des temps de la sondes %s", idsonde)
                    return releve_list, 200
            except pymysql.Error as err:
                db.close()
                logging.error(err)
                return{'Error db'}, 500

if __name__ == '__main__':
    app.secret_key = "123456789"
    app.run(host='0.0.0.0', port='5010', debug=True)