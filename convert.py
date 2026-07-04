import pandas as pd
import json
import sys

def convert_sheet_to_json():
    # TODO: Replace the string below with your actual Google Sheet ID
    SHEET_ID = '11ASeuLBTAHOq5dMGSYjGNNFNQTankQmvyK7_DL4rOFI'
    
    # Target URL to download the sheet directly as a CSV asset
    csv_url = f'https://docs.google.com/spreadsheets/d/11ASeuLBTAHOq5dMGSYjGNNFNQTankQmvyK7_DL4rOFI/export?format=csv'
    
    try:
        # Load data directly from the live CSV export endpoint
        df = pd.read_csv(csv_url)
        
        # Replace NaN/Empty cells with empty strings cleanly
        df = df.fillna('')
        
        # Convert DataFrame to list of records (JSON format)
        result = df.to_dict(orient='records')
        
        # Write output as a clean, structured JSON file
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print("Successfully generated data.json from Google Sheets.")
    except Exception as e:
        print(f"Error processing sheet data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    convert_sheet_to_json()
