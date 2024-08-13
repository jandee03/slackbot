import os
import glob
import csv
import pandas as pd
import os
import yaml
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException


class SlackScrapeMembers:
    def __init__(self, service, chrome_options, url):
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.url = f"{url}/people"
        self.csv_path = csv_path

        self.css_selector = By.CSS_SELECTOR
        self.xpath = By.XPATH

        self.clickable_element = EC.element_to_be_clickable
        self.check_visibility = EC.visibility_of_element_located

        self.member_names = []

    def web_driver_wait(
            self, 
            css, 
            timeout=20, 
            frequency=EC.element_to_be_clickable, 
            locator=By.CSS_SELECTOR
        ):
        return WebDriverWait(self.driver, timeout).until(
            frequency((locator, css))
        )

    def load_page(self):
        self.driver.get(self.url)
        clear_btn = self.get_clear_btn()
        if clear_btn:
            clear_btn.click()

        print("Setting up filters..")

        filter_btn = self.web_driver_wait(
            "#controls > div > div > div.p-explorer_controls__selects_col.p-explorer_controls__selects_col__left > div > div:nth-child(3) > button",
            20,
            self.clickable_element,
            self.css_selector
        )
        filter_btn.click()

        acc_types_btn = self.web_driver_wait(
            "#c-advanced_search_modal-account-types_button",
            20,
            self.clickable_element,
            self.css_selector
        )
        acc_types_btn.click()

        select_acc_types_btn = self.web_driver_wait(
            "#c-advanced_search_modal-account-types_option_3",
            20,
            self.clickable_element,
            self.css_selector
        )
        select_acc_types_btn.click()
        
        search_btn = self.web_driver_wait(
            "body > div.c-sk-modal_portal > div > div > div.c-sk-modal_footer.c-sk-modal_footer--responsive-column > div > button.c-button.c-button--primary.c-button--medium",
            20,
            self.clickable_element,
            self.css_selector
        )
        search_btn.click()

        search_input_css = "div.ql-editor.ql-blank"
        self.web_driver_wait(
            search_input_css,
            30, 
            self.check_visibility
        )

    def get_clear_btn(self, ):
        try:
            clear_btn = self.web_driver_wait(
                "body > div.p-client_container > div > div > div.p-client_workspace_wrapper > div.p-client_workspace > div.p-client_workspace__layout > div:nth-child(2) > div:nth-child(2) > div > div > div.p-explorer_search__container.p-explorer_search__container--tinted > div > div > div.c-search__input_and_close > div > div > div > button",
                7,
                self.clickable_element
            )
        except Exception:
            clear_btn = None
        return clear_btn 
    
    def quit(self):
        self.driver.quit()

    def sleep(self):
        #time.sleep(2)
        #self.quit()
        pass

    def search_members(self, letter):
        search_input_css = "div.ql-editor.ql-blank"
        search_input = self.web_driver_wait(
            search_input_css,
            7,
            self.clickable_element
        )
        search_input.click()
        print(f"Searching {letter} members")
        search_input.clear()
        search_input.send_keys(letter)
        search_input.send_keys(Keys.RETURN)
        
        nxt_btn = None
        try:
            nxt_btn = self.find_nxt_btn()
        except TimeoutException as ex:
            error = ex
            nxt_btn = None
            print(f"LINE 133 TimeoutException: {error}")

        member_names = []
        
        self.scrape_members(member_names)
        page_count = 1
        while nxt_btn:
            try:
                nxt_btn.click()
                page_count += 1
                self.scrape_members(member_names)
                nxt_btn = self.find_nxt_btn()
                if page_count == 101:
                    nxt_btn = None
            except:
                nxt_btn = None
                pass
        return member_names
    
    def find_nxt_btn(self):
        try:
            WebDriverWait(self.driver, 7).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-qa="c-pagination_forward_btn"].c-button-unstyled.c-icon_button.c-icon_button--size_small.c-pagination__arrow_btn.c-icon_button--default'))
            )
            nxt_btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-qa="c-pagination_forward_btn"].c-button-unstyled.c-icon_button.c-icon_button--size_small.c-pagination__arrow_btn.c-icon_button--default'))
            )
        except Exception:
            nxt_btn = None
        return nxt_btn

    def scrape_members(self, member_names):
        try:
            self.web_driver_wait(
                'span.p-browse_page_member_card_entity__name_text',
                10,
                self.check_visibility,
                self.css_selector
            )
            members = self.driver.find_elements(
                self.css_selector,
                'span.p-browse_page_member_card_entity__name_text'
            )
            for member in members:
                member_names.append(member.text)
        except Exception:
            time.sleep(1)
            pass
        return member_names

    def search_admins(self,):
        print("Searching admins..")

        filter_btn = self.web_driver_wait(
            "#controls > div > div > div.p-explorer_controls__selects_col.p-explorer_controls__selects_col__left > div > div:nth-child(3) > button",
            20,
            self.clickable_element,
            self.css_selector
        )
        clear_btn = self.get_clear_btn()
        clear_btn.click()
        filter_btn.click()
        self.web_driver_wait(
            "#c-advanced_search_modal-account-types_button",
            30,
            self.check_visibility,
            self.css_selector
        )
        acc_types_btn = self.web_driver_wait(
            "#c-advanced_search_modal-account-types_button",
            20,
            self.clickable_element,
            self.css_selector
        )
        acc_types_btn.click()

        filter_admin_btn = self.web_driver_wait(
            "#c-advanced_search_modal-account-types_option_2",
            20,
            self.clickable_element,
            self.css_selector
        )
        filter_admin_btn.click()
        
        search_btn = self.web_driver_wait(
            "body > div.c-sk-modal_portal > div > div > div.c-sk-modal_footer.c-sk-modal_footer--responsive-column > div > button.c-button.c-button--primary.c-button--medium",
            20,
            self.clickable_element,
            self.css_selector
        )
        search_btn.click()
        admins_arr = []
        self.scrape_members(admins_arr)
        return admins_arr


