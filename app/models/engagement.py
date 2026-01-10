from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from .user import Base
import datetime 

class EngagementScore:
    __tablename__ = "engagement_score"
    id = Column(Integer, primary_key = True) #id for each accounts 
    user_id = Column(Integer , ForeignKey ("users.id")) # ;link to the use who owns thier data
    #the followers username 
    follower_username = Column(String(200), nullable = False) # can't be empy 

    #metrics 
    total_score = Column(Float)
    likes_count = Column(Integer, default = 0) #how mnay posts they likes 
    comments_count = Column(Integer, default= 0) #how many comments they left 

    #timing data 
    last_interaction_date = Column(DateTime) #last time they interacted with your stuff 
    calculated_at = Column(DateTime, default= datetime.datetime.utcnow) #when it was calculated 
    
    #categorizing 
    engagement_level = Column(String(20)) #if it's high, low or medium 

    #relationship with user 
    user = relationship("User", back_populates="engagement_scores")