from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
import hashlib
import json
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TransactionMatch:
    """Represents a potential duplicate transaction match"""
    original_index: int
    duplicate_index: int
    confidence: float
    match_criteria: List[str]


class TransactionDeduplicator:
    """
    Advanced transaction deduplication service that identifies and removes duplicate transactions
    based on multiple criteria including exact matches, fuzzy matches, and business rules.
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        
    def deduplicate_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Remove duplicate transactions from a list of transaction dictionaries.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Dictionary containing deduplicated transactions and metadata
        """
        if not transactions:
            return {
                "deduplicated_transactions": [],
                "original_count": 0,
                "deduplicated_count": 0,
                "duplicates_removed": 0,
                "duplicate_groups": []
            }
        
        # Find all duplicate groups
        duplicate_groups = self._find_duplicate_groups(transactions)
        
        # Keep only the first transaction from each group
        indices_to_keep = set(range(len(transactions)))
        duplicates_removed = 0
        
        for group in duplicate_groups:
            # Keep the first transaction in each group, remove the rest
            for i in range(1, len(group)):
                if group[i] in indices_to_keep:
                    indices_to_keep.remove(group[i])
                    duplicates_removed += 1
        
        # Create deduplicated list
        deduplicated_transactions = [
            transactions[i] for i in sorted(indices_to_keep)
        ]
        
        return {
            "deduplicated_transactions": deduplicated_transactions,
            "original_count": len(transactions),
            "deduplicated_count": len(deduplicated_transactions),
            "duplicates_removed": duplicates_removed,
            "duplicate_groups": [
                {
                    "group_id": idx,
                    "transaction_indices": group,
                    "transactions": [transactions[i] for i in group]
                }
                for idx, group in enumerate(duplicate_groups)
            ]
        }
    
    def _find_duplicate_groups(self, transactions: List[Dict[str, Any]]) -> List[List[int]]:
        """Find groups of duplicate transactions"""
        duplicate_groups = []
        processed_indices = set()
        
        for i, transaction in enumerate(transactions):
            if i in processed_indices:
                continue
                
            # Find all transactions that match this one
            current_group = [i]
            
            for j in range(i + 1, len(transactions)):
                if j in processed_indices:
                    continue
                    
                if self._are_transactions_duplicates(transaction, transactions[j]):
                    current_group.append(j)
                    processed_indices.add(j)
            
            # Only add groups with more than one transaction
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
                processed_indices.update(current_group)
        
        return duplicate_groups
    
    def _are_transactions_duplicates(self, trans1: Dict[str, Any], trans2: Dict[str, Any]) -> bool:
        """
        Determine if two transactions are duplicates using multiple criteria
        """
        # Exact match criteria
        if self._exact_match(trans1, trans2):
            return True
        
        # Fuzzy match criteria
        if self._fuzzy_match(trans1, trans2):
            return True
        
        # Business rule based matching
        if self._business_rule_match(trans1, trans2):
            return True
            
        return False
    
    def _exact_match(self, trans1: Dict[str, Any], trans2: Dict[str, Any]) -> bool:
        """Check for exact matches on key fields"""
        key_fields = ['date', 'amount', 'currency', 'merchant']
        
        for field in key_fields:
            val1 = trans1.get(field)
            val2 = trans2.get(field)
            
            if val1 != val2:
                return False
        
        return True
    
    def _fuzzy_match(self, trans1: Dict[str, Any], trans2: Dict[str, Any]) -> bool:
        """Check for fuzzy matches allowing for slight variations"""
        # Same amount and currency
        if (trans1.get('amount') != trans2.get('amount') or 
            trans1.get('currency') != trans2.get('currency')):
            return False
        
        # Similar dates (within 2 days)
        if not self._dates_are_similar(trans1.get('date'), trans2.get('date')):
            return False
        
        # Similar merchant names
        if not self._merchants_are_similar(trans1.get('merchant'), trans2.get('merchant')):
            return False
        
        return True
    
    def _business_rule_match(self, trans1: Dict[str, Any], trans2: Dict[str, Any]) -> bool:
        """Apply business-specific rules for duplicate detection"""
        # Rule 1: Same raw_text (common in your data)
        if (trans1.get('raw_text') and trans2.get('raw_text') and
            trans1.get('raw_text') == trans2.get('raw_text')):
            return True
        
        # Rule 2: Same transaction_block structure
        if (trans1.get('transaction_block') and trans2.get('transaction_block') and
            trans1.get('transaction_block') == trans2.get('transaction_block')):
            return True
        
        # Rule 3: Same merchant, amount, currency with dates within 7 days
        if (trans1.get('amount') == trans2.get('amount') and
            trans1.get('currency') == trans2.get('currency') and
            self._merchants_are_similar(trans1.get('merchant'), trans2.get('merchant')) and
            self._dates_are_similar(trans1.get('date'), trans2.get('date'), max_diff_days=7)):
            return True
        
        return False
    
    def _dates_are_similar(self, date1: str, date2: str, max_diff_days: int = 2) -> bool:
        """Check if two dates are within the specified number of days"""
        if not date1 or not date2:
            return False
        
        try:
            # Parse dates in DD-MM-YYYY format
            d1 = datetime.strptime(date1, '%d-%m-%Y')
            d2 = datetime.strptime(date2, '%d-%m-%Y')
            
            diff = abs((d1 - d2).days)
            return diff <= max_diff_days
        except ValueError:
            # If parsing fails, do string comparison
            return date1 == date2
    
    def _merchants_are_similar(self, merchant1: str, merchant2: str) -> bool:
        """Check if two merchant names are similar"""
        if not merchant1 or not merchant2:
            return False
        
        # Normalize merchant names
        m1 = self._normalize_merchant_name(merchant1)
        m2 = self._normalize_merchant_name(merchant2)
        
        # Exact match after normalization
        if m1 == m2:
            return True
        
        # Check if one is contained in the other
        if m1 in m2 or m2 in m1:
            return True
        
        return False
    
    def _normalize_merchant_name(self, merchant: str) -> str:
        """Normalize merchant name for comparison"""
        if not merchant:
            return ""
        
        # Convert to lowercase and remove common words
        merchant = merchant.lower()
        
        # Remove common location indicators
        remove_words = ['abu dhabi', 'ae', 'aed', 'center', 'store', 'shop', 'mart']
        for word in remove_words:
            merchant = merchant.replace(word, '')
        
        # Remove extra spaces
        merchant = ' '.join(merchant.split())
        
        return merchant.strip()
    
    def generate_deduplication_report(self, result: Dict[str, Any]) -> str:
        """Generate a human-readable deduplication report"""
        report = []
        report.append("=== TRANSACTION DEDUPLICATION REPORT ===")
        report.append(f"Original transactions: {result['original_count']}")
        report.append(f"Deduplicated transactions: {result['deduplicated_count']}")
        report.append(f"Duplicates removed: {result['duplicates_removed']}")
        report.append(f"Duplicate groups found: {len(result['duplicate_groups'])}")
        report.append("")
        
        for group in result['duplicate_groups']:
            report.append(f"Duplicate Group {group['group_id'] + 1}:")
            for i, trans in enumerate(group['transactions']):
                status = "KEPT" if i == 0 else "REMOVED"
                report.append(f"  [{status}] {trans.get('date', 'N/A')} - {trans.get('merchant', 'N/A')} - {trans.get('amount', 'N/A')} {trans.get('currency', 'N/A')}")
            report.append("")
        
        return "\n".join(report)


# Convenience function for direct usage
def deduplicate_transactions(transactions: List[Dict[str, Any]], 
                           similarity_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Convenience function to deduplicate transactions
    
    Args:
        transactions: List of transaction dictionaries
        similarity_threshold: Similarity threshold for fuzzy matching
        
    Returns:
        Dictionary with deduplicated transactions and metadata
    """
    deduplicator = TransactionDeduplicator(similarity_threshold)
    return deduplicator.deduplicate_transactions(transactions)