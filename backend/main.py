from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uvicorn
from pydantic import BaseModel



from database import SessionLocal, engine, Base
from models import Customer, Transaction, CreditCard
from services.pdf_parser import PDFParser
from services.email_parser import EmailParser
from services.sms_parser import SMSParser
from services.transaction_extractor import TransactionExtractor
from services.categorizer import TransactionCategorizer
from services.anomaly_detector import AnomalyDetector
from services.reminder_service import ReminderService
from services.reward_analyzer import RewardAnalyzer
from services.transaction_deduplicator import TransactionDeduplicator
from schemas import (
    CustomerCreate, CustomerResponse, TransactionResponse, CreditCardResponse, 
    CreditCardCreate, SMSParseRequest, SMSParseResponse, SMSBatchParseRequest, SMSBatchParseResponse,
    EmailProcessRequest, ChatRequest
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Credit Card Management API",
    description="API for parsing credit card statements and managing payments",
    version="1.0.0"
)

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

import os
import httpx
from dotenv import load_dotenv
       
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")  # Store your API key in .env under this name
MODEL = "mistralai/mistral-7b-instruct:free"



@app.get("/")
async def root():
    return {"message": "Credit Card Management API"}

@app.post("/customers/", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.post("/upload-pdf/{customer_id}")
async def upload_pdf(
    customer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        pdf_parser = PDFParser()
        parsed_data = await pdf_parser.parse_pdf(file, customer)
        
        # Use advanced deduplication before saving to database
        deduplicator = TransactionDeduplicator()
        deduplication_result = deduplicator.deduplicate_transactions(parsed_data['transactions'])
        
        # Save deduplicated transactions to database
        transactions_saved = 0
        for transaction_data in deduplication_result['deduplicated_transactions']:
            transaction_date = datetime.strptime(transaction_data['date'], '%d-%m-%Y') if transaction_data['date'] else datetime.now()
            
            # Check for existing transaction in database
            existing_transaction = db.query(Transaction).filter(
                Transaction.customer_id == customer_id,
                Transaction.date == transaction_date,
                Transaction.amount == transaction_data['amount'],
                Transaction.merchant == transaction_data['merchant']
            ).first()
            
            if existing_transaction:
                continue
            
            transaction = Transaction(
                customer_id=customer_id,
                date=transaction_date,
                description=f"{transaction_data['merchant']} - {transaction_data['currency']} {transaction_data['amount']}",
                amount=transaction_data['amount'],
                category='purchase',
                subcategory='general',
                merchant=transaction_data['merchant'],
                is_recurring=False,
                confidence_score=0.9,
                raw_text=transaction_data['raw_text']
            )
            db.add(transaction)
            transactions_saved += 1
        
        # Update customer's credit card info if summary data available
        if parsed_data['summary']:
            summary = parsed_data['summary']
            # Find or create credit card record
            credit_card = db.query(CreditCard).filter(CreditCard.customer_id == customer_id).first()
            if credit_card:
                if 'current_balance' in summary:
                    credit_card.current_balance = summary['current_balance']
                if 'minimum_payment' in summary:
                    credit_card.minimum_payment = summary['minimum_payment']
                if 'credit_limit' in summary:
                    credit_card.credit_limit = summary['credit_limit']
                if 'due_date' in summary:
                    credit_card.due_date = summary['due_date']
                if 'statement_date' in summary:
                    credit_card.statement_date = summary['statement_date']
        
        db.commit()
        
        # Add transaction count and deduplication info to response
        parsed_data['transactions_saved'] = transactions_saved
        parsed_data['duplicates_removed'] = deduplication_result['duplicates_removed']
        parsed_data['original_transaction_count'] = deduplication_result['original_count']
        parsed_data['deduplicated_transaction_count'] = deduplication_result['deduplicated_count']
        parsed_data['deduplication_report'] = deduplicator.generate_deduplication_report(deduplication_result)
        
        return parsed_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/analyze-pdf/{customer_id}")
async def analyze_pdf(
    customer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Analyze PDF and return detailed structured data without saving to database"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        pdf_parser = PDFParser()
        parsed_data = await pdf_parser.parse_pdf(file, customer)
        
        # Add analysis metadata
        parsed_data['analysis_metadata'] = {
            'file_name': file.filename,
            'customer_id': customer_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'file_size': file.size if hasattr(file, 'size') else 'unknown'
        }
        
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing PDF: {str(e)}")

@app.post("/upload-email/{customer_id}")
async def upload_email(
    customer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Only EML email files are allowed")
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
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
                customer_id=customer_id,
                date=transaction_data.get('date'),
                description=transaction_data.get('description'),
                amount=transaction_data.get('amount'),
                category=transaction_data.get('category'),
                subcategory=transaction_data.get('subcategory'),
                merchant=transaction_data.get('merchant'),
                is_recurring=transaction_data.get('is_recurring', False),
                confidence_score=transaction_data.get('confidence_score'),
                raw_text=transaction_data.get('raw_text')
            )
            db.add(transaction)
        
        db.commit()
        
        return {"message": f"Processed {len(categorized_transactions)} transactions", "transactions_processed": len(categorized_transactions)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

@app.get("/customers/{customer_id}/transactions", response_model=List[TransactionResponse])
async def get_transactions(customer_id: int, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
    return transactions

@app.get("/customers/{customer_id}/anomalies")
async def detect_anomalies(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
    
    if not transactions:
        return {"anomalies": [], "message": "No transactions found for analysis"}
    
    try:
        anomaly_detector = AnomalyDetector()
        anomalies = anomaly_detector.detect_anomalies(transactions)
        
        return {"anomalies": anomalies, "total_anomalies": len(anomalies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")

@app.get("/customers/{customer_id}/due-dates")
async def get_due_dates(customer_id: int, db: Session = Depends(get_db)):
    reminder_service = ReminderService()
    due_dates = reminder_service.get_upcoming_due_dates(customer_id, db)
    
    return {"due_dates": due_dates}

@app.post("/customers/{customer_id}/credit-cards", response_model=CreditCardResponse)
async def create_credit_card(
    customer_id: int,
    card_data: CreditCardCreate,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    credit_card = CreditCard(customer_id=customer_id, **card_data.model_dump())
    db.add(credit_card)
    db.commit()
    db.refresh(credit_card)
    return credit_card

@app.get("/customers/{customer_id}/credit-cards", response_model=List[CreditCardResponse])
async def get_credit_cards(customer_id: int, db: Session = Depends(get_db)):
    credit_cards = db.query(CreditCard).filter(CreditCard.customer_id == customer_id).all()
    return credit_cards

@app.get("/customers/{customer_id}/rewards")
async def get_rewards_analysis(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
    credit_cards = db.query(CreditCard).filter(CreditCard.customer_id == customer_id).all()
    
    if not transactions:
        return {"rewards_analysis": {}, "message": "No transactions found for analysis"}
    
    try:
        reward_analyzer = RewardAnalyzer()
        analysis = reward_analyzer.analyze_rewards(transactions, credit_cards)
        
        return {"rewards_analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing rewards: {str(e)}")

@app.get("/customers/{customer_id}/spending-insights")
async def get_spending_insights(customer_id: int, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
    credit_cards = db.query(CreditCard).filter(CreditCard.customer_id == customer_id).all()
    
    reward_analyzer = RewardAnalyzer()
    insights = reward_analyzer.generate_spending_insights(transactions, credit_cards)
    
    return {"spending_insights": insights}

@app.post("/parse-sms", response_model=SMSParseResponse)
async def parse_sms(request: SMSParseRequest):
    try:
        sms_parser = SMSParser()
        parsed_data = sms_parser.parse_sms(request.sms_text)
        
        return SMSParseResponse(**parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing SMS: {str(e)}")

@app.post("/parse-sms-batch", response_model=SMSBatchParseResponse)
async def parse_sms_batch(request: SMSBatchParseRequest):
    try:
        sms_parser = SMSParser()
        results = sms_parser.parse_multiple_sms(request.sms_list)
        
        response_results = [SMSParseResponse(**result) for result in results]
        
        return SMSBatchParseResponse(
            results=response_results,
            total_processed=len(response_results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing SMS batch: {str(e)}")

@app.post("/customers/{customer_id}/process-sms")
async def process_sms_for_customer(
    customer_id: int,
    request: SMSParseRequest,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        sms_parser = SMSParser()
        parsed_data = sms_parser.parse_sms(request.sms_text)
        
        if parsed_data['sms_type'] == 'payment_due' and parsed_data['due_date'] and parsed_data['total_amount']:
            credit_card = None
            if parsed_data['card_last_four']:
                credit_card = db.query(CreditCard).filter(
                    CreditCard.customer_id == customer_id,
                    CreditCard.card_number_last_four == parsed_data['card_last_four']
                ).first()
            
            if parsed_data['total_amount']:
                transaction = Transaction(
                    customer_id=customer_id,
                    credit_card_id=credit_card.id if credit_card else None,
                    date=datetime.now(),
                    description=f"Payment due notification from SMS",
                    amount=parsed_data['total_amount'],
                    category='payment_due',
                    subcategory='bill_payment',
                    merchant=parsed_data['bank_name'] or 'Unknown Bank',
                    is_recurring=False,
                    is_anomaly=False,
                    confidence_score=parsed_data['confidence_score'],
                    raw_text=parsed_data['raw_text']
                )
                db.add(transaction)
                db.commit()
        
        return {
            "message": "SMS processed successfully",
            "parsed_data": parsed_data,
            "customer_id": customer_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing SMS: {str(e)}")

@app.post("/customers/{customer_id}/process-email")
async def process_email_for_customer(
    customer_id: int,
    request: EmailProcessRequest,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        email_parser = EmailParser()
        
        email_content = f"Subject: {request.subject}\nFrom: {request.sender}\nBody: {request.body}"
        
        parsed_email = {
            'subject': request.subject,
            'from': request.sender,
            'body': request.body,
            'extracted_info': email_parser.extract_financial_info(request.body)
        }
        
        transactions = email_parser.extract_transactions_from_email(parsed_email)
        
        processed_transactions = []
        if transactions:
            categorizer = TransactionCategorizer()
            categorized_transactions = categorizer.categorize_transactions(transactions)
            
            for transaction_data in categorized_transactions:
                transaction = Transaction(
                    customer_id=customer_id,
                    date=transaction_data.get('date') or datetime.now(),
                    description=transaction_data.get('description'),
                    amount=transaction_data.get('amount'),
                    category=transaction_data.get('category'),
                    subcategory=transaction_data.get('subcategory'),
                    merchant=transaction_data.get('merchant'),
                    is_recurring=transaction_data.get('is_recurring', False),
                    confidence_score=transaction_data.get('confidence_score'),
                    raw_text=transaction_data.get('raw_text')
                )
                db.add(transaction)
                processed_transactions.append(transaction_data)
            
            db.commit()
        
        return {
            "message": "Email processed successfully",
            "transactions_processed": len(processed_transactions),
            "parsed_email": parsed_email,
            "transactions": processed_transactions,
            "customer_id": customer_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

@app.post("/deduplicate-transactions")
async def deduplicate_transactions_endpoint(transactions: List[dict]):
    """
    Endpoint to test transaction deduplication on a provided list of transactions
    """
    try:
        deduplicator = TransactionDeduplicator()
        result = deduplicator.deduplicate_transactions(transactions)
        
        # Add the detailed report
        result['deduplication_report'] = deduplicator.generate_deduplication_report(result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deduplicating transactions: {str(e)}")

@app.post("/customers/{customer_id}/upload-email-content")
async def upload_email_content(
    customer_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        email_parser = EmailParser()
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False) as temp_file:
            temp_file.write(request['email_content'])
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as temp_file:
                upload_file = UploadFile(filename='email.eml', file=temp_file)
                parsed_email = await email_parser.parse_email(upload_file)
            
            transaction_extractor = TransactionExtractor()
            transactions = transaction_extractor.extract_transactions(parsed_email)
            
            processed_transactions = []
            if transactions:
                categorizer = TransactionCategorizer()
                categorized_transactions = categorizer.categorize_transactions(transactions)
                
                for transaction_data in categorized_transactions:
                    transaction = Transaction(
                        customer_id=customer_id,
                        date=transaction_data.get('date') or datetime.now(),
                        description=transaction_data.get('description'),
                        amount=transaction_data.get('amount'),
                        category=transaction_data.get('category'),
                        subcategory=transaction_data.get('subcategory'),
                        merchant=transaction_data.get('merchant'),
                        is_recurring=transaction_data.get('is_recurring', False),
                        confidence_score=transaction_data.get('confidence_score'),
                        raw_text=transaction_data.get('raw_text')
                    )
                    db.add(transaction)
                    processed_transactions.append(transaction_data)
                
                db.commit()
            
            return {
                "message": "Email content processed successfully",
                "transactions_processed": len(processed_transactions),
                "parsed_email": parsed_email,
                "transactions": processed_transactions
            }
        finally:
            os.unlink(temp_file_path)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing email content: {str(e)}")


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

            if response.status_code != 200:
                try:
                    error_detail = response.json()  # ✅ NO await here
                except Exception:
                    error_detail = response.text
                return {
                    "error": f"OpenRouter Error {response.status_code}",
                    "detail": error_detail
                }

            try:
                data = response.json()  # ✅ NO await here
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)