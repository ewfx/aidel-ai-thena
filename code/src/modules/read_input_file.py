import pandas as pd
import os
import re
import csv

# Function to parse the text data and extract transaction details
def parse_transaction_data(file_path):
    with open(file_path, 'r') as file:
        # Read the entire file as a string
        transaction_data = file.read()

    # Split the data by the delimiter '---' to get each transaction block
    transactions = transaction_data.split('---')

    # List to store parsed data
    parsed_transactions = []

    # Loop through each transaction block and extract details
    for transaction in transactions:
        # Strip leading/trailing whitespaces
        transaction = transaction.strip()

        if not transaction:
            continue

        # Extract TransactionID
        transaction_id = extract_value(transaction, "TransactionID:")

        # Extract Amount
        amount = extract_value(transaction, "Amount:")

        # Extract Transaction IP Address using a specific regex pattern
        ip_address = extract_ip_address(transaction)
        print(f"IP Address: {ip_address}")  # Debugging line to see the extracted IP address

        # Extract Payer Name (from Sender -> Name)
        payer_name = extract_value(transaction, "Sender:\n- Name:")

        # Extract Receiver Name
        receiver_name = extract_value(transaction, "Receiver:\n- Name:")

        # Extract Receiver Location
        # receiver_location = extract_value(transaction, "Receiver:\n- Location:")

        # Extract Notes
        notes = extract_value(transaction, "Notes:")

        # Append the extracted data into the list
        parsed_transactions.append([
            transaction_id, payer_name, receiver_name, notes, amount, ip_address
        ])

    return parsed_transactions

# Helper function to extract a specific field based on a label
def extract_value(transaction, label):
    # Find the position of the label in the transaction text
    start_index = transaction.find(label)
    
    if start_index == -1:
        return ''  # Return empty string if the label is not found

    # Extract the substring starting after the label
    start_index += len(label)
    
    # Find the next newline after the value
    end_index = transaction.find('\n', start_index)
    
    # Return the value, stripped of leading/trailing spaces
    return transaction[start_index:end_index].strip()

# Helper function to extract the IP address using regex
def extract_ip_address(transaction):
    # Use a regular expression to capture the IP address (format: xxx.xxx.xxx.xxx)
    ip_pattern = r"Transaction IP Address:\s*([\d\.]+)"
    match = re.search(ip_pattern, transaction)
    
    # Debugging output to see if IP address is being matched
    if match:
        return match.group(1)  # Return the IP address if found
    else:
        print("No IP address found in this transaction.")  # If not found, print a message
    return ''  # Return empty string if no IP address found

# Function to write data to CSV
def write_to_csv(parsed_data, output_file):
    # Prepare the CSV header
    header = ["TransactionID", "PayerName", "Receiver Name", "Transaction Notes", "Amount", "Transaction IP Address"]
    
    # Write data to CSV
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Write the header first
        writer.writerows(parsed_data)  # Write the data

    print(f"CSV file '{output_file}' created successfully.")

# Main function
def convert_txt_to_csv(input_txt, output_csv):
    # Parse the transaction data
    parsed_data = parse_transaction_data(input_txt)
    
    if not parsed_data:
        print("No data extracted from the input file.")
        return

    # Write structured data to CSV
    write_to_csv(parsed_data, output_csv)




def extract_input_file_details(file_name):
    file_extension = os.path.splitext(file_name)[1]
    if file_extension == ".csv":
        input_file = pd.read_csv(file_name)
        # Extract columns as separate Series
        return input_file['PayerName'], input_file['Receiver Name'], input_file['Transaction Notes']
    else:
        # Convert 'data.txt' to 'input.csv'
        convert_txt_to_csv(file_name, 'input.csv')
        input_file = pd.read_csv('input.csv')
        # Extract columns as separate Series
        return input_file['PayerName'], input_file['Receiver Name'], input_file['Transaction Notes']


        