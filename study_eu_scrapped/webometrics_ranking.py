import pandas as pd
import requests
import re
import time
import unicodedata
from bs4 import BeautifulSoup
from difflib import get_close_matches


INPUT_FILE = "study_eu_programs_cleaned.csv"
OUTPUT_FILE = "study_eu_programs_with_ranking.csv"

BASE_URL = "https://www.webometrics.org/europe"
MAX_PAGES = 55


def normalize_name(name):
    if pd.isna(name):
        return ""

    name = str(name).strip().lower()

    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))

    name = name.replace("&", " and ")
    name = re.sub(r"[^\w\s]", " ", name)

    replacements = {
        "univ ": "university ",
        "univ.": "university",
        "universitat": "university",
        "universite": "university",
        "universidade": "university",
        "universita": "university",
        "technische universitat": "technical university",
        "universitatet": "university",
        "universiteit": "university",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    name = re.sub(r"\s+", " ", name).strip()
    return name


def get_soup(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_rows_from_page(soup):
    rows = []

    table_rows = soup.select("table tr")

    for tr in table_rows:
        cells = tr.find_all("td")
        if len(cells) < 3:
            continue

        row_text = clean_text(tr.get_text(" ", strip=True))

        match = re.match(r"^\s*(\d+)\s+(\d+)\s+", row_text)
        if not match:
            continue

        world_rank = int(match.group(2))

        a = tr.find("a", href=True)
        if not a:
            continue

        university_name = clean_text(a.get_text(" ", strip=True))
        if not university_name:
            continue

        rows.append({
            "webometrics_world_rank": world_rank,
            "webometrics_university_name_normalized": normalize_name(university_name),
        })

    if not rows:
        return pd.DataFrame(columns=[
            "webometrics_world_rank",
            "webometrics_university_name_normalized",
        ])

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["webometrics_university_name_normalized"], keep="first")
    return df


def scrape_webometrics_europe():
    all_parts = []

    for page in range(MAX_PAGES + 1):
        url = f"{BASE_URL}?page={page}"
        print(f"Scraping: {url}")

        try:
            soup = get_soup(url)
            part = extract_rows_from_page(soup)
            print(f"  Found {len(part)} universities")

            if not part.empty:
                all_parts.append(part)

            time.sleep(1)

        except Exception as e:
            print(f"  Error on page {page}: {e}")

    if not all_parts:
        raise ValueError("Could not scrape any Europe ranking rows from Webometrics.")

    df = pd.concat(all_parts, ignore_index=True)
    df = df.drop_duplicates(subset=["webometrics_university_name_normalized"], keep="first")
    df = df.sort_values("webometrics_world_rank").reset_index(drop=True)

    return df


def build_lookup(rank_df):
    lookup = {}
    for _, row in rank_df.iterrows():
        lookup[row["webometrics_university_name_normalized"]] = row["webometrics_world_rank"]
    return lookup


def match_university(university_name, lookup, normalized_names):
    norm = normalize_name(university_name)

    if norm in lookup:
        return lookup[norm]

    matches = get_close_matches(norm, normalized_names, n=1, cutoff=0.90)
    if matches:
        return lookup[matches[0]]

    for candidate in normalized_names:
        if norm in candidate or candidate in norm:
            return lookup[candidate]

    return "N/A"


def main():
    df = pd.read_csv(INPUT_FILE)

    rank_df = scrape_webometrics_europe()

    lookup = build_lookup(rank_df)
    normalized_names = list(lookup.keys())

    unique_unis = (
        df["university_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )


    uni_to_rank = {}
    for i, uni in enumerate(unique_unis, start=1):
        uni_to_rank[uni] = match_university(uni, lookup, normalized_names)


    df["global_ranking"] = df["university_name"].map(uni_to_rank).fillna("N/A")

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

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()