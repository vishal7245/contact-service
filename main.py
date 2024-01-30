from fastapi import FastAPI ,HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import smtplib ,os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import create_engine, Column, String, Date, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from sqlalchemy.sql import func
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


load_dotenv()


app = FastAPI(title="Contact" ,version="4.0")


# VERY IMPORTANT DO NOT TOUCH THIS. IT JUST WORKS
origins = ["*"]  

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#API KEY AND AUTHENTICATION
API_KEY = os.getenv("API_KEY")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )


#DATABASE FUNCTIONS
Base = declarative_base()
class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255),nullable=False)
    email = Column(String(255),nullable=False)
    designation = Column(String(255),nullable=False)
    subject = Column(String(255),nullable=False)
    body = Column(Text,nullable=False)
    created_date = Column(Date, default=func.current_date())

def write_to_database(name, email, designation, subject, body):
    engine = create_engine(os.getenv("DATABASE_URL"), echo=True)

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    contact = Contact(
        name=name,
        email=email,
        designation=designation,
        subject=subject,
        body=body,
        created_date=datetime.utcnow()
    )

    session.add(contact)
    session.commit()




#API ENDPOINT
class EmailRequest(BaseModel):
    query_mail : str
    Name:str
    Designation: str
    title: str
    body: str

@app.post("/send_mail")
async def endpoint_to_send_email(request_data : EmailRequest, api_key: str = Depends(get_api_key)):
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    subject = "Rawallab Contact"
    body = f""" 
            Title: {request_data.title}

            Message: {request_data.body}

            Name: {request_data.Name}
            Designation: {request_data.Designation}
            Email: {request_data.query_mail}
            """
    
    # WRITING IN DATABASE
    write_to_database(name=request_data.Name, email=request_data.query_mail, designation=request_data.Designation, subject=request_data.title, body=body)

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = os.getenv("SENDER_EMAIL")
    smtp_password = os.getenv("SENDER_PASSWORD")
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    return JSONResponse(content={"status":"Email Sent"})



