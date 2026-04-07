import yaml
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db_config = config['database']
app_config = config['app']

DATABASE_URI = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"

engine = create_engine(DATABASE_URI, echo=app_config['debug'])
Session = sessionmaker(bind=engine)
session = Session()

db = SQLAlchemy()