import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


SEARCH_URL = "https://www.study.eu/search"


class StudyEUScraper:
    def __init__(self):
        self.driver = self.create_driver()
        self.wait = WebDriverWait(self.driver, 15)
        self.rows = []
        self.seen_urls = set()

    def create_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1400,1000")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=en-US")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
        return webdriver.Chrome(options=options)

    def restart_driver(self, current_url, region="noneea", accept_cookies=False):
        try:
            self.driver.quit()
        except:
            pass

        self.driver = self.create_driver()
        self.wait = WebDriverWait(self.driver, 15)

        self.driver.get(current_url)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        if accept_cookies:
            self.accept_cookies()

        self.apply_filters(region=region)
        time.sleep(3)

    def accept_cookies(self):
        try:
            btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='OK']"))
            )
            btn.click()
            time.sleep(1)
        except:
            pass

    def clean_text(self, text):
        if not text:
            return "N/A"
        return " ".join(text.replace("\xa0", " ").split())

    def apply_filters(self, region="noneea"):
        try:
            currency_select = Select(
                self.wait.until(EC.presence_of_element_located((By.ID, "select-currency")))
            )
            currency_select.select_by_value("USD")
            time.sleep(1)
        except:
            pass

        try:
            term_select = Select(
                self.wait.until(EC.presence_of_element_located((By.ID, "select-tuition-term")))
            )
            term_select.select_by_value("total")
            time.sleep(1)
        except:
            pass

        try:
            region_select = Select(
                self.wait.until(EC.presence_of_element_located((By.ID, "select-tuition-region")))
            )
            region_select.select_by_value(region)
            time.sleep(1)
        except:
            pass

    def get_result_cards(self):
        cards = self.driver.find_elements(By.CSS_SELECTOR, "li.featured-search-result")
        if cards:
            return cards
        return self.driver.find_elements(By.CSS_SELECTOR, "#search-results li")

    def wait_for_cards(self, timeout=20):
        end_time = time.time() + timeout
        while time.time() < end_time:
            cards = self.get_result_cards()
            if cards:
                return cards
            time.sleep(1)
        return []

    def extract_card_data(self, card):
        program_name = "N/A"
        degree = "N/A"
        university_name = "N/A"
        location = "N/A"
        duration = "N/A"
        tuition = "N/A"
        url = "N/A"

        try:
            link = card.find_element(By.CSS_SELECTOR, 'a[href^="/university/"]')
            href = link.get_attribute("href")
            if href:
                url = href
        except:
            pass

        try:
            program_name = self.clean_text(
                card.find_element(By.CSS_SELECTOR, ".panel-heading .col-md-10 strong").text
            )
        except:
            pass

        try:
            degree = self.clean_text(
                card.find_element(By.CSS_SELECTOR, ".search-degree-type").text
            )
        except:
            pass

        try:
            info_block = card.find_element(By.CSS_SELECTOR, ".panel-body .col-md-7").text
            lines = [
                self.clean_text(line)
                for line in info_block.split("\n")
                if self.clean_text(line) != "N/A"
            ]

            if len(lines) >= 1:
                university_name = lines[0]
            if len(lines) >= 2:
                location = lines[1]
        except:
            pass

        try:
            extra_info = card.find_elements(By.CSS_SELECTOR, ".search-result-additional-info")

            if len(extra_info) >= 1:
                first_text = self.clean_text(extra_info[0].text)

                if "mode" in first_text.lower():
                    duration = "N/A"
                else:
                    duration = first_text

            if len(extra_info) >= 2:
                tuition = self.clean_text(extra_info[1].text)
        except:
            pass

        return {
            "university_name": university_name,
            "program_name": program_name,
            "degree": degree,
            "tuition_fee_usd_total": tuition,
            "program_duration": duration,
            "global_ranking": "N/A",
            "university_location": location,
            "url": url
        }

    def save_data(self):
        df = pd.DataFrame(self.rows)
        df.to_csv("study_eu_programs.csv", index=False, encoding="utf-8-sig")

    def get_next_page_url(self):
        try:
            next_link = self.driver.find_element(By.CSS_SELECTOR, 'li.next a[rel="next"]')
            href = next_link.get_attribute("href")
            if href:
                return href
        except:
            pass
        return None

    def scrape(self, region="noneea"):
        try:
            current_url = SEARCH_URL
            page_num = 1

            while current_url:
                self.driver.get(current_url)
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)

                if page_num == 1:
                    self.accept_cookies()

                self.apply_filters(region=region)
                time.sleep(3)

                cards = self.wait_for_cards(timeout=20)

                print(f"Page {page_num}: found {len(cards)} cards")

                added_this_page = 0

                for card in cards:
                    row = self.extract_card_data(card)

                    if row["url"] != "N/A" and row["url"] not in self.seen_urls:
                        self.rows.append(row)
                        self.seen_urls.add(row["url"])
                        added_this_page += 1

                print(f"Added {added_this_page} new rows")
                self.save_data()

                next_url = self.get_next_page_url()

                if not next_url:
                    break

                if next_url == current_url:
                    break

                if page_num % 50 == 0:
                    current_url = next_url
                    page_num += 1
                    self.restart_driver(current_url, region=region, accept_cookies=False)
                    continue

                current_url = next_url
                page_num += 1


        finally:
            self.driver.quit()


if __name__ == "__main__":
    scraper = StudyEUScraper()
    scraper.scrape(region="noneea")