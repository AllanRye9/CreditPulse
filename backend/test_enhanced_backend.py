#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced PDF parsing functionality
"""
import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def create_test_customer():
    """Create a test customer"""
    customer_data = {
        "name": "Mohammed Maaz Shaikh",
        "email": "mohammed.maaz@example.com",
        "phone_number": "+971501234567",
        "date_of_birth": "1990-01-01"
    }
    
    response = requests.post(f"{BASE_URL}/customers/", json=customer_data)
    if response.status_code == 200:
        customer = response.json()
        print(f"✅ Created customer: {customer['name']} (ID: {customer['id']})")
        return customer['id']
    else:
        print(f"❌ Failed to create customer: {response.text}")
        return None

def analyze_pdf(customer_id, pdf_path):
    """Analyze PDF using the enhanced endpoint"""
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('statement.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/analyze-pdf/{customer_id}", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PDF Analysis successful!")
            print(f"📊 Analysis Results:")
            print(f"   - Transactions found: {data['statistics']['total_transactions']}")
            print(f"   - Total amount: AED {data['statistics']['total_amount']:,.2f}")
            print(f"   - Unique amounts: {data['statistics']['unique_amounts_found']}")
            print(f"   - Currency: {data['statistics']['currency']}")
            
            # Show summary information
            if data['summary']:
                print(f"\\n💳 Credit Card Summary:")
                summary = data['summary']
                if 'current_balance' in summary:
                    print(f"   - Current Balance: AED {summary['current_balance']:,.2f}")
                if 'minimum_payment' in summary:
                    print(f"   - Minimum Payment: AED {summary['minimum_payment']:,.2f}")
                if 'credit_limit' in summary:
                    print(f"   - Credit Limit: AED {summary['credit_limit']:,.2f}")
                if 'due_date' in summary:
                    print(f"   - Due Date: {summary['due_date']}")
            
            # Show first few transactions
            print(f"\\n🛍️  Sample Transactions:")
            for i, transaction in enumerate(data['transactions'][:5]):
                print(f"   {i+1}. {transaction['date']} - {transaction['merchant']} - AED {transaction['amount']:,.2f}")
            
            # Show all unique amounts
            print(f"\\n💰 All AED Amounts Found:")
            for amount in data['aed_amounts']:
                print(f"   - AED {amount['amount']:,.2f}")
            
            return data
        else:
            print(f"❌ PDF Analysis failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error analyzing PDF: {str(e)}")
        return None

def upload_pdf_with_save(customer_id, pdf_path):
    """Upload PDF and save to database"""
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('statement.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload-pdf/{customer_id}", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PDF Upload and processing successful!")
            print(f"💾 Saved {data.get('transactions_saved', 0)} transactions to database")
            return data
        else:
            print(f"❌ PDF Upload failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error uploading PDF: {str(e)}")
        return None

def get_customer_transactions(customer_id):
    """Get all transactions for a customer"""
    try:
        response = requests.get(f"{BASE_URL}/customers/{customer_id}/transactions")
        if response.status_code == 200:
            transactions = response.json()
            print(f"✅ Retrieved {len(transactions)} transactions from database")
            
            if transactions:
                print(f"\\n📋 Database Transactions:")
                for i, transaction in enumerate(transactions[:10]):  # Show first 10
                    print(f"   {i+1}. {transaction['date']} - {transaction['merchant']} - AED {transaction['amount']:,.2f}")
                    print(f"      Category: {transaction['category']}")
            
            return transactions
        else:
            print(f"❌ Failed to get transactions: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting transactions: {str(e)}")
        return None

def main():
    print("🚀 Testing Enhanced PDF Backend\\n")
    
    # Test PDF path
    pdf_path = "/Users/sbartoul/Desktop/complete_app/backend/Email Credit Card Statement_unlocked.pdf"
    
    # Create test customer
    customer_id = create_test_customer()
    if not customer_id:
        return
    
    print("\\n" + "="*60)
    print("🔍 PHASE 1: PDF Analysis (Read-only)")
    print("="*60)
    
    # Analyze PDF without saving
    analysis_result = analyze_pdf(customer_id, pdf_path)
    
    print("\\n" + "="*60)
    print("💾 PHASE 2: PDF Upload and Save")
    print("="*60)
    
    # Upload PDF and save to database
    upload_result = upload_pdf_with_save(customer_id, pdf_path)
    
    print("\\n" + "="*60)
    print("📊 PHASE 3: Database Verification")
    print("="*60)
    
    # Get transactions from database
    db_transactions = get_customer_transactions(customer_id)
    
    print("\\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
    
    print(f"\\n📈 Summary:")
    print(f"   - Customer created: {customer_id}")
    print(f"   - PDF analysis: {'✅ Success' if analysis_result else '❌ Failed'}")
    print(f"   - PDF upload: {'✅ Success' if upload_result else '❌ Failed'}")
    print(f"   - Database transactions: {len(db_transactions) if db_transactions else 0}")

if __name__ == "__main__":
    main()