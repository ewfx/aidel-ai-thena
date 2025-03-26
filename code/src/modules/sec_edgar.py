from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def load_data_to_df(file_name):
    file_path = f'/content/{file_name}.txt'

    # Read the file and skip the first two lines (header and separator)
    with open(file_path, 'r') as f:
        lines = f.readlines()[2:]

    # Save cleaned data to a temporary file
    cleaned_path = f'/content/cleaned_{file_name}.txt'
    with open(cleaned_path, 'w') as f:
        f.writelines(lines)

    # Read the cleaned file into a PySpark DataFrame
    df = spark.read.csv(cleaned_path, sep='|', header=False)

    # Rename and select required columns
    df = df.withColumnRenamed("_c0", "CIK") \
        .withColumnRenamed("_c1", "Company Name") \
        .withColumnRenamed("_c2", "Form Type") \
        .withColumnRenamed("_c3", "Date Filed") \
        .select("CIK", "Company Name", "Form Type", "Date Filed")

    # Dynamically name the dataframe using globals()
    globals()[f"df_{file_name}"] = df
    print(f"DataFrame for {file_name} created with {df.count()} rows.")
    df.show(5, truncate=False)

def compute_sec_edgar_score(company_name, establishment_year, penalty=5, max_filings_per_year=20616):
    # Determine which years to check
    start_year = max(establishment_year, 2021)
    years_to_check = range(start_year, 2026)
    total_years = len(years_to_check)

    total_score = 0
    has_filings = False

    print(f"Computing SEC EDGAR Score for {company_name} (Established in {establishment_year})\n")

    for year in years_to_check:
        df = globals().get(f"df_{year}")
        if df is not None:
            result = df.filter(F.col("Company Name") == company_name) \
                       .agg(F.count("*").alias("Occurrences")) \
                       .collect()

            occurrences = result[0]['Occurrences'] if result else 0

            if occurrences > 0:
                print(f"Year: {year} | Occurrences: {occurrences}")
                has_filings = True
            else:
                print(f"Year: {year} - No Filings Found")

            # Apply penalty if no filings are found
            no_filing_penalty = penalty if occurrences == 0 else 0

            # Calculate score
            total_score += occurrences - no_filing_penalty
        else:
            print(f"Year: {year} - DataFrame Not Found")

    # Ensure the score is non-negative and normalized
    if has_filings:
        sec_edgar_score = max(0, total_score / (total_years * max_filings_per_year))
    else:
        sec_edgar_score = 0

    print(f"\nFinal SEC EDGAR Score for {company_name}: {sec_edgar_score:.4f}")




# Function to get unique form types for a company across multiple dataframes
def get_unique_form_types(company_name, dataframes, years):
    results = []
    
    for df, year in zip(dataframes, years):
        result = df.filter(F.col("Company Name") == company_name) \
                   .agg(F.collect_set("Form Type").alias("Unique Form Types")) \
                   .collect()
        
        if result and result[0]['Unique Form Types']:
            unique_forms = ', '.join(sorted(result[0]['Unique Form Types']))
            results.append(f"Year {year}: {unique_forms}")
        else:
            results.append(f"Year {year}: No records found for company: {company_name}")

    return "\n".join(results)

# Example usage
dataframes = [df_2021, df_2022, df_2023, df_2024, df_2025]
years = [2021, 2022, 2023, 2024, 2025]
print(get_unique_form_types("NICHOLAS FINANCIAL INC", dataframes, years))
