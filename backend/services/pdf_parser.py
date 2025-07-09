import fitz
import pikepdf
import pytesseract
from PIL import Image
import io
import re
import os
import tempfile
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import UploadFile, HTTPException
from models import Customer
import numpy as np

# Fix OpenSSL legacy provider issue
os.environ['OPENSSL_CONF'] = '/dev/null'

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

class PDFParser:
    def __init__(self):
        self.password_attempts = []
        self.setup_openssl_config()
    
    def setup_openssl_config(self):
        """Setup OpenSSL configuration to handle legacy encryption"""
        try:
            # Create a temporary OpenSSL config that enables legacy provider
            openssl_config = """
openssl_conf = openssl_init

[openssl_init]
providers = provider_sect

[provider_sect]
default = default_sect
legacy = legacy_sect

[default_sect]
activate = 1

[legacy_sect]
activate = 1
"""
            # Write config to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(openssl_config)
                self.openssl_config_path = f.name
            
            # Set environment variable to use our config
            os.environ['OPENSSL_CONF'] = self.openssl_config_path
            print(f"DEBUG - OpenSSL config set to: {self.openssl_config_path}")
        except Exception as e:
            print(f"WARNING - Could not setup OpenSSL config: {e}")
            # Fallback: disable OpenSSL config entirely
            os.environ['OPENSSL_CONF'] = '/dev/null'
    
    def extract_birth_year(self, dob: str) -> Optional[str]:
        """Extract birth year from various date formats"""
        if not dob:
            return None
        
        # Remove all non-digit characters
        dob_digits = re.sub(r'[^\d]', '', dob)
        
        if len(dob_digits) < 4:
            return None
        
        # Try different date formats
        formats_to_try = [
            '%Y-%m-%d',  # YYYY-MM-DD
            '%d-%m-%Y',  # DD-MM-YYYY
            '%m-%d-%Y',  # MM-DD-YYYY
            '%Y/%m/%d',  # YYYY/MM/DD
            '%d/%m/%Y',  # DD/MM/YYYY
            '%m/%d/%Y',  # MM/DD/YYYY
            '%Y%m%d',    # YYYYMMDD
            '%d%m%Y',    # DDMMYYYY
            '%m%d%Y',    # MMDDYYYY
        ]
        
        for fmt in formats_to_try:
            try:
                parsed_date = datetime.strptime(dob, fmt)
                return str(parsed_date.year)
            except ValueError:
                continue
        
        # Fallback: try to extract 4-digit year from the string
        # Look for 4 consecutive digits that could be a year (1900-2100)
        year_pattern = r'(19|20)\d{2}'
        year_match = re.search(year_pattern, dob_digits)
        if year_match:
            return year_match.group()
        
        # If all else fails, check if first 4 digits could be a year
        if len(dob_digits) >= 4:
            potential_year = dob_digits[:4]
            if 1900 <= int(potential_year) <= 2100:
                return potential_year
        
        # Check if last 4 digits could be a year
        if len(dob_digits) >= 4:
            potential_year = dob_digits[-4:]
            if 1900 <= int(potential_year) <= 2100:
                return potential_year
        
        return None
    
    def generate_password_candidates(self, customer: Customer) -> List[str]:
        """Generate password candidates with focus on birth year + phone format"""
        candidates = []
        name_parts = customer.name.lower().split()
        full_name = ''.join(name_parts)
        phone = re.sub(r'[^\d]', '', customer.phone_number)
        dob = customer.date_of_birth

        # Extract birth year properly
        birth_year = self.extract_birth_year(dob)

        # DEBUG: Print what we extracted
        print(f"DEBUG - Raw DOB: '{dob}'")
        print(f"DEBUG - Birth year extracted: '{birth_year}'")
        print(f"DEBUG - Raw phone: '{customer.phone_number}'")
        print(f"DEBUG - Phone digits: '{phone}'")
        print(f"DEBUG - Phone last 4: '{phone[-4:] if len(phone) >= 4 else 'N/A'}'")

        # PRIORITY: Add the specific format (birth year + last 4 phone digits) first
        if birth_year and len(phone) >= 4:
            primary_password = f"{birth_year}{phone[-4:]}"
            candidates.insert(0, primary_password)
            print(f"DEBUG - Primary password candidate: '{primary_password}'")
            
            # Add encoding variations for the primary password
            candidates.extend([
                primary_password,
                primary_password.encode('utf-8').decode('utf-8'),
                primary_password.encode('latin-1').decode('latin-1', errors='ignore'),
                str(primary_password).strip(),
            ])

        # Add variations of birth year + phone combinations
        if birth_year and len(phone) >= 4:
            candidates.extend([
                f"{birth_year}{phone[-4:]}",
                f"{birth_year[-2:]}{phone[-4:]}",  # 2-digit year + last 4 phone
                f"{birth_year}{phone[-6:]}",       # year + last 6 phone digits
                f"{birth_year}{phone[-8:]}",       # year + last 8 phone digits
            ])

        # Legacy date parsing for backward compatibility
        dob_digits = re.sub(r'[^\d]', '', dob)
        if len(dob_digits) >= 8:
            # Try different interpretations of date digits
            ddmm = dob_digits[6:8] + dob_digits[4:6]  # assuming YYYYMMDD
            ddmmyy = dob_digits[6:8] + dob_digits[4:6] + dob_digits[2:4]
            
            # Also try DD/MM/YYYY format
            if len(dob_digits) == 8:
                ddmm_alt = dob_digits[0:2] + dob_digits[2:4]  # assuming DDMMYYYY
                ddmmyy_alt = dob_digits[0:2] + dob_digits[2:4] + dob_digits[6:8]
                
                candidates.extend([
                    f"{birth_year}{ddmm_alt}" if birth_year else '',
                    f"{birth_year}{ddmmyy_alt}" if birth_year else '',
                ])

        # Name derived combinations
        if len(full_name) >= 4:
            first4 = full_name[:4]
            last4 = full_name[-4:]
            
            if len(dob_digits) >= 8:
                ddmm = dob_digits[6:8] + dob_digits[4:6] if len(dob_digits) >= 8 else ''
                ddmmyy = dob_digits[6:8] + dob_digits[4:6] + dob_digits[2:4] if len(dob_digits) >= 8 else ''
                
                candidates.extend([
                    f"{first4}{ddmmyy}",
                    f"{first4}{ddmm}",
                    f"{last4}{phone[-4:]}" if len(phone) >= 4 else '',
                    f"{first4.upper()}{ddmm}",
                    f"{first4.upper()}{ddmmyy}"
                ])

        # Card derived combinations
        for card in customer.credit_cards:
            if hasattr(card, 'card_number_last_four'):
                if len(dob_digits) >= 8:
                    ddmm = dob_digits[6:8] + dob_digits[4:6]
                    candidates.append(f"{card.card_number_last_four}{ddmm}")

        # Date format variations
        dob_formats = [
            dob.replace('-', ''),
            dob.replace('/', ''),
            dob.replace('.', ''),
        ]
        
        # Add 2-digit year versions
        for fmt in dob_formats:
            if len(fmt) >= 2:
                candidates.extend([
                    fmt,
                    fmt[-2:],  # last 2 digits
                    fmt[-4:],  # last 4 digits
                ])

        # Name variations
        for name_part in name_parts:
            if name_part:
                candidates.extend([
                    name_part,
                    name_part.capitalize(),
                    name_part.upper(),
                ])

        # Phone variations
        if len(phone) >= 4:
            candidates.extend([
                phone,
                phone[-4:],
                phone[-6:] if len(phone) >= 6 else '',
                phone[-8:] if len(phone) >= 8 else '',
            ])

        # Name + date combinations
        for name_part in name_parts:
            if name_part:
                for dob_format in dob_formats:
                    if dob_format:
                        candidates.extend([
                            f"{name_part}{dob_format}",
                            f"{name_part.capitalize()}{dob_format}",
                            f"{dob_format}{name_part}",
                            f"{name_part}{dob_format[-4:]}" if len(dob_format) >= 4 else '',
                            f"{name_part}{dob_format[-2:]}" if len(dob_format) >= 2 else '',
                        ])

        # Name + phone combinations
        for name_part in name_parts:
            if name_part and len(phone) >= 4:
                candidates.extend([
                    f"{name_part}{phone[-4:]}",
                    f"{name_part.capitalize()}{phone[-4:]}",
                    f"{phone[-4:]}{name_part}",
                ])

        # Additional birth year combinations
        if birth_year:
            candidates.extend([
                birth_year,
                birth_year[-2:],  # 2-digit year
            ])
            
            # Birth year + name combinations
            for name_part in name_parts:
                if name_part:
                    candidates.extend([
                        f"{birth_year}{name_part}",
                        f"{name_part}{birth_year}",
                        f"{birth_year[-2:]}{name_part}",
                        f"{name_part}{birth_year[-2:]}",
                    ])

        # Remove empty strings and duplicates while preserving order
        candidates = [c for c in candidates if c and c.strip()]
        candidates = list(dict.fromkeys(candidates))  # Remove duplicates while preserving order

        print(f"DEBUG - Generated {len(candidates)} total candidates")
        print(f"DEBUG - First 10 candidates: {candidates[:10]}")

        return candidates
    
    def try_password_protected_pdf(self, pdf_bytes: bytes, customer: Customer) -> Optional[str]:
        password_candidates = self.generate_password_candidates(customer)
        
        print(f"DEBUG - Attempting to unlock PDF with {len(password_candidates)} password candidates")
        
        for i, password in enumerate(password_candidates):
            print(f"DEBUG - Trying password {i+1}/{len(password_candidates)}: '{password}'")
            
            # Method 1: Try with pikepdf
            try:
                with pikepdf.open(io.BytesIO(pdf_bytes), password=password) as pdf:
                    text_content = ""
                    for page in pdf.pages:
                        page_text = str(page)
                        text_content += page_text + "\n"
                    
                    if text_content.strip():
                        print(f"SUCCESS - PDF unlocked with pikepdf using password: '{password}'")
                        return text_content
            except pikepdf.PasswordError:
                continue
            except Exception as e:
                print(f"WARNING - pikepdf failed with password '{password}': {str(e)}")
                
                # Method 2: Try with PyMuPDF as fallback
                try:
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    if doc.needs_pass:
                        auth_result = doc.authenticate(password)
                        if auth_result:
                            text_content = ""
                            for page_num in range(len(doc)):
                                page = doc[page_num]
                                text_content += page.get_text() + "\n"
                            doc.close()
                            
                            if text_content.strip():
                                print(f"SUCCESS - PDF unlocked with PyMuPDF using password: '{password}'")
                                return text_content
                        doc.close()
                except Exception as pymupdf_error:
                    print(f"WARNING - PyMuPDF also failed with password '{password}': {str(pymupdf_error)}")
                    continue
        
        print("DEBUG - All password attempts failed")
        return None
    
    def extract_text_with_pymupdf(self, pdf_bytes: bytes) -> str:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Try multiple text extraction methods
                page_text = page.get_text()
                
                # If no text found, try extracting text blocks
                if not page_text.strip():
                    text_blocks = page.get_text("blocks")
                    for block in text_blocks:
                        if len(block) > 4:  # Block contains text
                            page_text += block[4] + "\n"
                
                # If still no text, try extracting text with layout preserved
                if not page_text.strip():
                    page_text = page.get_text("dict")
                    if isinstance(page_text, dict) and "blocks" in page_text:
                        for block in page_text["blocks"]:
                            if "lines" in block:
                                for line in block["lines"]:
                                    if "spans" in line:
                                        for span in line["spans"]:
                                            if "text" in span:
                                                page_text += span["text"] + " "
                                        page_text += "\n"
                
                text_content += str(page_text) + "\n"
            
            doc.close()
            return text_content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_with_ocr(self, pdf_bytes: bytes) -> str:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Increase resolution for better OCR results
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                img = Image.open(io.BytesIO(img_data))
                
                # Try different OCR configurations
                ocr_configs = [
                    '--psm 6',  # Uniform block of text
                    '--psm 4',  # Single column of text
                    '--psm 3',  # Fully automatic page segmentation
                    '--psm 11', # Sparse text
                    '--psm 12'  # Sparse text with OSD
                ]
                
                page_text = ""
                for config in ocr_configs:
                    try:
                        ocr_text = pytesseract.image_to_string(img, config=config)
                        if ocr_text.strip() and len(ocr_text.strip()) > len(page_text.strip()):
                            page_text = ocr_text
                    except:
                        continue
                
                if not page_text.strip() and CV2_AVAILABLE:
                    # Try with image preprocessing
                    try:
                        # Convert PIL image to OpenCV format
                        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        
                        # Apply preprocessing
                        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                        
                        # Convert back to PIL
                        processed_img = Image.fromarray(thresh)
                        
                        try:
                            page_text = pytesseract.image_to_string(processed_img, config='--psm 6')
                        except:
                            pass
                    except Exception:
                        # OpenCV processing failed, skip preprocessing
                        pass
                
                text_content += page_text + "\n"
            
            doc.close()
            return text_content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to perform OCR on PDF: {str(e)}")
    
    async def parse_pdf(self, file: UploadFile, customer: Customer) -> Dict:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        content = await file.read()
        
        try:
            # First try normal text extraction
            text_content = self.extract_text_with_pymupdf(content)
            
            # If we got some text, process it
            if text_content.strip():
                return self.process_extracted_text(text_content)
            
            # If no text found, try OCR
            text_content = self.extract_text_with_ocr(content)
            if text_content.strip():
                return self.process_extracted_text(text_content)
            
            # If still no text, file might be password protected
            raise Exception("No text could be extracted")
        
        except Exception as e:
            # Try password-protected PDF extraction
            password_content = self.try_password_protected_pdf(content, customer)
            
            if password_content:
                return self.process_extracted_text(password_content)
            
            # Last resort: try OCR again with different settings
            try:
                text_content = self.extract_text_with_ocr(content)
                if text_content.strip():
                    return self.process_extracted_text(text_content)
            except Exception as ocr_error:
                pass
                
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to parse PDF. Could not extract text or decrypt: {str(e)}"
            )
    
    def extract_detailed_transactions(self, text: str) -> List[dict]:
        """Extract detailed transaction information with AED/DHS amounts"""
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
                
                # Look for AED/DHS amounts in this block
                full_block = ' '.join(transaction_block)
                aed_pattern = r'(?:AED|DHS)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
                amount_pattern = r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:AED|DHS)'
                
                amount_matches = re.findall(aed_pattern, full_block, re.IGNORECASE)
                if not amount_matches:
                    amount_matches = re.findall(amount_pattern, full_block, re.IGNORECASE)
                
                if amount_matches:
                    # Extract merchant name (look for text between dates and amounts)
                    merchant_pattern = r'\d{2}-\d{2}-\d{4}\s+([A-Z][A-Z0-9\s&\-\.]{3,40})\s+'
                    merchant_match = re.search(merchant_pattern, full_block)
                    merchant = merchant_match.group(1).strip() if merchant_match else "Unknown Merchant"
                    
                    # Extract transaction date
                    date_match = re.search(date_pattern, line)
                    transaction_date = date_match.group(1) if date_match else None
                    
                    for amount_str in amount_matches:
                        try:
                            amount = float(amount_str.replace(',', ''))
                            transactions.append({
                                'date': transaction_date,
                                'merchant': merchant,
                                'amount': amount,
                                'currency': 'AED',
                                'raw_text': full_block,
                                'transaction_block': transaction_block
                            })
                        except ValueError:
                            continue
        
        return transactions
    
    def extract_summary_amounts(self, text: str) -> dict:
        """Extract key summary amounts from the statement"""
        summary = {}
        
        # Key patterns to look for
        patterns = {
            'current_balance': r'Current Balance.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            'minimum_payment': r'Minimum Payment Due.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            'total_payment': r'Total Payment Due.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            'previous_balance': r'Previous Balance.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            'credit_limit': r'(?:Total\s+)?Credit Limit.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            'available_credit': r'Available Credit Limit.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            'statement_date': r'Statement Date.*?(\d{2}-\d{2}-\d{4})',
            'due_date': r'Payment Due Date.*?(\d{2}-\d{2}-\d{4})'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1)
                if key in ['statement_date', 'due_date']:
                    summary[key] = value
                else:
                    try:
                        summary[key] = float(value.replace(',', ''))
                    except ValueError:
                        summary[key] = value
        
        return summary
    
    def extract_aed_dhs_amounts(self, text: str) -> List[dict]:
        """Extract all AED/DHS amounts from the text"""
        amounts = []
        
        # Patterns for AED/DHS amounts
        patterns = [
            r'AED\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'DHS\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*AED',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*DHS', 
            r'(?:AED|DHS)[\s:]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:AED|DHS)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1)
                try:
                    amount = float(amount_str.replace(',', ''))
                    amounts.append({
                        'amount': amount,
                        'currency': 'AED',
                        'raw_match': match.group(0),
                        'context': text[max(0, match.start()-50):match.end()+50]
                    })
                except ValueError:
                    continue
        
        # Remove duplicates
        unique_amounts = []
        seen = set()
        for amount_info in amounts:
            key = (amount_info['amount'], amount_info['currency'])
            if key not in seen:
                seen.add(key)
                unique_amounts.append(amount_info)
        
        return unique_amounts
    
    def format_currency(self, amount: float) -> str:
        """Format currency amount for display"""
        return f"AED {amount:,.2f}"
    
    def clean_extracted_text(self, text: str) -> str:
        if not text:
            return ""
            
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Remove very short lines that are likely artifacts
            if line and len(line) > 2:
                # Remove lines that are just special characters or numbers
                if not re.match(r'^[\W\d]+$', line):
                    cleaned_lines.append(line)
                elif re.search(r'\d+[/\-]\d+[/\-]\d+', line) or re.search(r'\$\d+', line) or re.search(r'AED|DHS', line, re.IGNORECASE):
                    # Keep lines with dates or amounts
                    cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Additional cleaning
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize whitespace
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)  # Remove multiple newlines
        
        return cleaned_text
    
    def process_extracted_text(self, text: str) -> Dict:
        """Process extracted text and return structured data"""
        cleaned_text = self.clean_extracted_text(text)
        
        # Extract detailed information
        transactions = self.extract_detailed_transactions(text)
        summary = self.extract_summary_amounts(text)
        amounts = self.extract_aed_dhs_amounts(text)
        
        # Count total transactions
        total_transaction_amount = sum(t['amount'] for t in transactions)
        
        return {
            'raw_text': text,
            'cleaned_text': cleaned_text,
            'transactions': transactions,
            'summary': summary,
            'aed_amounts': amounts,
            'statistics': {
                'total_transactions': len(transactions),
                'total_amount': total_transaction_amount,
                'unique_amounts_found': len(amounts),
                'currency': 'AED'
            },
            'extraction_success': True
        }


