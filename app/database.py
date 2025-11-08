from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base #this just allows u to write in sql using python instead of typical SQL language making it more redable 
from sqlalchemy.orm import sessionmaker
#what this is doing is just setting up the url to the databse trough sql
SQLALCHEMY_DATABASE_URL  = 'sqllie:///.instragram_tracker.db'
#this connects to the data base
engine = create_engine(SQLALCHEMY_DATABASE_URL)
#session is bascially just how to talk to the databse, wether that's opening or closing a file
#it also makes data base sessions 
SessionLocal = sessionmaker(bind = engine)

Base = declarative_base()
#This what we're going to be calling through out our modles 