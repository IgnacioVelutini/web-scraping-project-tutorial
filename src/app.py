import subprocess
import sys

# Function to install a package using python3
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required packages
required_packages = ['pandas', 'requests', 'beautifulsoup4', 'matplotlib']

# Install packages if they are not already installed
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install_package(package)

# Now, proceed with the rest of the imports
import pandas as pd
import requests
from bs4 import BeautifulSoup
import sqlite3
import matplotlib.pyplot as plt

# Step 2: Download HTML
def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Check for request errors
    return response.text


# Step 3: Transform HTML
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Locate all tables
    tables = soup.find_all('table')
    
    # Identify the correct table for quarterly revenue data, usually the first one
    data_table = tables[0] if tables else None
    rows = []

    # Parse each row in the table
    if data_table:
        for row in data_table.find_all('tr')[1:]:  # Skip header row
            cols = [col.text.strip() for col in row.find_all('td')]
            if cols:  # Avoid empty rows
                rows.append(cols)
    
    # Create DataFrame from parsed rows
    df = pd.DataFrame(rows, columns=['Date', 'Revenue'])
    return df

# Step 4: Process DataFrame
def clean_data(df):
    # Remove $ and commas
    df['Revenue'] = df['Revenue'].replace(r'[\$,]', '', regex=True)
    
    # Convert 'B' (billions) and 'M' (millions) suffixes to floats
    def convert_revenue(value):
        if 'B' in value:
            return float(value.replace('B', '')) * 1e9  # Convert billions
        elif 'M' in value:
            return float(value.replace('M', '')) * 1e6  # Convert millions
        return float(value)  # Already a plain number
    
    df['Revenue'] = df['Revenue'].apply(convert_revenue)
    
    # Drop any rows with NaN values if present
    df.dropna(inplace=True)
    return df


# Step 5: Store data in SQLite
def store_data_in_db(df, db_name='tesla_revenues.db'):
    # Connect to SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS revenues (
        Date TEXT PRIMARY KEY,
        Revenue REAL
    )''')
    
    # Insert data into the table
    df.to_sql('revenues', conn, if_exists='replace', index=False)
    # Commit changes and close connection
    conn.commit()
    conn.close()

# Step 6: Visualize the data
def plot_data(df):
    plt.figure(figsize=(10, 6))

    # Plot 1: Time Series of Quarterly Revenues
    plt.plot(pd.to_datetime(df['Date']), df['Revenue'], marker='o')
    plt.title('Tesla Quarterly Revenues Over Time')
    plt.xlabel('Date')
    plt.ylabel('Revenue (in billions)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Plot 2: Revenue Distribution
    plt.hist(df['Revenue'], bins=10)
    plt.title('Revenue Distribution')
    plt.xlabel('Revenue')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.show()

    # Plot 3: Percentage Change in Revenue
    df['Revenue Change (%)'] = df['Revenue'].pct_change() * 100
    plt.plot(pd.to_datetime(df['Date']), df['Revenue Change (%)'], marker='o', color='red')
    plt.title('Quarter-over-Quarter Revenue Change (%)')
    plt.xlabel('Date')
    plt.ylabel('Revenue Change (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    url = 'https://ycharts.com/companies/TSLA/revenues'
    html = fetch_html(url)
    df = parse_html(html)
    df = clean_data(df)
    store_data_in_db(df)
    plot_data(df)

if __name__ == '__main__':
    main()
