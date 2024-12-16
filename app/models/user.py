from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    organization_id = Column(Integer, ForeignKey("organization.id"))
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
