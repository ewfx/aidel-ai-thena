import spacy
import re
nlp = spacy.load("en_core_web_sm")
import csv
def normalize_name(name):
    """Removes all non-alphabetic characters except spaces and converts the name to lowercase."""
    return re.sub(r'[^a-zA-Z\s]', '', name.replace("\n", "").replace(".", "")).lower()

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
  reputation_entities.add(normalize_name(company_name))
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
def analyze_articles(articles,name):
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
          rep_risk_reasons.append(name + " - " + article["Title"])

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
    if fraud_percentage > 50:
        return "High"
    elif 30 <= fraud_percentage <= 50:
        return "Medium"
    elif 20 <= fraud_percentage < 30:
        return "Low"
    else:
        return "Minimal"

# --------------------- FUNCTION: SAVE RESULTS TO CSV ----------------------
def save_to_csv(articles, fraud_percentage, fraud_risk_level, entity_name, company_name):
    """Saves analyzed articles and results to CSV."""
    article = []
    article.append({
            "Name": entity_name,
            "Title": articles,
            "Fraud Percentage": fraud_percentage,
            "Fraud Risk Level": fraud_risk_level
        })
    df = pd.DataFrame(article)
    if os.path.exists(f"news/{company_name}/{entity_name}_news_articles.csv"):
        # Append without writing header if file exists
        df.to_csv(f"news/{company_name}/{entity_name}_news_articles.csv", mode="a", header=False, index=False)
    else:
        if not os.path.exists(f"news/{company_name}"):
            os.makedirs(f"news/{company_name}")
        # Write with header if file does not exist
        df.to_csv(f"news/{company_name}/{entity_name}_news_articles.csv", mode="w", header=True, index=False)
    #df.to_csv(f"news/{entity_name}_news_articles.csv", index=False)

# --------------------- FUNCTION: PROCESS NAMES ----------------------
import time

def classify_article(article,name):
    fraud_count = 0 
    negative_sentiment_count = 0 
    fraud_percentage = 0
    fraud_risk = 0
    content = article["Title"]  # GDELT only provides title and URL
    fraud_score = detect_fraud_keywords(content)
    sentiment = analyze_sentiment(content)

    if fraud_score >= 0.5:
            fraud_count += 1
    
    if sentiment == "negative":
            negative_sentiment_count += 1

    fraud_percentage = fraud_count * 100
    fraud_risk = classify_fraud_risk(fraud_percentage)

    return fraud_count, negative_sentiment_count, fraud_percentage, fraud_risk 

