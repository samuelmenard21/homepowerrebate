#!/usr/bin/env python3
import csv
import time
from google.oauth2.service_account import Credentials
import gspread

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_file('google-credentials.json', scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open('HomePowerRebate-Installers')
worksheet = sheet.sheet1

print("Importing from complete-installers.csv...")
installers = []
with open('complete-installers.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        installers.append([
            row.get('City', ''),
            row.get('Business Name', ''),
            row.get('Address', ''),
            row.get('Phone', ''),
            row.get('Website', ''),
            row.get('Google Rating', ''),
            row.get('Review Count', ''),
            row.get('Google Maps URL', ''),
            row.get('HomePowerRebate Recommended', 'No'),
            row.get('Notes', ''),
            row.get('Last Updated', ''),
        ])

print("Clearing existing data...")
worksheet.delete_rows(2, worksheet.row_count)
time.sleep(2)

chunk_size = 20
for i in range(0, len(installers), chunk_size):
    chunk = installers[i:i+chunk_size]
    print(f"Inserting rows {i+1}-{min(i+chunk_size, len(installers))}...")
    worksheet.append_rows(chunk)
    time.sleep(2)

print(f"✓ Imported {len(installers)} installers")
