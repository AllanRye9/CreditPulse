#!/usr/bin/env python3
"""
Test script for transaction deduplication
"""

from services.transaction_deduplicator import TransactionDeduplicator
import json

# Sample data from your example
sample_transactions = [
    {
        "date": "05-10-2024",
        "merchant": "Unknown Merchant",
        "amount": 16.2,
        "currency": "AED",
        "raw_text": "05-10-2024 07-10-2024 Meat mart butchery and Abu Dhabi AE AED 16.20",
        "transaction_block": [
            "05-10-2024",
            "07-10-2024 Meat mart butchery and",
            "Abu Dhabi",
            "AE AED",
            "16.20"
        ]
    },
    {
        "date": "07-10-2024",
        "merchant": "Unknown Merchant",
        "amount": 16.2,
        "currency": "AED",
        "raw_text": "07-10-2024 Meat mart butchery and Abu Dhabi AE AED 16.20 16.20",
        "transaction_block": [
            "07-10-2024 Meat mart butchery and",
            "Abu Dhabi",
            "AE AED",
            "16.20",
            "16.20"
        ]
    },
    {
        "date": "08-10-2024",
        "merchant": "Unknown Merchant",
        "amount": 34,
        "currency": "AED",
        "raw_text": "08-10-2024 10-10-2024 Meat mart butchery and Abu Dhabi AE AED 34.00",
        "transaction_block": [
            "08-10-2024",
            "10-10-2024 Meat mart butchery and",
            "Abu Dhabi",
            "AE AED",
            "34.00"
        ]
    },
    {
        "date": "10-10-2024",
        "merchant": "Unknown Merchant",
        "amount": 34,
        "currency": "AED",
        "raw_text": "10-10-2024 Meat mart butchery and Abu Dhabi AE AED 34.00 34.00",
        "transaction_block": [
            "10-10-2024 Meat mart butchery and",
            "Abu Dhabi",
            "AE AED",
            "34.00",
            "34.00"
        ]
    },
    {
        "date": "08-10-2024",
        "merchant": "LULU CENTER ABU DHABI AE AED",
        "amount": 248.9,
        "currency": "AED",
        "raw_text": "08-10-2024 10-10-2024 LULU CENTER ABU DHABI AE AED 248.90",
        "transaction_block": [
            "08-10-2024",
            "10-10-2024 LULU CENTER",
            "ABU DHABI",
            "AE AED",
            "248.90"
        ]
    }
]

def test_deduplication():
    print("Testing Transaction Deduplication")
    print("=" * 50)
    
    # Create deduplicator
    deduplicator = TransactionDeduplicator()
    
    # Perform deduplication
    result = deduplicator.deduplicate_transactions(sample_transactions)
    
    # Print results
    print(f"Original count: {result['original_count']}")
    print(f"Deduplicated count: {result['deduplicated_count']}")
    print(f"Duplicates removed: {result['duplicates_removed']}")
    print(f"Duplicate groups: {len(result['duplicate_groups'])}")
    print()
    
    # Show detailed report
    report = deduplicator.generate_deduplication_report(result)
    print(report)
    
    # Show final deduplicated transactions
    print("FINAL DEDUPLICATED TRANSACTIONS:")
    print("=" * 40)
    for i, trans in enumerate(result['deduplicated_transactions']):
        print(f"{i+1}. {trans['date']} - {trans['merchant']} - {trans['amount']} {trans['currency']}")
    
    return result

if __name__ == "__main__":
    test_deduplication()