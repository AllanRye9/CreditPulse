#!/usr/bin/env python3

from services.sms_parser import SMSParser
from datetime import datetime

def test_sms_parsing():
    parser = SMSParser()
    
    test_cases = [
        "Dear Customer, Your Emirates NBD credit card ending in 1234 has a payment due of AED 15,000 on 25th March 2024. Please pay by the due date to avoid late charges.",
        
        "Payment reminder: Your ADCB credit card bill of AED 8,500 is due on 15/03/2024. Minimum payment due: AED 850. Pay now to avoid charges.",
        
        "Payment successful! AED 5,000 has been paid towards your FAB credit card ending in 5678. Current outstanding balance: AED 12,000.",
        
        "Your monthly statement is ready. Total outstanding amount: AED 25,000. Due date: March 20, 2024. Card: Mashreq Bank ****4567",
        
        "Auto-pay successful for AED 3,500 on your HSBC credit card. Remaining balance: AED 8,900. Due date: 28th March.",
        
        "Alert: Payment of AED 2,000 failed for your Emirates NBD credit card ****1234 due to insufficient funds. Please try again.",
        
        "Your credit card bill is generated. Total amount: DHS 1,200. Due: 03/25/2024. Card ending 9876.",
        
        "Payment due reminder: AED 18500 due on 22 Mar. Card: CITI ****2345. Pay minimum AED 1850 to avoid late fee.",
        
        "Transaction alert: AED 1,500 spent at Mall of Emirates using your ENBD card ****1234 on 15-03-2024.",
        
        "Statement generated: Outstanding balance AED 45,000. Due 30th March. Minimum payment AED 4,500. Card: AMEX ****7890",
        
        "Payment confirmation: 2,500 AED paid successfully to your CBD credit card ****5678. Thank you for your payment.",
        
        "Your Mashreq credit card balance is 12,000 DHS. Due date: 15th April. Please pay minimum 1,200 DHS to avoid charges."
    ]
    
    print("SMS Parsing Test Results:")
    print("=" * 60)
    
    for i, sms in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"SMS: {sms}")
        print("-" * 40)
        
        try:
            result = parser.parse_sms(sms)
            
            print(f"SMS Type: {result['sms_type']}")
            print(f"Due Date: {result['due_date']}")
            print(f"Total Amount: {result['total_amount']}")
            print(f"Remaining Amount: {result['remaining_amount']}")
            print(f"Payment Amount: {result['payment_amount']}")
            print(f"Payment Status: {result['payment_status']}")
            print(f"Card Last Four: {result['card_last_four']}")
            print(f"Bank Name: {result['bank_name']}")
            print(f"Confidence Score: {result['confidence_score']:.2f}")
            
            summary = parser.get_payment_summary(result)
            print(f"Summary: {summary}")
            
        except Exception as e:
            print(f"Error parsing SMS: {e}")
        
        print("-" * 40)

def test_batch_parsing():
    parser = SMSParser()
    
    batch_sms = [
        "Payment due: AED 5000 on 25th March. Card: Emirates NBD ****1234",
        "Payment successful: AED 2000 paid. Balance: AED 3000",
        "Monthly statement ready. Total: AED 15000. Due: March 30th"
    ]
    
    print("\n\nBatch Parsing Test:")
    print("=" * 40)
    
    results = parser.parse_multiple_sms(batch_sms)
    
    for i, result in enumerate(results, 1):
        print(f"\nBatch Item {i}:")
        print(f"Type: {result['sms_type']}")
        print(f"Due Date: {result['due_date']}")
        print(f"Amount: {result['total_amount'] or result['remaining_amount'] or result['payment_amount']}")
        print(f"Confidence: {result['confidence_score']:.2f}")

if __name__ == "__main__":
    test_sms_parsing()
    test_batch_parsing()