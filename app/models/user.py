from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, func, ForeignKey
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
class FollowRelationship(Base):
    __tablename__ ="follower_relationships"
    id = Column(Integer, primary_key = True)
    users_id = Column(Integer, ForeignKey("users.id")) #this just the link to the user table
    instagram_user_id = (Column(String(500), nullable = False))
    full_name = (Column(String(100))) #user full name 
    profile_pic_url = (Column(String(300))) # profile flics
    username = Column(String(100), unique = True, nullable = False)
    i_follow_them = Column(Boolean, default = True)
    they_follow_me= Column(Boolean,default = False ) #this could be either true of false depending 
    last_checked = Column(DateTime,default = func.now())
