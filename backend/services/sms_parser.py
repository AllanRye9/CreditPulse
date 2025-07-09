import re
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import dateparser

class SMSParser:
    def __init__(self):
        self.date_patterns = [
            r'due\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'due\s+(?:date|by):?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'pay\s+by\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
            r'(\d{1,2})\s*(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'due\s+(\d{1,2})(st|nd|rd|th)',
            r'(\d{1,2})(st|nd|rd|th)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
        ]
        
        self.amount_patterns = [
            r'(?:total|amount|balance|outstanding)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:aed|dhs|dirham)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:aed|dhs|dirham)',
            r'minimum\s+(?:payment|amount|due)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'remaining\s+(?:balance|amount)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:pay|payment)\s+(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        self.remaining_amount_patterns = [
            r'remaining\s+(?:balance|amount|due)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'outstanding\s+(?:balance|amount|due)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'current\s+(?:balance|due)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'balance\s+(?:due|remaining)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        self.total_amount_patterns = [
            r'total\s+(?:amount|due|balance)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'statement\s+(?:amount|balance)\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'total\s+outstanding\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'credit\s+card\s+bill\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        self.payment_patterns = [
            r'payment\s+(?:of|received)\s+(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'paid\s+(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'payment\s+successful\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'payment\s+confirmed\s*[:\-]?\s*(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'auto\s+pay\s+(?:aed|dhs|dirham)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        self.payment_status_patterns = [
            r'payment\s+(?:successful|confirmed|received|processed)',
            r'paid\s+successfully',
            r'payment\s+complete',
            r'auto\s+pay\s+successful',
            r'payment\s+debited',
            r'payment\s+failed',
            r'payment\s+declined',
            r'insufficient\s+funds',
        ]
        
        self.bank_patterns = [
            r'(emirates\s+nbd|enbd|adcb|abu\s+dhabi\s+commercial\s+bank|fab|first\s+abu\s+dhabi\s+bank)',
            r'(mashreq|cbd|commercial\s+bank\s+of\s+dubai|noor\s+bank|ajman\s+bank|rak\s+bank)',
            r'(hsbc|citi|standard\s+chartered|american\s+express|amex)',
            r'(chase|wells\s+fargo|bank\s+of\s+america|capital\s+one|discover)',
        ]
        
        self.card_patterns = [
            r'card\s+ending\s+(?:in\s+)?(\d{4})',
            r'card\s+\*+(\d{4})',
            r'\*+(\d{4})',
            r'xxxx\s*(\d{4})',
        ]

    def parse_sms(self, sms_text: str) -> Dict:
        sms_text = sms_text.strip()
        sms_lower = sms_text.lower()
        
        parsed_data = {
            'raw_text': sms_text,
            'due_date': None,
            'total_amount': None,
            'remaining_amount': None,
            'payment_amount': None,
            'payment_status': None,
            'card_last_four': None,
            'bank_name': None,
            'sms_type': self._classify_sms_type(sms_lower),
            'extracted_amounts': [],
            'extracted_dates': [],
            'confidence_score': 0.0
        }
        
        parsed_data['due_date'] = self._extract_due_date(sms_text)
        parsed_data['total_amount'] = self._extract_total_amount(sms_text)
        parsed_data['remaining_amount'] = self._extract_remaining_amount(sms_text)
        parsed_data['payment_amount'] = self._extract_payment_amount(sms_text)
        parsed_data['payment_status'] = self._extract_payment_status(sms_lower)
        parsed_data['card_last_four'] = self._extract_card_number(sms_text)
        parsed_data['bank_name'] = self._extract_bank_name(sms_lower)
        parsed_data['extracted_amounts'] = self._extract_all_amounts(sms_text)
        parsed_data['extracted_dates'] = self._extract_all_dates(sms_text)
        parsed_data['confidence_score'] = self._calculate_confidence_score(parsed_data)
        
        return parsed_data

    def _classify_sms_type(self, sms_text: str) -> str:
        if any(word in sms_text for word in ['due', 'payment due', 'bill due', 'minimum payment']):
            return 'payment_due'
        elif any(word in sms_text for word in ['payment successful', 'payment confirmed', 'paid', 'payment received']):
            return 'payment_confirmation'
        elif any(word in sms_text for word in ['statement', 'bill generated', 'monthly statement']):
            return 'statement_generated'
        elif any(word in sms_text for word in ['transaction', 'purchase', 'spent']):
            return 'transaction_alert'
        elif any(word in sms_text for word in ['balance', 'outstanding', 'current balance']):
            return 'balance_inquiry'
        else:
            return 'unknown'

    def _extract_due_date(self, sms_text: str) -> Optional[datetime]:
        for pattern in self.date_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                
                parsed_date = dateparser.parse(match)
                if parsed_date:
                    if parsed_date.year < datetime.now().year:
                        parsed_date = parsed_date.replace(year=datetime.now().year)
                    return parsed_date
        
        due_patterns = [
            r'due\s+(?:on\s+)?(\d{1,2})',
            r'pay\s+by\s+(\d{1,2})',
            r'due\s+(\d{1,2})(st|nd|rd|th)?'
        ]
        
        for pattern in due_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    day = int(match[0])
                else:
                    day = int(match)
                
                if 1 <= day <= 31:
                    today = datetime.now()
                    try:
                        due_date = today.replace(day=day)
                        if due_date < today:
                            if today.month == 12:
                                due_date = due_date.replace(year=today.year + 1, month=1)
                            else:
                                due_date = due_date.replace(month=today.month + 1)
                        return due_date
                    except ValueError:
                        continue
        
        return None

    def _extract_total_amount(self, sms_text: str) -> Optional[float]:
        for pattern in self.total_amount_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    return amount
                except ValueError:
                    continue
        return None

    def _extract_remaining_amount(self, sms_text: str) -> Optional[float]:
        for pattern in self.remaining_amount_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    return amount
                except ValueError:
                    continue
        return None

    def _extract_payment_amount(self, sms_text: str) -> Optional[float]:
        for pattern in self.payment_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    return amount
                except ValueError:
                    continue
        return None

    def _extract_payment_status(self, sms_text: str) -> Optional[str]:
        for pattern in self.payment_status_patterns:
            if re.search(pattern, sms_text, re.IGNORECASE):
                if 'successful' in pattern or 'confirmed' in pattern or 'received' in pattern or 'complete' in pattern or 'debited' in pattern:
                    return 'successful'
                elif 'failed' in pattern or 'declined' in pattern or 'insufficient' in pattern:
                    return 'failed'
        return None

    def _extract_card_number(self, sms_text: str) -> Optional[str]:
        for pattern in self.card_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            if matches:
                return matches[0]
        return None

    def _extract_bank_name(self, sms_text: str) -> Optional[str]:
        for pattern in self.bank_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            if matches:
                return matches[0].upper()
        return None

    def _extract_all_amounts(self, sms_text: str) -> List[float]:
        amounts = []
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    amounts.append(amount)
                except ValueError:
                    continue
        return list(set(amounts))

    def _extract_all_dates(self, sms_text: str) -> List[datetime]:
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, sms_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                
                parsed_date = dateparser.parse(match)
                if parsed_date:
                    dates.append(parsed_date)
        return dates

    def _calculate_confidence_score(self, parsed_data: Dict) -> float:
        score = 0.0
        
        if parsed_data['due_date']:
            score += 0.3
        if parsed_data['total_amount'] or parsed_data['remaining_amount']:
            score += 0.3
        if parsed_data['payment_amount']:
            score += 0.2
        if parsed_data['payment_status']:
            score += 0.1
        if parsed_data['card_last_four']:
            score += 0.05
        if parsed_data['bank_name']:
            score += 0.05
        
        return min(score, 1.0)

    def parse_multiple_sms(self, sms_list: List[str]) -> List[Dict]:
        results = []
        for sms in sms_list:
            parsed = self.parse_sms(sms)
            results.append(parsed)
        return results

    def get_payment_summary(self, parsed_data: Dict) -> Dict:
        summary = {
            'has_due_date': parsed_data['due_date'] is not None,
            'has_amount_info': parsed_data['total_amount'] is not None or parsed_data['remaining_amount'] is not None,
            'has_payment_info': parsed_data['payment_amount'] is not None or parsed_data['payment_status'] is not None,
            'days_until_due': None,
            'amount_type': None
        }
        
        if parsed_data['due_date']:
            days_until_due = (parsed_data['due_date'] - datetime.now()).days
            summary['days_until_due'] = days_until_due
        
        if parsed_data['total_amount']:
            summary['amount_type'] = 'total'
        elif parsed_data['remaining_amount']:
            summary['amount_type'] = 'remaining'
        elif parsed_data['payment_amount']:
            summary['amount_type'] = 'payment'
        
        return summary