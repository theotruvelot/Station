#!/bin/sh
from http import server


apt-get install python
apt-get install mysql-server
mysql -h localhost -u root -p root wheatherstation > sql.sql
python ../frontend/main.py
python ../backend/main.py