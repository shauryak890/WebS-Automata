"""
Helper utilities for the LangChain AutoMailer application.
"""

import os
import json
import re
import csv
from typing import Dict, List, Any, Optional

def extract_emails_from_text(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to extract emails from
        
    Returns:
        List of extracted email addresses
    """
    # Standard email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    
    # Look for obfuscated emails (e.g., "email at domain dot com")
    obfuscated_pattern = r'[a-zA-Z0-9._%+-]+\s+(?:at|AT|@|&#64;|&#9090;)\s+[a-zA-Z0-9.-]+\s+(?:dot|DOT|\.)\s+(?:com|COM|org|ORG|net|NET|edu|EDU|gov|GOV|io|IO)'
    obfuscated_matches = re.findall(obfuscated_pattern, text)
    
    for match in obfuscated_matches:
        # Convert to standard email format
        email = match.replace(' at ', '@').replace(' AT ', '@').replace(' @ ', '@').replace('&#64;', '@').replace('&#9090;', '@')
        email = email.replace(' dot ', '.').replace(' DOT ', '.').replace(' . ', '.')
        email = email.replace(' ', '')
        if re.match(email_pattern, email):
            emails.append(email)
    
    # Look for emails with HTML entities
    html_pattern = r'[a-zA-Z0-9._%+-]+&#64;[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    html_matches = re.findall(html_pattern, text)
    
    for match in html_matches:
        email = match.replace('&#64;', '@')
        if re.match(email_pattern, email):
            emails.append(email)
    
    # Look for emails with "mailto:" prefix
    mailto_pattern = r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    mailto_matches = re.findall(mailto_pattern, text)
    emails.extend(mailto_matches)
    
    # Remove duplicates and return
    return list(set(emails))

def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Text to extract phone numbers from
        
    Returns:
        List of extracted phone numbers
    """
    # Common phone number patterns
    patterns = [
        r'\b\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b',  # (123) 456-7890, 123-456-7890, 123.456.7890
        r'\b\+\d{1,3}[-. ]?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b',  # +1 (123) 456-7890
        r'\b\d{3}[-. ]?\d{4}\b'  # 123-4567, 123.4567
    ]
    
    phone_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phone_numbers.extend(matches)
    
    # Clean up and standardize phone numbers
    cleaned_numbers = []
    for number in phone_numbers:
        # Remove non-numeric characters except for leading +
        cleaned = re.sub(r'[^0-9+]', '', number)
        if cleaned.startswith('+'):
            # International format
            if len(cleaned) >= 10:  # At least country code + number
                cleaned_numbers.append(cleaned)
        else:
            # US format
            if len(cleaned) == 10:  # Standard US number
                cleaned_numbers.append(cleaned)
            elif len(cleaned) == 11 and cleaned.startswith('1'):  # US with country code
                cleaned_numbers.append(cleaned)
            elif len(cleaned) >= 7:  # Partial number with area code
                cleaned_numbers.append(cleaned)
    
    # Remove duplicates
    return list(set(cleaned_numbers))

def extract_social_handles_from_text(text: str) -> List[str]:
    """
    Extract social media handles from text.
    
    Args:
        text: Text to extract social media handles from
        
    Returns:
        List of extracted social media handles
    """
    # Common social media handle patterns
    patterns = [
        r'@[a-zA-Z0-9_.]{1,30}\b',  # Twitter/Instagram style @username
        r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})\b',  # Twitter URLs
        r'instagram\.com/([a-zA-Z0-9_.]{1,30})\b',  # Instagram URLs
        r'facebook\.com/([a-zA-Z0-9.]{1,50})\b',  # Facebook URLs
        r'linkedin\.com/in/([a-zA-Z0-9_-]{1,50})\b',  # LinkedIn URLs
        r'youtube\.com/(?:user|channel)/([a-zA-Z0-9_-]{1,50})\b',  # YouTube URLs
        r'tiktok\.com/@([a-zA-Z0-9_.]{1,24})\b'  # TikTok URLs
    ]
    
    handles = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, str):  # Make sure match is a string
                if match.startswith('@'):
                    handles.append(match)
                else:
                    handles.append(f'@{match}')
    
    # Remove duplicates and filter out common false positives
    filtered_handles = []
    for handle in handles:
        # Skip handles that are likely not real
        if any(word in handle.lower() for word in ['@example', '@username', '@user', '@me', '@test']):
            continue
        # Skip very short handles (likely false positives)
        if len(handle) <= 3:
            continue
        filtered_handles.append(handle)
    
    return list(set(filtered_handles))

def save_json_data(data: Any, filepath: str, pretty: bool = True) -> None:
    """
    Save data as JSON to a file.
    
    Args:
        data: Data to save
        filepath: Path to save the file to
        pretty: Whether to format the JSON with indentation
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    # Save the data
    with open(filepath, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)

def export_leads_to_csv(leads: List[Dict], filepath: str) -> None:
    """
    Export lead data to a CSV file.
    
    Args:
        leads: List of lead dictionaries
        filepath: Path to save the CSV file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    # Determine all possible fields from all leads
    fieldnames = set()
    for lead in leads:
        fieldnames.update(lead.keys())
    
    # Sort fieldnames to ensure consistent order, but prioritize common fields
    priority_fields = ['title', 'name', 'business_name', 'email', 'link', 'source', 
                      'website', 'location', 'industry', 'keywords']
    
    # Sort the fieldnames with priority fields first
    sorted_fields = [field for field in priority_fields if field in fieldnames]
    sorted_fields.extend(sorted([field for field in fieldnames if field not in priority_fields]))
    
    # Write the data to CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted_fields)
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)

def load_json_data(filepath: str) -> Any:
    """
    Load JSON data from a file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_leads_from_csv(filepath: str) -> List[Dict]:
    """
    Load lead data from a CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of lead dictionaries
    """
    leads = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(dict(row))
    return leads

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing line endings.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    return text

def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the text
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Truncate and add ellipsis
    return text[:max_length-3] + '...'

def format_email(subject: str, body: str) -> str:
    """
    Format an email with subject and body.
    
    Args:
        subject: Email subject
        body: Email body
        
    Returns:
        Formatted email
    """
    return f"Subject: {subject}\n\n{body}" 