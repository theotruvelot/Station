from flask import Flask
from flask_restx import Resource, Api
import logging
from datetime import date
import pymysql
import string
import random
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
    db = pymysql.connect(host='192.168.8.192',
                             port=3306,
                             user='root',
                             password='root',
                             database='weatherstation')
    logging.info("Database connection successful")
    db.close()
except pymysql.Error as err:
    logging.error(err)
    print(err)
    exit()

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

@api.route("/post/sonde/<string:idsonde>/<string:key>/<string:temp>")
class Temp(Resource):
    def post(self, idsonde, key, temp):
        sql_sondekey = "SELECT SON_KEY, SON_STATUS FROM SONDES WHERE SON_ID=%s"
        sql = "INSERT INTO MESURES (MES_TEMP, SON_ID) VALUES (%s, %s)"
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
                            cursor.execute(sql, (temp, idsonde))
                            db.commit()
                            last_id = cursor.lastrowid
                            logging.info('Temp injected with probe ID : ' + idsonde + ', temp : ' + temp )
                            db.close()
                            return {'Temp injected with ID':str(last_id)}, 200
                        except pymysql.Error as err:
                            db.close()
                            logging.error(err)
                            return {'Error in temp injection'}, 500
                    else:
                        db.close()
                        logging.warning("Sonde ID : " + idsonde + " want to inject with the wrong key or the status of probe = 0")
                        return{'Error': 'Check your API key or the status of the probe is down'}, 403
            except (pymysql.Error):
                db.close()
                logging.error("Error for ckecking probe ID")
                return{'Error': 'for checking probe ID'}, 500

# mise a jour du status d'une sonde
@api.route("/admin/set/<string:idsonde>/<string:status>", methods=["PUT"])
class admin(Resource):
    def put(self, idsonde, status):
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
                    return{'Probe updated with ID':str(idsonde), 'and status':str(status)}               
            except pymysql.Error as err:
                db.close()
                logging.error(err)
                return {'Error in update probe status'}, 500
@api.route("/sonde/create/<string:useid>/<string:location>", methods=["POST"])
class sonde(Resource):
    def post(self, location, useid):
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
                                "releve_sonde":releve['SON_ID']  
                        })
                        logging.info("recuperation des temps de la sondes %s", idsonde)
                    return releve_list, 200
            except pymysql.Error as err:
                db.close()
                logging.error(err)
                return{'Error db'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5010', debug=True)