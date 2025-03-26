# 🚀 AI-Driven Entity Intelligence Risk Analysis

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
Entity verification and risk assessment in financial transactions are critical but highly manual and error-prone. This project aims to develop a Generative AI/ML-powered system to automate the research and evidence-gathering process by:
 * Extracting and enriching entity names from transaction data.
 * Verifying and classifying entities using public data sources (e.g., WikiData, SEC EDGAR, OFAC Sanctions list).
 * Detecting fraudulent or high-risk entities through anomaly detection.
 * Assigning risk scores and providing supporting evidence to assist analysts.

The solution will improve efficiency, reduce manual effort, and enhance the accuracy of risk evaluation.

## 🎥 Demo 
📹 Demo video: https://drive.google.com/file/d/1qC-DzEj6brbcQiviQsYawH7Zp8Oa8tMR/view?usp=drive_link

🖼️ Screenshots:
![Architectural diagram](https://github.com/user-attachments/assets/478c4cad-4a1b-469c-ae8f-bec9c71e8b39)

![Home page](https://github.com/user-attachments/assets/4b6f737d-a5eb-4cbe-9c6a-5f27c0baa5ff)
![Output page](https://github.com/user-attachments/assets/c765d87d-ff33-4cf9-8dd4-376f43d4b249)
![Knowledge Graph](https://github.com/user-attachments/assets/f3ea2012-a0cc-4c8a-8062-9bcf0de69d09)
![Visualization of risk scores](https://github.com/user-attachments/assets/c2c09e32-0bbf-42d6-9695-69c3b68645ee)




## 💡 Inspiration
The inspiration for this project comes from the need to automate entity verification, reduce manual effort, and enhance risk assessment to combat rising financial fraud and meet growing regulatory compliance demands.

## ⚙️ What It Does
This project focuses on extracting entity information from transactions and assigning risk score.
* Extract entities from transactions, and collect all the details related to that entity. (Eg. If an entity is a company, we collect CEO, share holders, partners of the company)
* We extract these 3 types of risk from
 - Reputational risk of the entity by collecting the news articles 
 - Check if that entity is listed on OFAC Sanctions list
 - Calculate the number of filings done by the company
 - Calculate risk score from 4 models Ekata's transaction API, Plaids signal, Maxmind algorithm, Flagrights transaction monitoring algorithm
* We customized the risk formula, 0.3*sec_edgar_risk + 0.2*ofac_risk_score + 0.3*rep_risk_score +
  - cumulative_risk_score = (sec_edgar_score*0.3) + (0.3*max(rep_risk_party1,rep_risk_party2)) + (0.2 if (ofac_party1=="Yes" or ofac_party2=="Yes") else 0) + (0.4*plaid_score + 0.3*maxmind_score + 0.2*ekata_score + 0.1*flagright_score)

## 🛠️ How We Built It
We used python, NLP, Html, LLM models to get details and calculated risk score for entities.

## 🚧 Challenges We Faced
* Comprehending the Business Requirements related to the Problem Statement.
* Getting the right APIs for our technical requirements.
* Finding the most authentic Data Sources for the SEC EDGAR filings , OFAC Sanctions List and News Articles.
* Working on Prompt Engineering for the LLMs
* Tuning the LLM Model according to our requirements.

## 🏃 How to Run
1. Clone the repository  
   ```sh
   git clone https://github.com/ewfx/aidel-ai-thena.git
   ```
2. Install dependencies  
   ```sh
   pip install -r requirements.txt (for Python)
   ```
3. Run the project  
   ```sh
   python app.py
   ```

## 🏗️ Tech Stack
- 🔹 Frontend: Html
- 🔹 Backend: Python, Flask
- 🔹 Vader, Falcon-7b-Instruct, NLP, Knowledge Graph, pyspark, py2neo, SQL Alchemy
- 🔹 Other: WikiData, GDELT, SecEdgar, OFAC Sanctions list

## 👥 Team
- **Ramya R** - https://github.com/melodyramya | https://www.linkedin.com/in/ramya-r-3356a9256
- **Samiksha D. Tawde** - https://github.com/SamikshaDTawde-25) | http://www.linkedin.com/in/samiksha-tawde-b33051229)
- **Vedasree Anusha K. O.** - https://github.com/vedasree-anusha) | https://www.linkedin.com/in/vedasree-anusha-395245215/)
- **Soundharya Subramanian** - https://github.com/soundharya53) | http://www.linkedin.com/in/soundharya-s-b19661253)
