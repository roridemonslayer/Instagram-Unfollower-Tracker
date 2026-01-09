from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, relationship
from typing import List

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
    relationship: Mapped[List["FollowRelationship"]] = relationship(back_populates = "user") #we're using list because we're tracking many users under the follow relaitonship
class FollowRelationship(Base):
    __tablename__ ="follower_relationships"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id")) #this just the link to the user table, allows you to return not just the table number but assigned the id to the user 
    instagram_user_id = (Column(String(500), nullable = False))
    full_name = (Column(String(100))) #user full name 
    profile_pic_url = (Column(String(300))) # profile flics
    username = Column(String(100), unique = True, nullable = False)
    i_follow_them = Column(Boolean, default = True)
    they_follow_me= Column(Boolean,default = False ) #this could be either true of false depending 
    last_checked = Column(DateTime,default = func.now())
    user : Mapped["User"] = relationship(back_populates = "relationship")
    #note that when using back_poulates, conect it to the attrivuate not the class. 
#want to go from follower relationship to user 
#and user relaitosnhip to user  but we cna just add mapping to the two classes we have above
