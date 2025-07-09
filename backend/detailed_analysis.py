#!/usr/bin/env python3
import fitz
import re
from datetime import datetime

def extract_detailed_transactions(text):
    """Extract detailed transaction information with AED amounts"""
    transactions = []
    lines = text.split('\n')
    
    # Look for transaction patterns
    for i, line in enumerate(lines):
        # Look for date patterns followed by merchant info and AED amounts
        date_pattern = r'(\d{2}-\d{2}-\d{4})'
        if re.search(date_pattern, line):
            # Check next few lines for merchant and amount info
            transaction_block = []
            for j in range(i, min(i+5, len(lines))):
                if lines[j].strip():
                    transaction_block.append(lines[j].strip())
            
            # Look for AED amounts in this block
            full_block = ' '.join(transaction_block)
            aed_pattern = r'AED\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            amount_matches = re.findall(aed_pattern, full_block)
            
            if amount_matches:
                transactions.append({
                    'block': transaction_block,
                    'amounts': amount_matches,
                    'raw_text': full_block
                })
    
    return transactions

def extract_summary_amounts(text):
    """Extract key summary amounts from the statement"""
    summary = {}
    
    # Key patterns to look for
    patterns = {
        'current_balance': r'Current Balance.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        'minimum_payment': r'Minimum Payment Due.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        'total_payment': r'Total Payment Due.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        'previous_balance': r'Previous Balance.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        'credit_limit': r'Total Credit Limit.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        'available_credit': r'Available Credit Limit.*?(\d+(?:,\d{3})*(?:\.\d{2})?)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            summary[key] = match.group(1)
    
    return summary

def format_currency(amount_str):
    """Format currency amount for display"""
    try:
        # Remove commas and convert to float
        amount = float(amount_str.replace(',', ''))
        return f"AED {amount:,.2f}"
    except:
        return f"AED {amount_str}"

def main():
    pdf_path = "/Users/sbartoul/Desktop/complete_app/backend/Email Credit Card Statement_unlocked.pdf"
    
    # Extract text
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    print("FIRST ABU DHABI BANK CREDIT CARD STATEMENT ANALYSIS")
    print("=" * 60)
    
    # Extract summary information
    summary = extract_summary_amounts(text)
    
    print("\nSUMMARY INFORMATION:")
    print("-" * 30)
    for key, value in summary.items():
        formatted_key = key.replace('_', ' ').title()
        print(f"{formatted_key}: {format_currency(value)}")
    
    # Extract detailed transactions
    transactions = extract_detailed_transactions(text)
    
    print(f"\nTRANSACTIONS FOUND: {len(transactions)}")
    print("-" * 30)
    
    total_spent = 0
    for i, transaction in enumerate(transactions, 1):
        print(f"\nTransaction {i}:")
        print(f"Raw text: {transaction['raw_text'][:100]}...")
        
        for amount in transaction['amounts']:
            try:
                amount_float = float(amount.replace(',', ''))
                total_spent += amount_float
                print(f"Amount: {format_currency(amount)}")
            except:
                print(f"Amount: AED {amount}")
    
    print(f"\nTotal transactions amount: {format_currency(str(total_spent))}")
    
    # Extract all AED amounts for verification
    print("\nALL AED AMOUNTS DETECTED:")
    print("-" * 30)
    
    aed_amounts = re.findall(r'AED\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
    amount_only = re.findall(r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*AED', text)
    
    all_amounts = aed_amounts + amount_only
    unique_amounts = list(set(all_amounts))
    
    for amount in sorted(unique_amounts, key=lambda x: float(x.replace(',', ''))):
        print(f"- {format_currency(amount)}")
    
    print(f"\nTotal unique amounts found: {len(unique_amounts)}")

if __name__ == "__main__":
    main()