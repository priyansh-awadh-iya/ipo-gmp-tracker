import re
import logging

logger = logging.getLogger(__name__)

def normalize_name(name):
    """
    Normalizes company names for fuzzy/token match:
    - Lowercase
    - Removes parenthesis content (e.g. (India), (SME))
    - Removes common business suffixes (Ltd, Limited, Pvt, Co, Company, IPO, REIT)
    - Strips non-alphanumeric chars and normalizes spacing
    """
    if not name:
        return ""
    name = name.lower()
    
    # Remove text in parentheses
    name = re.sub(r'\(.*?\)', '', name)
    
    # List of suffixes to strip
    suffixes = [
        r'\bltd\b', r'\blimited\b', r'\bpvt\b', r'\bprivate\b',
        r'\bco\b', r'\bcompany\b', r'\bcorp\b', r'\bcorporation\b',
        r'\bipo\b', r'\breit\b', r'\bindia\b', r'\bindian\b', r'\bllp\b'
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name)
        
    # Strip special characters and punctuation
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # Normalize spaces
    name = " ".join(name.split())
    return name

def is_match(name1, name2):
    """
    Checks if normalized company names match.
    Returns True if names are identical or if one is a strong substring of another.
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    
    if not n1 or not n2:
        return False
        
    # Exact match of normalized strings
    if n1 == n2:
        return True
        
    # Token-based match (e.g. "Advit Jewels" vs "Advit Jewels Enterprises")
    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    
    # If they share at least 2 words, or all words of the shorter name
    common = tokens1.intersection(tokens2)
    shorter_len = min(len(tokens1), len(tokens2))
    
    if shorter_len > 0 and len(common) >= shorter_len:
        return True
        
    # Substring check for multi-word matches
    if len(n1) > 4 and len(n2) > 4:
        if n1 in n2 or n2 in n1:
            return True
            
    return False

def consolidate_data(chittorgarh_list, ipowatch_list, investorgain_list):
    """
    Consolidates data across three sources.
    Matches companies, calculates consensus averages and expected listing gain percentages.
    
    Returns a list of dicts: [
        {
            'company': str (display name),
            'chittorgarh_gmp': float or None,
            'ipowatch_gmp': float or None,
            'investorgain_gmp': float or None,
            'consensus_gmp': float,
            'cutoff_price': float,
            'listing_gain_pct': float
        }
    ]
    """
    consolidated = {}

    def add_to_consolidated(record, source_name):
        comp_name = record['company']
        gmp = record['gmp']
        price = record['price']
        close_date = record.get('close_date', 'N/A')

        # Check if company already matched in consolidated
        matched_key = None
        for key in consolidated.keys():
            if is_match(key, comp_name):
                matched_key = key
                break

        if matched_key:
            # Update existing record
            consolidated[matched_key][f'{source_name}_gmp'] = gmp
            if price > 0:
                consolidated[matched_key]['prices'].append(price)
            # Choose a non-N/A close date if current is N/A
            if close_date and close_date != 'N/A' and (not consolidated[matched_key]['close_date'] or consolidated[matched_key]['close_date'] == 'N/A'):
                consolidated[matched_key]['close_date'] = close_date
            # Retain the longer/more detailed company name for display
            if len(comp_name) > len(consolidated[matched_key]['company']):
                consolidated[matched_key]['company'] = comp_name
        else:
            # Create new record
            normalized_key = normalize_name(comp_name)
            consolidated[normalized_key] = {
                'company': comp_name,
                'chittorgarh_gmp': None,
                'ipowatch_gmp': None,
                'investorgain_gmp': None,
                'prices': [price] if price > 0 else [],
                'close_date': close_date
            }
            consolidated[normalized_key][f'{source_name}_gmp'] = gmp

    # Load records from all sources
    for rec in chittorgarh_list:
        add_to_consolidated(rec, 'chittorgarh')
    for rec in ipowatch_list:
        add_to_consolidated(rec, 'ipowatch')
    for rec in investorgain_list:
        add_to_consolidated(rec, 'investorgain')

    results = []
    for key, data in consolidated.items():
        # Get active GMP entries
        gmp_values = []
        for src in ['chittorgarh', 'ipowatch', 'investorgain']:
            val = data[f'{src}_gmp']
            if val is not None:
                gmp_values.append(val)

        if not gmp_values:
            continue

        # Calculate Consensus Average GMP
        consensus_gmp = sum(gmp_values) / len(gmp_values)

        # Consensus Cut-off Price: prefer the maximum non-zero official price reported
        cutoff_price = max(data['prices']) if data['prices'] else 0.0

        # Calculate Listing Gain Percentage
        if cutoff_price > 0:
            listing_gain_pct = (consensus_gmp / cutoff_price) * 100
        else:
            listing_gain_pct = 0.0

        results.append({
            'company': data['company'],
            'chittorgarh_gmp': data['chittorgarh_gmp'],
            'ipowatch_gmp': data['ipowatch_gmp'],
            'investorgain_gmp': data['investorgain_gmp'],
            'consensus_gmp': round(consensus_gmp, 2),
            'cutoff_price': round(cutoff_price, 2),
            'listing_gain_pct': round(listing_gain_pct, 2),
            'close_date': data.get('close_date', 'N/A')
        })

    return results
