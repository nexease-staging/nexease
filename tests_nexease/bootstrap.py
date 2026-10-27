import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.update(DJANGO_SETTINGS_MODULE='config.settings',DJANGO_SECRET_KEY='test-only-nexease-isolated-key-not-for-deployment',MONGODB_URI='mongodb://localhost',MONGODB_DATABASE='nexease_test_isolated',APP_ENV='development',EMAIL_MODE='development')
import mongomock,mongoengine
import config.mongodb
config.mongodb.connect_to_mongodb=lambda: mongoengine.connect('nexease_test_isolated',host='mongodb://localhost',mongo_client_class=mongomock.MongoClient)
os.environ["SAAS_ENFORCEMENT"]="false"
import django
django.setup()
