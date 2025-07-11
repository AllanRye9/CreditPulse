from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    
class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    date_of_birth: str

class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: str
    date_of_birth: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    date: datetime
    description: str
    amount: float
    category: Optional[str]
    subcategory: Optional[str]
    merchant: Optional[str]
    is_recurring: bool
    is_anomaly: bool
    confidence_score: Optional[float]
    
    class Config:
        from_attributes = True

class CreditCardResponse(BaseModel):
    id: int
    card_number_last_four: str
    bank_name: str
    card_type: str
    credit_limit: float
    current_balance: float
    minimum_payment: float
    due_date: str
    statement_date: str
    apr: float
    rewards_rate: float
    
    class Config:
        from_attributes = True

class AnomalyResponse(BaseModel):
    transaction_id: int
    anomaly_type: str
    score: float
    description: str

class DueDateResponse(BaseModel):
    credit_card_id: int
    bank_name: str
    due_date: str
    amount: float
    days_until_due: int

class CreditCardCreate(BaseModel):
    card_number_last_four: str
    bank_name: str
    card_type: str
    credit_limit: float
    current_balance: float
    minimum_payment: float
    due_date: str
    statement_date: str
    apr: float
    rewards_rate: float

class RewardAnalysisResponse(BaseModel):
    total_rewards_earned: float
    rewards_by_category: Dict[str, float]
    potential_rewards: float
    optimization_suggestions: List[str]

class SpendingInsightsResponse(BaseModel):
    monthly_spending: Dict[str, float]
    category_breakdown: Dict[str, float]
    trends: List[str]
    recommendations: List[str]

class SMSParseRequest(BaseModel):
    sms_text: str

class SMSParseResponse(BaseModel):
    raw_text: str
    due_date: Optional[datetime]
    total_amount: Optional[float]
    remaining_amount: Optional[float]
    payment_amount: Optional[float]
    payment_status: Optional[str]
    card_last_four: Optional[str]
    bank_name: Optional[str]
    sms_type: str
    extracted_amounts: List[float]
    extracted_dates: List[datetime]
    confidence_score: float

class SMSBatchParseRequest(BaseModel):
    sms_list: List[str]

class SMSBatchParseResponse(BaseModel):
    results: List[SMSParseResponse]
    total_processed: int

class EmailProcessRequest(BaseModel):
    subject: str
    sender: str
    body: str
    parsed_data: Optional[Dict[str, Any]] = None

class PDFTransactionResponse(BaseModel):
    date: Optional[str]
    merchant: str
    amount: float
    currency: str
    raw_text: str

class PDFSummaryResponse(BaseModel):
    current_balance: Optional[float]
    minimum_payment: Optional[float]
    total_payment: Optional[float]
    previous_balance: Optional[float]
    credit_limit: Optional[float]
    available_credit: Optional[float]
    statement_date: Optional[str]
    due_date: Optional[str]

class PDFAmountResponse(BaseModel):
    amount: float
    currency: str
    raw_match: str
    context: str

class PDFStatisticsResponse(BaseModel):
    total_transactions: int
    total_amount: float
    unique_amounts_found: int
    currency: str

class PDFParseResponse(BaseModel):
    raw_text: str
    cleaned_text: str
    transactions: List[PDFTransactionResponse]
    summary: PDFSummaryResponse
    aed_amounts: List[PDFAmountResponse]
    statistics: PDFStatisticsResponse
    extraction_success: bool