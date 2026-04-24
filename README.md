SF Snowflake Synthetic Data

A Python-based pipeline for generating and maintaining realistic synthetic data in a Salesforce sandbox.

This project is designed to continuously seed and update sandbox data — not just insert it once.


What This Does
Generates realistic Account and Contact data
Maintains stable identities using Synthetic_Id__c
Uses Salesforce upsert to:
create missing records
update existing records
Preserves relationships between records (Account → Contact)


Core Idea

Instead of inserting random data once, this project allows you to:

Re-run the script and safely update the same synthetic dataset over time.
This is enabled by a custom field:
Synthetic_Id__c (External ID, Unique)
This acts as a stable key so Salesforce can match records across runs.


📁 Project Structure
SF-Snowflake-Synthetic-Data/
│
├── data/                     # Output (debug/export)
│   └── accounts_raw.json
│
├── src/
│   ├── generators/          # Fake data generation
│   │   ├── base.py          # Shared utilities (faker, IDs, seed)
│   │   ├── accounts.py      # Account generator
│   │   └── contacts.py      # Contact generator
│   │
│   ├── loaders/             # Salesforce interaction
│   │   └── salesforce.py    # Login + upsert + queries
│   │
│   ├── config.py            # Project settings
│   ├── exporters.py         # Write data to disk
│   └── main.py              # Orchestrates the run
│
├── .env                     # Salesforce credentials (NOT committed)
├── requirements.txt
└── README.md




1. Salesforce Configuration

Create this field on objects you want to manage:

Account & Contact
Field	Type	Settings
Synthetic_Id__c	Text(50)	External ID + Unique


2. Environment Variables

Create a .env file in the project root:

SF_USERNAME=your.sandbox.username
SF_PASSWORD=yourpassword
SF_DOMAIN=test
SF_ORGANIZATION_ID=00Dxxxxxxxxxxxx


3. Install Dependencies
pip install -r requirements.txt
▶️ Running the Project
python -m src.main
🔁 What Happens When You Run It
Generates synthetic Accounts
Writes raw output to /data
Connects to Salesforce
Upserts Accounts using Synthetic_Id__c
Fetches Salesforce IDs for those Accounts


Example Generated Record
{
  "object": "Account",
  "synthetic_id": "ACC-000001",
  "fields": {
    "Synthetic_Id__c": "ACC-000001",
    "Name": "Smith Physical Therapy",
    "Phone": "(312) 555-1234"
  }
}