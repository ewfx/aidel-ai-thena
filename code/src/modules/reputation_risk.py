import spacy
import re
nlp = spacy.load("en_core_web_sm")
import csv
def normalize_name(name):
    """Removes all non-alphabetic characters except spaces and converts the name to lowercase."""
    return re.sub(r'[^a-zA-Z\s]', '', name.replace("\n", "")).lower()

def get_entity_details(company_name):
  entity_info=pd.read_csv("entity_info.csv")
  company_details=entity_info[entity_info["name"] == company_name]
  persons_involved_with_company = []

  ceo=company_details["ceo"].values[0]
  doc = nlp(ceo)
  persons_involved_with_company.extend([ent.text for ent in doc.ents if ent.label_ == "PERSON"])

  owners = company_details["owner"].values[0]
  doc = nlp(owners)
  persons_involved_with_company.extend([ent.text for ent in doc.ents if ent.label_ == "ORG" or ent.label_ == "PERSON"])

  founder = company_details["founder"].values[0]
  doc = nlp(founder)
  persons_involved_with_company.extend([ent.text for ent in doc.ents if ent.label_ == "PERSON"])

  persons_involved_with_company = list(set(persons_involved_with_company))

  # Remove duplicates while normalizing names
  unique_persons = set()
  for person in persons_involved_with_company:
      normalized_person = normalize_name(person)
      unique_persons.add(normalized_person)

  

  reputation_entities = unique_persons
  reputation_entities.add(company_name)
  return reputation_entities

from enum import unique
import os
import requests
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import time


# --------------------- SETUP ----------------------
nltk.download("vader_lexicon")
rep_risk_reasons = []
# --------------------- CONFIG ----------------------
fraud_keywords = {
    "fraud": 1.0,
    "scam": 1.0,
    "ponzi": 1.0,
    "embezzlement": 1.0,
    "misconduct": 0.8,
    "lawsuit": 0.3,
    "penalty": 0.5,
    "fine": 0.6,
    "criminal": 0.9
}

GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# --------------------- FUNCTION: FETCH ARTICLES ----------------------
def get_gdelt_articles(query, num_articles=20):
    """Fetches news articles from GDELT API for a given query."""
    params = {
        "query": query,
        "mode": "artlist",  # Return article list
        "format": "json",
        "maxrecords": num_articles,
        "timespan": "5Y"  # Fetch articles from past 5 years
    }

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(GDELT_API_URL, params=params, headers=headers)

        response.raise_for_status()
        data = response.json()

        articles = []
        if "articles" in data:
            for result in data["articles"]:
                title = result.get("title", "")
                url = result.get("url", "")
                content = result.get("seendate", "")  # Date of the article
                source = result.get("sourceurl", "")

                articles.append({
                    "Title": title,
                    "URL": url,
                    "Published_Date": content,
                    "Source": source
                })
        return articles
    except Exception as e:
        return []

# --------------------- FUNCTION: FRAUD DETECTION ----------------------
def detect_fraud_keywords(article_text):
    """Calculates fraud score based on keyword matches."""
    fraud_score = 0.0
    for keyword, weight in fraud_keywords.items():
        if keyword in article_text.lower():
            fraud_score += weight
    return fraud_score

# --------------------- FUNCTION: SENTIMENT ANALYSIS ----------------------
def analyze_sentiment(article_text):
    """Analyzes sentiment using VADER."""
    sia = SentimentIntensityAnalyzer()
    sentiment_score = sia.polarity_scores(article_text)["compound"]
    return "negative" if sentiment_score < -0.05 else "neutral/positive"

# --------------------- FUNCTION: PROCESS ARTICLES ----------------------
def analyze_articles(articles):
    rep_risk_reasons = []
    """Processes articles for fraud indicators and sentiment."""
    fraud_count = 0
    negative_sentiment_count = 0
    total_articles = len(articles)

    for article in articles:
        content = article["Title"]  # GDELT only provides title and URL
        fraud_score = detect_fraud_keywords(content)
        sentiment = analyze_sentiment(content)

        if fraud_score != 0:
          rep_risk_reasons.append(article["Title"])

        if fraud_score >= 1.0:
            fraud_count += 1

        if sentiment == "negative":
            negative_sentiment_count += 1

    fraud_percentage = (fraud_count / total_articles) * 100 if total_articles > 0 else 0
    
    fraud_risk_level = classify_fraud_risk(fraud_percentage)

    return fraud_count, negative_sentiment_count, fraud_percentage, fraud_risk_level

