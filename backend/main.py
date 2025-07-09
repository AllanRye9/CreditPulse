from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from fastapi import Request
from database import SessionLocal, engine, Base
from models import Customer, Transaction, CreditCard
from services.pdf_parser import PDFParser
from services.email_parser import EmailParser
from services.transaction_extractor import TransactionExtractor
from services.categorizer import TransactionCategorizer
from services.anomaly_detector import AnomalyDetector
from services.reminder_service import ReminderService
from services.reward_analyzer import RewardAnalyzer
from schemas import CustomerCreate, CustomerResponse, TransactionResponse, CreditCardResponse, CreditCardCreate
from pydantic import BaseModel
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="42 Abu Dhabi Hackathon",
    description="API for parsing credit card statements and managing payments",
    version="1.0.0"
)

API_KEY = os.getenv("OPENROUTER_API_KEY")  # Set your key in .env or directly here
MODEL = "mistralai/mistral-7b-instruct"


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(chat_request: ChatRequest):
    user_message = chat_request.message

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful banking assistant."},
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )

            # Handle non-200 responses
            if response.status_code != 200:
                try:
                    error_detail = response.json()
                except Exception:
                    error_detail = response.text
                return {
                    "error": f"OpenRouter Error {response.status_code}",
                    "detail": error_detail
                }

            # Handle success
            try:
                data = response.json()
                reply = data["choices"][0]["message"]["content"]
                return {"response": reply}
            except Exception as e:
                return {
                    "error": "Failed to parse response from OpenRouter.",
                    "detail": str(e)
                }

        except httpx.RequestError as e:
            return {
                "error": "Connection error with OpenRouter API",
                "detail": str(e)
            }

        except Exception as e:
            return {
                "error": "Unexpected server error",
                "detail": str(e)
            }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Credit Card Management API"}


@app.post("/customer", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: Session=Depends(get_db)):
    existing = db.query(Customer).first()
    if existing:
        raise HTTPException(status_code=400, detail="Customer already exists")
    db_customer = Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def get_single_customer(db: Session):
    customer = db.query(Customer).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile=File(...), db: Session=Depends(get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    try:
        customer = get_single_customer(db)
        pdf_parser = PDFParser()
        content = await pdf_parser.parse_pdf(file, customer)
        transaction_extractor = TransactionExtractor()
        transactions = transaction_extractor.extract_transactions(content)
        if not transactions:
            return {"message": "No transactions found in the PDF", "transactions_processed": 0}
        categorizer = TransactionCategorizer()
        categorized_transactions = categorizer.categorize_transactions(transactions)
        for transaction_data in categorized_transactions:
            transaction = Transaction(
                customer_id=customer.id,
                **transaction_data
            )
            db.add(transaction)
        db.commit()
        return {
            "message": f"Processed {len(categorized_transactions)} transactions",
            "transactions_processed": len(categorized_transactions)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/upload-email")
async def upload_email(file: UploadFile=File(...), db: Session=Depends(get_db)):
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Only EML files are allowed")
    try:
        customer = get_single_customer(db)
        email_parser = EmailParser()
        content = await email_parser.parse_email(file)
        transaction_extractor = TransactionExtractor()
        transactions = transaction_extractor.extract_transactions(content)
        if not transactions:
            return {"message": "No transactions found in the email", "transactions_processed": 0}
        categorizer = TransactionCategorizer()
        categorized_transactions = categorizer.categorize_transactions(transactions)
        for transaction_data in categorized_transactions:
            transaction = Transaction(
                customer_id=customer.id,
                **transaction_data
            )
            db.add(transaction)
        db.commit()
        return {
            "message": f"Processed {len(categorized_transactions)} transactions",
            "transactions_processed": len(categorized_transactions)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")


@app.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(db: Session=Depends(get_db)):
    customer = get_single_customer(db)
    return db.query(Transaction).filter(Transaction.customer_id == customer.id).all()


@app.get("/anomalies")
async def detect_anomalies(db: Session=Depends(get_db)):
    customer = get_single_customer(db)
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer.id).all()
    if not transactions:
        return {"anomalies": [], "message": "No transactions found for analysis"}
    try:
        anomaly_detector = AnomalyDetector()
        anomalies = anomaly_detector.detect_anomalies(transactions)
        return {"anomalies": anomalies, "total_anomalies": len(anomalies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@app.get("/due-dates")
async def get_due_dates(db: Session=Depends(get_db)):
    customer = get_single_customer(db)
    reminder_service = ReminderService()
    due_dates = reminder_service.get_upcoming_due_dates(customer.id, db)
    return {"due_dates": due_dates}


@app.post("/credit-cards", response_model=CreditCardResponse)
async def create_credit_card(card_data: CreditCardCreate, db: Session=Depends(get_db)):
    customer = get_single_customer(db)
    credit_card = CreditCard(customer_id=customer.id, **card_data.dict())
    db.add(credit_card)
    db.commit()
    db.refresh(credit_card)
    return credit_card


@app.get("/credit-cards", response_model=List[CreditCardResponse])
async def get_credit_cards(db: Session=Depends(get_db)):
    customer = get_single_customer(db)
    return db.query(CreditCard).filter(CreditCard.customer_id == customer.id).all()


@app.get("/rewards")
async def get_rewards_analysis(db: Session=Depends(get_db)):
    customer = get_single_customer(db)
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer.id).all()
    credit_cards = db.query(CreditCard).filter(CreditCard.customer_id == customer.id).all()
    if not transactions:
        return {"rewards_analysis": {}, "message": "No transactions found for analysis"}
    try:
        reward_analyzer = RewardAnalyzer()
        analysis = reward_analyzer.analyze_rewards(transactions, credit_cards)
        return {"rewards_analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing rewards: {str(e)}")


@app.get("/spending-insights")
async def get_spending_insights(db: Session=Depends(get_db)):
    customer = get_single_customer(db)
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer.id).all()
    credit_cards = db.query(CreditCard).filter(CreditCard.customer_id == customer.id).all()
    reward_analyzer = RewardAnalyzer()
    insights = reward_analyzer.generate_spending_insights(transactions, credit_cards)
    return {"spending_insights": insights}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