letters_arr = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
    'Y', 'Z'
]


config = yaml.safe_load(open('selenium/config.yaml'))

chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={config['user_data_dir']}") 
chrome_options.add_argument(f"profile-directory={config['profile']}") 

csv_path = config["csv_path"]
group_name = config["group_name"]
filepath = f"{csv_path}{group_name}/subfolder/"
os.makedirs(filepath, exist_ok=True)

members = []
service = Service(config["chromedriver"])
scraper = None
try:
    print("Starting..")
    for letter in letters_arr:
        filename = f"{filepath}{letter}.csv"
        if not os.path.exists(filename):
            if letter in ("A", "I", "Q") or scraper == None:
                scraper = SlackScrapeMembers(
                    service, 
                    chrome_options, 
                    config["workspace_url"]
                )
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                #writer.writerow(letter)
                scraper.load_page()
                members = scraper.search_members(letter)
                print("Saving...")
                for member in members:
                    writer.writerow([member])
                time.sleep(2)
                if letter in ("H", "P"):
                    scraper.quit()

    csv_files = glob.glob(os.path.join(filepath, '*.csv'))

    main_df = pd.DataFrame()
    df_list = []
    for csv in csv_files:
        try:
            sub_df = pd.read_csv(csv, header=None)
            df_list.append(sub_df)
        except:
            pass

    main_df = pd.concat(df_list, ignore_index=True)
    main_df = main_df.drop_duplicates()
    
    admins = scraper.search_admins()
    scraper.quit()
    print(f"Admins: {admins}")
    for admin in admins:
        main_df = main_df[~main_df.apply(lambda row: row.astype(str).str.contains(admin)).any(axis=1)]

    main_df.to_csv(f"{csv_path}{group_name}/{group_name}.csv", index=False, header=None)

    split_index = len(main_df) // 2
    p1_df = main_df.iloc[:split_index].reset_index(drop=True)
    p2_df = main_df.iloc[split_index:].reset_index(drop=True)
    p1_df.to_csv(f"{csv_path}{group_name}/{group_name}-p1.csv", index=False, header=None)
    p2_df.to_csv(f"{csv_path}{group_name}/{group_name}-p2.csv", index=False, header=None)

    print(main_df.shape)
except Exception as ex:
    if os.path.exists(filename):
        os.remove(filename)
    error = ex
    print(f"LINE 242 ERROR: {error}")
