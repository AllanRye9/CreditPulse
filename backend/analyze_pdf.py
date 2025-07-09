#!/usr/bin/env python3
import fitz
import re
import sys

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        doc = fitz.open(pdf_path)
        text_content = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_content += page.get_text() + "\n"
        
        doc.close()
        return text_content
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

def find_aed_dhs_amounts(text):
    """Find AED/DHS amounts in the text"""
    amounts = []
    
    # Patterns for AED/DHS amounts
    patterns = [
        r'AED\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'DHS\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*AED',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*DHS',
        r'AED\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'DHS\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        # More flexible patterns
        r'(?:AED|DHS)[\s:]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:AED|DHS)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amount = match.group(1) if match.group(1) else match.group(0)
            amounts.append(amount)
    
    return amounts

def analyze_pdf_structure(text):
    """Analyze the structure of the PDF"""
    lines = text.split('\n')
    print(f"Total lines: {len(lines)}")
    print(f"Non-empty lines: {len([line for line in lines if line.strip()])}")
    
    # Look for common credit card statement keywords
    keywords = ['balance', 'payment', 'transaction', 'date', 'amount', 'credit', 'debit', 'statement']
    found_keywords = []
    
    for keyword in keywords:
        if keyword.lower() in text.lower():
            found_keywords.append(keyword)
    
    print(f"Found keywords: {found_keywords}")
    
    # Show first few lines with content
    print("\nFirst 20 non-empty lines:")
    count = 0
    for line in lines:
        if line.strip() and count < 20:
            print(f"{count+1}: {line.strip()}")
            count += 1

if __name__ == "__main__":
    pdf_path = "/Users/sbartoul/Desktop/complete_app/backend/Email Credit Card Statement_unlocked.pdf"
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    
    if text:
        print("PDF Analysis Results:")
        print("=" * 50)
        
        # Analyze structure
        analyze_pdf_structure(text)
        
        print("\n" + "=" * 50)
        print("AED/DHS Amounts Found:")
        print("=" * 50)
        
        # Find AED/DHS amounts
        amounts = find_aed_dhs_amounts(text)
        
        if amounts:
            unique_amounts = list(set(amounts))
            for amount in unique_amounts:
                print(f"- {amount}")
        else:
            print("No AED/DHS amounts found with standard patterns")
            
        print("\n" + "=" * 50)
        print("Full Text Content:")
        print("=" * 50)
        print(text)
    else:
        print("Failed to extract text from PDF")