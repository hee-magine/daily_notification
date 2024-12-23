import requests

# Airtable configuration
BASE_ID = 'appVQixeY8ZIvhpRF'
TABLE_NAME = 'tblkkU88vQGr1MPoa'
AIRTABLE_API_KEY = ""

def get_record_by_member_and_date(member_name, date_string):
    # Construct the filter formula for multiple conditions
    filter_formula = f"AND({{팀원}}='{member_name}', {{Date String}}='{date_string}')"
    
    # Construct the URL with the filter
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}?filterByFormula={filter_formula}'
    
    # Set up headers with API key
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Make the request
    response = requests.get(url, headers=headers)
    
    # Check if request was successful
    if response.ok:
        data = response.json()
        records = data.get('records', [])
        return records
    else:
        print(f'Error: {response.status_code}')
        print(response.json())
        return None

# Example usage
if __name__ == "__main__":
    member_name = "강희산"
    date_string = "2024-11-18"
    
    records = get_record_by_member_and_date(member_name, date_string)
    
    if records:
        print(f"Found {len(records)} matching records:")
        for record in records:
            print("\nRecord ID:", record['id'])
            print("Fields:", record['fields'])
