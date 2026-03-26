import pandas as pd
import re


INPUT_FILE = "study_eu_programs.csv"
OUTPUT_FILE = "study_eu_programs_cleaned.csv"


def clean_text(x):
    if pd.isna(x):
        return pd.NA
    x = str(x).replace("\xa0", " ").strip()
    x = re.sub(r"\s+", " ", x)
    if x == "" or x.lower() in ["n/a", "na", "none", "null"]:
        return pd.NA
    return x


def extract_tuition_number(x):
    if pd.isna(x):
        return pd.NA

    x = str(x)
    match = re.search(r"([\d,]+(?:\.\d+)?)", x)
    if not match:
        return pd.NA

    number_str = match.group(1).replace(",", "")
    try:
        number = float(number_str)
        if number.is_integer():
            return int(number)
        return number
    except:
        return pd.NA


def extract_duration_years(x):
    if pd.isna(x):
        return pd.NA

    x = str(x).lower().strip()

    if "year" not in x and "month" not in x:
        return pd.NA

    year_match = re.search(r"(\d+(?:\.\d+)?)\s*years?", x)
    if year_match:
        val = float(year_match.group(1))
        if val.is_integer():
            return int(val)
        return val

    month_match = re.search(r"(\d+(?:\.\d+)?)\s*months?", x)
    if month_match:
        months = float(month_match.group(1))
        years = round(months / 12, 2)
        if years.is_integer():
            return int(years)
        return years

    return pd.NA


def main():
    df = pd.read_csv(INPUT_FILE)

    for col in df.columns:
        df[col] = df[col].apply(clean_text)

    df = df.drop_duplicates()

    df["global_ranking"] = "N/A"
    df["tuition_fee_usd_total"] = df["tuition_fee_usd_total"].apply(extract_tuition_number)
    df["program_duration_year"] = df["program_duration"].apply(extract_duration_years)
    df = df.drop(columns=["program_duration"])

    df = df[
        [
            "university_name",
            "program_name",
            "degree",
            "tuition_fee_usd_total",
            "program_duration_year",
            "global_ranking",
            "university_location",
            "url",
        ]
    ]

    df = df.dropna(subset=["university_name", "program_name", "url"])

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")



if __name__ == "__main__":
    main()