# Test function to verify password generation
def test_password_generation():
    """Test the password generation with your example"""
    class MockCustomer:
        def __init__(self):
            self.name = "John Doe"
            self.phone_number = "050 123 4567"
            self.date_of_birth = "15/03/1980"  # DD/MM/YYYY format
            self.credit_cards = []
    
    parser = PDFParser()
    customer = MockCustomer()
    candidates = parser.generate_password_candidates(customer)
    
    print("\n" + "="*50)
    print("PASSWORD GENERATION TEST")
    print("="*50)
    print(f"Customer Name: {customer.name}")
    print(f"Phone Number: {customer.phone_number}")
    print(f"Date of Birth: {customer.date_of_birth}")
    print(f"Generated {len(candidates)} candidates:")
    
    for i, candidate in enumerate(candidates[:20]):  # Show first 20
        print(f"{i+1:2d}. {candidate}")
    
    if len(candidates) > 20:
        print(f"... and {len(candidates) - 20} more candidates")
    
    # Check if the expected password is in the list
    expected = "19804567"
    if expected in candidates:
        print(f"\n✅ Expected password '{expected}' found at position {candidates.index(expected) + 1}")
    else:
        print(f"\n❌ Expected password '{expected}' NOT found")
    
    print("="*50)


# Run the test if this file is executed directly
if __name__ == "__main__":
    test_password_generation()