# --------------------- FUNCTION: CLASSIFY FRAUD RISK ----------------------
def classify_fraud_risk(fraud_percentage):
    """Classifies fraud risk level based on fraud percentage."""
    if fraud_percentage > 85:
        return "High"
    elif 50 <= fraud_percentage <= 85:
        return "Medium"
    elif 20 <= fraud_percentage < 50:
        return "Low"
    else:
        return "Minimal"

# --------------------- FUNCTION: SAVE RESULTS TO CSV ----------------------
def save_to_csv(articles, fraud_percentage, fraud_risk_level, entity_name):
    """Saves analyzed articles and results to CSV."""
    df = pd.DataFrame(articles)
    df["fraud_percentage"] = fraud_percentage
    df["fraud_risk_level"] = fraud_risk_level
    df["entity_name"] = entity_name
    df.to_csv(f"news/{entity_name}_news_articles.csv", index=False)

# --------------------- FUNCTION: PROCESS NAMES ----------------------
import time

def process_names(names_list):
    """Processes multiple names and checks for fraud-related articles."""
    all_results = []

    for name in names_list:

        # Add a delay to prevent hitting the rate limit
        time.sleep(5)  # Add a delay of 2 seconds before each API call

        articles = get_gdelt_articles(name, num_articles=20)

        if articles:
            fraud_count, negative_count, fraud_percentage, fraud_risk = analyze_articles(articles)
        else:
            fraud_percentage, fraud_count, negative_count, fraud_risk = 0, 0, 0, "Minimal"

        save_to_csv(articles, fraud_percentage, fraud_risk, name)

        # Append result to list
        all_results.append({
            "name": name,
            "fraud_percentage": fraud_percentage,
            "fraud_count": fraud_count,
            "negative_articles": negative_count,
            "fraud_risk_level": fraud_risk
        })

    # Save summary to CSV
    df_results = pd.DataFrame(all_results)
    df_results.to_csv("fraud_results_summary.csv", index=False)

# --------------------- MAIN EXECUTION ----------------------
# if __name__ == "__main__":
#     #names_list = ["Satya Nadella", "Bill Gates", "Google", "Microsoft", "Sundar Pichai"]
#     process_names(reputation_entities)

def fraud_detection(reputation_entities,company_name):
  cache_data = {}
  if os.path.exists('reputation_risk_summary.csv'):
    with open('reputation_risk_summary.csv', mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cache_data[row["name"]] = row
  if company_name in cache_data:
     print("Using cache data for reputational risk....")
  else:
    reputation_risk = []  
    process_names(reputation_entities)
    reputation_df = pd.read_csv("fraud_results_summary.csv")
    percentage_sum = 0
    for index, row in reputation_df.iterrows():
        if row['name'] == company_name:
            company_rep_risk = row['fraud_percentage']
        else:
            percentage_sum = percentage_sum + row['fraud_percentage']
  
    if percentage_sum == 0 and company_rep_risk == 0:
        reputation_risk_score = 0
    else:
        reputation_risk_score = (percentage_sum*20 + company_rep_risk*80)/(percentage_sum + company_rep_risk)

    print(reputation_risk_score/100)
    print(rep_risk_reasons)
    reputation_risk.append({
            "name": company_name,
            "reputation_risk_score": reputation_risk_score/100,
            "rep_risk_reason": rep_risk_reasons
        })
    df_results = pd.DataFrame(reputation_risk)

    # Check if file exists
    if os.path.exists('reputation_risk_summary.csv'):
        # Append without writing header if file exists
        df_results.to_csv('reputation_risk_summary.csv', mode="a", header=False, index=False)
    else:
        # Write with header if file does not exist
        df_results.to_csv('reputation_risk_summary.csv', mode="w", header=True, index=False)
  

