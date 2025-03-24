import requests
from bs4 import BeautifulSoup
#from serpapi import GoogleSearch
from googleapiclient.discovery import build
import time
import hashlib
import csv
import os
import json
import pandas as pd

# --------------------- API CONFIG ----------------------
HF_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HF_SUMMARY_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_TOKEN = "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"  # Replace with your Hugging Face API key
SERP_API_KEY = "0e171bb73853d57fa90599a725208b89c8fbfd6af245ba07ee196c4753473ba8"  # Replace with your SerpAPI key
GOOGLE_CSE_API_KEY = "AIzaSyACPO6pPXknFegMmZUCv7TF61C9nBOi5o4"  # Replace with your Google CSE API key
GOOGLE_CSE_ID = "7362fd7218df54a28"  # Replace with your Custom Search Engine ID

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --------------------- CACHING ----------------------
CACHE_FILE = "entity_info.csv"
CACHE_HEADERS = ["name", "type", "ceo", "owner", "headquarters", "net_worth", "founder","date_of_establishment","Sanction","Reason"]

# Read existing cache into a dictionary
cache_data = {}

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cache_data[row["name"]] = row

def save_to_csv(data):
    """Save data to CSV file."""
    file_exists = os.path.exists(CACHE_FILE)

    with open(CACHE_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CACHE_HEADERS)

        # Write header only if file does not exist
        if not file_exists:
            writer.writeheader()

        # Add data to CSV
        writer.writerow(data)

# --------------------- FUNCTION: Query HF API ----------------------
def query_hf_api(prompt, url=HF_API_URL, max_retries=3):
    """Query Hugging Face API with retry logic."""
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.7}}

    for i in range(max_retries):
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"].strip()

        elif response.status_code in [503, 504]:
            print(f"⚠️ API temporarily unavailable. Retrying in 5 seconds... (Attempt {i+1}/{max_retries})")
            time.sleep(5)
        else:
            return f"Error: {response.json()}"

    return "Failed after multiple retries."

# --------------------- FUNCTION: Scrape Wikipedia ----------------------
def scrape_wikipedia(company_name):
    """Scrape Wikipedia to get company information."""
    search_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
    cache_key = hashlib.sha256(search_url.encode()).hexdigest()

    try:
        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract infobox or paragraphs
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            rows = infobox.find_all("tr")
            data = {}
            for row in rows:
                header = row.find("th")
                value = row.find("td")
                if header and value:
                    data[header.get_text(strip=True)] = value.get_text(strip=True)
            return data

        # Fallback to paragraphs if no infobox
        paragraphs = soup.find_all("p")
        text_data = " ".join([para.get_text() for para in paragraphs[:3]])

        if len(text_data) > 50:
            return {"Summary": text_data}
    except Exception as e:
        print(f"Error while scraping: {e}")
        return None
    return None

# --------------------- FUNCTION: Summarize Content ----------------------
def summarize_content(content, max_length=130):
    """Summarizes the content using Hugging Face API."""
    payload = {"inputs": content[:2000], "parameters": {"max_length": max_length, "min_length": 50}}
    response = requests.post(HF_SUMMARY_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and len(result) > 0 and "summary_text" in result[0]:
            return result[0]["summary_text"].strip()

    return content[:max_length]  # Return trimmed content if summarization fails


# --------------------- FUNCTION: Google Search via API ----------------------
def google_cse_search(company_name):
    """Use Google Custom Search Engine API to get relevant link."""
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_CSE_API_KEY)
        result = service.cse().list(q=company_name, cx=GOOGLE_CSE_ID, num=1).execute()

        if "items" in result and len(result["items"]) > 0:
            first_link = result["items"][0]["link"]

            response = requests.get(first_link, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all("p")
            data = " ".join([para.get_text() for para in paragraphs[:3]])
            return {"Summary": summarize_content(data)}
    except Exception:
        return None
    return None

# --------------------- FUNCTION: Get Company Info ----------------------
def get_company_info(company_name, question):
    """Retrieve company information using Wikipedia and Google API."""

    # Scrape Wikipedia First
    wikipedia_info = scrape_wikipedia(company_name)
    if wikipedia_info:
        result = query_hf_api(f"Based on this information:\n{wikipedia_info}\nAnswer: {question}")
    else:
      # Fallback to Google CSE if Wikipedia Fails
      google_data = google_cse_search(company_name)
      if google_data:
        result = query_hf_api(f"Based on this information:\n{google_data}\nAnswer: {question}")
      else:
        # Fallback to Basic Query if Google CSE Fails
        result = query_hf_api(f"Provide an accurate answer about {company_name}.\nQuestion: {question}\nAnswer:")

    # Extract only the answer by splitting on 'Answer:'
    if "Answer:" in result:
        answer = result.split("Answer:")[-1].strip()
    else:
        answer = result.strip()

    # Clean unnecessary question-like patterns from the response
    # Handle cases like "Amazon is an e-commerce company..." or similar patterns
    if "?" in answer or question.lower() in answer.lower():
        parts = answer.split("?")
        if len(parts) > 1:
            answer = parts[1].strip()

    return answer


# --------------------- EXAMPLE USAGE ----------------------
def entity_extraction(entity_name):
  company_name = entity_name
  questions = [
    "What is the classification or type of the company?",    # type
    "Who is the CEO of the company?",  # ceo
    "What are the names of current majority share holders of the company?",
    "Where is the headquarters of the company?",  # headquarters
    "What is the net worth of the company?",  # net_worth
    "Who is the founder of the company?",  # founder,
    "When was the company established?",
    "Is this company listed on the OFAC sanctions list or subject to any U.S. government sanction?",
    "Why is this company present in OFAC sanctions list?"
  ]
  # Check if the company info is already cached
  if company_name in cache_data:
      print("Using cached data...")
      company_info = cache_data[company_name]
  else:
      print("Fetching new data...")
      company_info = {"name": company_name}

      for i, q in enumerate(questions):
          result = get_company_info(company_name, q)
          # Extract only the final answer
          if "Answer:" in result:
              answer = result.split("Answer:")[-1].strip()
          else:
              answer = result

        # Map answers to respective columns
          if i == 0:
              company_info["type"] = answer
          elif i == 1:
              company_info["ceo"] = answer
          elif i ==2:
              company_info["owner"] = answer
          elif i == 3:
              company_info["headquarters"] = answer
          elif i == 4:
              company_info["net_worth"] = answer
          elif i == 5:
              company_info["founder"] = answer
          elif i == 6:
              company_info["date_of_establishment"] = answer
          elif i == 7:
             company_info["Sanction"] = answer
          elif i == 8:
            if "Yes" in company_info["Sanction"]:
              company_info["Reason"] = answer
            else:
              company_info["Reason"] = " "

    # Save to CSV and update cache
      save_to_csv(company_info)
      cache_data[company_name] = company_info

# Print the results
#   for key, value in company_info.items():
#       print(f"{key.capitalize()}: {value}")
