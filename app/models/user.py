from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    insta_user = Column(String, unique=True, nullable=False)
    insta_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    follow_relationships = relationship("FollowRelationship", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, insta_user={self.insta_user})>"


class FollowRelationship(Base):
    __tablename__ = 'follow_relationships'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    instagram_user_id = Column(String, nullable=False)  # Instagram's internal ID
    username = Column(String, nullable=False)
    full_name = Column(String, default="")
    profile_pic_url = Column(String, default="")
    i_follow_them = Column(Boolean, default=False)
    they_follow_me = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Optional: engagement tracking columns
    engagement_score = Column(Integer, default=0)
    engagement_level = Column(String, default='Ghost')
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    
    # Relationship back to User
    user = relationship("User", back_populates="follow_relationships")
    
    def __repr__(self):
        return f"<FollowRelationship(username={self.username}, i_follow={self.i_follow_them}, they_follow={self.they_follow_me})>"