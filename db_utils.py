from sqlalchemy import create_engine, Column, String, JSON, Text, DateTime, Boolean, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Resume(Base):
    __tablename__ = "resumes"
    
    email = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    position = Column(String)
    raw_text = Column(Text)
    full_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    username = Column(String(50), primary_key=True)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    api_key = Column(String(64), unique=True)

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")

def create_admin_user(username: str, password: str, full_name: str):
    db = SessionLocal()
    try:
        if db.query(AdminUser).filter(AdminUser.username == username).first():
            return False, "Username already exists"
            
        new_admin = AdminUser(
            username=username,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            api_key=secrets.token_hex(32),
            is_active=True
        )
        db.add(new_admin)
        db.commit()
        return True, "Admin user created successfully"
    except Exception as e:
        db.rollback()
        return False, f"Error creating admin: {str(e)}"
    finally:
        db.close()

def save_parsed_resume(resume_data: dict, primary_key: str):
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if not inspector.has_table("resumes"):
            create_tables()
        
        existing = db.query(Resume).filter(Resume.email == primary_key).first()
        
        if existing:
            existing.name = resume_data["contact_info"]["name"]
            existing.phone = resume_data["contact_info"]["phone"]
            existing.position = resume_data["contact_info"].get("position", "")
            existing.raw_text = resume_data["raw_text"]
            existing.full_data = resume_data
            action = "updated"
        else:
            new_resume = Resume(
                email=primary_key,
                name=resume_data["contact_info"]["name"],
                phone=resume_data["contact_info"]["phone"],
                position=resume_data["contact_info"].get("position", ""),
                raw_text=resume_data["raw_text"],
                full_data=resume_data
            )
            db.add(new_resume)
            action = "created"
        
        db.commit()
        return True, f"Record {action} successfully for {primary_key}"
    except IntegrityError as e:
        db.rollback()
        return False, f"Database integrity error: {str(e)}"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        db.close()

# Initialize database
create_tables()