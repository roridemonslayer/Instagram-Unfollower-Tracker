from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#all this is just doing is connection all of the stuff from our databse 
Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True)
    email = Column(String(100), unique = True, nullable = False)
    insta_user = Column(String(100), unique = True, nullable = False)
    insta_password = Column(String(100), nullable = False)
    is_active = Column(Boolean, default = True, nullable = False)
    created_at = Column(DateTime, default=func.now())

    __tablename__ ="followerelationships"
    id = Column(Integer, PrimaryKey = True)
    user_name = Column(String(100), unique = True, nullable = False)