def process_names(names_list,company_name):
    """Processes multiple names and checks for fraud-related articles."""
    all_results = []
    rep_risk_reasons = set()
    entity_fraud_percent = 0
    entity_fraud_risk = ""
    for name in names_list:
        rep_risk_reasons = set() 
        entity_fraud_percent = 0
        entity_fraud_risk = ""
        if os.path.exists(f"news/{company_name}/{name}_news_articles.csv") == False:
            # Add a delay to prevent hitting the rate limit
            time.sleep(5)  # Add a delay of 2 seconds before each API call
            high_risk = 0
            low_risk = 0
            medium_risk = 0

            articles = get_gdelt_articles(name, num_articles=20)

            if articles:
                for article in articles:                                   
                    fraud_count, negative_count, fraud_percentage, fraud_risk = classify_article(article,name)
                    if fraud_risk != "Minimal":
                        rep_risk_reasons.add(name + " - " + article["Title"])
                    if fraud_risk == "High":
                        high_risk = high_risk+1
                    elif fraud_risk == "Medium":
                        medium_risk = medium_risk + 1
                    elif fraud_risk == "Low":
                        low_risk = low_risk + 1
                    save_to_csv(article["Title"], fraud_percentage, fraud_risk, name, company_name)
            else:
                fraud_percentage, fraud_count, negative_count, fraud_risk = 0, 0, 0, "Minimal"
                save_to_csv(articles, fraud_percentage, fraud_risk, name,company_name)
            #risk calculation
            if high_risk+medium_risk+low_risk != 0:
                entity_fraud_percent = ((high_risk*70 + medium_risk*20 + low_risk*10)/(high_risk+medium_risk+low_risk))
            print(name,entity_fraud_percent,high_risk)
            entity_fraud_risk = classify_fraud_risk(entity_fraud_percent)

            if not any(result["name"] == name for result in all_results):
                all_results.append({
                "name": name,
                "fraud_percentage": entity_fraud_percent,
                "fraud_risk": entity_fraud_risk,
                "Rep_risk_reason": list(rep_risk_reasons)  # Convert set to list
                })


            
        else:
            rep_risk_reasons = set()
            #"File already exists"
            if os.path.exists(f"news/{company_name}/{name}_news_articles.csv"):
                with open(f"news/{company_name}/{name}_news_articles.csv", mode="r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:  
                        #print(row)                      
                        name = row["Name"]
                        title = row["Title"]
                        fraud_percentage = row["Fraud Percentage"]
                        fruad_risk_level = row["Fraud Risk Level"]
                        if fruad_risk_level != "Minimal":
                            rep_risk_reasons.add(name + " - " + title)
                        if not any(result["name"] == name for result in all_results):
                            all_results.append({
                            "name": name,
                            "fraud_percentage": entity_fraud_percent,
                            "fraud_risk": entity_fraud_risk,
                            "Rep_risk_reason": list(rep_risk_reasons)  # Convert set to list
                        })




        # Append result to list
        

    # Save summary to CSV
    df_results = pd.DataFrame(all_results)
    df_results.to_csv(f"news/{company_name}_fraud_results_summary.csv", index=False)



# --------------------- MAIN EXECUTION ----------------------
# if __name__ == "__main__":
#     #names_list = ["Satya Nadella", "Bill Gates", "Google", "Microsoft", "Sundar Pichai"]
#     process_names(reputation_entities)

def fraud_detection(reputation_entities,company_name):
  company_rep_risk = 0
  percentage_sum = 0
  cache_data = {}
  if os.path.exists('reputation_risk_summary.csv'):
    with open('reputation_risk_summary.csv', mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cache_data[row["name"]] = row
  if company_name in cache_data:
     print("Using cache data for reputational risk....")
  else:
    print("Finding new data ....")
    reputation_risk = []  
    if os.path.exists(f"news/{company_name}_fraud_results_summary.csv") == False:
        process_names(reputation_entities,company_name)
    reputation_df = pd.read_csv(f"news/{company_name}_fraud_results_summary.csv")
    percentage_sum = 0
    for index, row in reputation_df.iterrows():
        if row['name'] == normalize_name(company_name):
            company_rep_risk = company_rep_risk + row['fraud_percentage']
        else:
            percentage_sum = percentage_sum + row['fraud_percentage']
    print(company_rep_risk)
    print(percentage_sum)
  
    if percentage_sum == 0 and company_rep_risk == 0:
        reputation_risk_score = 0
    else:
        reputation_risk_score = ((percentage_sum/100)*20 + (company_rep_risk/100)*80)/100

    # print(reputation_risk_score/100)
    # print(rep_risk_reasons)
    reputation_risk.append({
            "name": company_name,
            "reputation_risk_score": reputation_risk_score,
            "rep_risk_reason": reputation_df["Rep_risk_reason"].to_list()
        })
    df_results = pd.DataFrame(reputation_risk)

    # Check if file exists
    if os.path.exists('reputation_risk_summary.csv'):
        # Append without writing header if file exists
        df_results.to_csv('reputation_risk_summary.csv', mode="a", header=False, index=False)
    else:
        # Write with header if file does not exist
        df_results.to_csv('reputation_risk_summary.csv', mode="w", header=True, index=False)
  

