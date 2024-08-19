import yaml
import logging
import time
import os
import csv
import glob
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from main import SlackBot


letters_arr = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
    'Y', 'Z'
]

config = yaml.safe_load(open('config.yaml'))

chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={config['user_data_dir']}") 
chrome_options.add_argument(f"profile-directory={config['profile'][0]}") 

service = Service(config["chromedriver"])
csv_path = config["csv_path"]
group_name = config["group_name"]
csv_name = config["csv_name"]
filepath = f"{csv_path}{group_name}/subfolder/"
url = f'{config["workspace_url"]}/people'
os.makedirs(filepath, exist_ok=True)


def get_clear_btn(bot):
    try:
        clear_btn = bot.web_driver_wait(
            "body > div.p-client_container > div > div > div.p-client_workspace_wrapper > div.p-client_workspace > div.p-client_workspace__layout > div:nth-child(2) > div:nth-child(2) > div > div > div.p-explorer_search__container.p-explorer_search__container--tinted > div > div > div.c-search__input_and_close > div > div > div > button",
            3,
            EC.element_to_be_clickable
        )
    except Exception:
        clear_btn = None
    return clear_btn 


def load_page(bot):
    bot.driver.get(url)

    clear_btn = get_clear_btn(bot)
    if clear_btn:
        clear_btn.click()

    print("Setting up filters..")
    filter_btn = bot.web_driver_wait(
        "#controls > div > div > div.p-explorer_controls__selects_col.p-explorer_controls__selects_col__left > div > div:nth-child(3) > button",
        20,
        EC.element_to_be_clickable
    )
    filter_btn.click()

    acc_types_btn = bot.web_driver_wait(
        "#c-advanced_search_modal-account-types_button",
        20,
        EC.element_to_be_clickable
    )
    acc_types_btn.click()


def search_members(bot, letter, account_type="3"):
    select_acc_types_btn = bot.web_driver_wait(
        f"#c-advanced_search_modal-account-types_option_{account_type}",
        20,
        EC.element_to_be_clickable
    )
    select_acc_types_btn.click()
    search_btn = bot.web_driver_wait(
        "body > div.c-sk-modal_portal > div > div > div.c-sk-modal_footer.c-sk-modal_footer--responsive-column > div > button.c-button.c-button--primary.c-button--medium",
        20,
        EC.element_to_be_clickable
    )
    search_btn.click()

    if letter:
        search_input_css = "div.ql-editor.ql-blank"
        search_input = bot.web_driver_wait(
            search_input_css,
            5,
            EC.element_to_be_clickable
        )
        search_input.click()
        search_input.clear()
        search_input.send_keys(letter)
        search_input.send_keys(Keys.RETURN)

    row_group_css = "div[role='rowgroup'].p-grid__rowgroup"
    bot.web_driver_wait(
        row_group_css,
        10,
        EC.visibility_of_all_elements_located,
        By.CSS_SELECTOR
    )

    bot.web_driver_wait(
        "div.p-grid__cell",
        10,
        EC.visibility_of_all_elements_located,
        By.CSS_SELECTOR
    )
    
    nxt_btn = find_nxt_btn(bot)
    members = []
    scrape_members(bot, members)
    page_count = 1
    while nxt_btn:
        try:
            nxt_btn.click()
            page_count += 1
            scrape_members(bot, members)
            nxt_btn = find_nxt_btn(bot)
            if page_count == 101:
                nxt_btn = None
        except:
            nxt_btn = None
            pass
    return members


def find_nxt_btn(bot):
    nxt_btn_css = 'button[data-qa="c-pagination_forward_btn"].c-button-unstyled.c-icon_button.c-icon_button--size_small.c-pagination__arrow_btn.c-icon_button--default'
    bot.web_driver_wait(
        nxt_btn_css,
        10,
        EC.visibility_of_element_located,
        By.CSS_SELECTOR
    )
    nxt_btn = bot.web_driver_wait(
        nxt_btn_css,
        3,
        EC.element_to_be_clickable,
        By.CSS_SELECTOR
    )
    return nxt_btn


def extract_time(time_string, reference_date=None):
    # Check if the time_string mentions "yesterday"
    if "yesterday" in time_string:
        # Adjust the reference_date to the previous day
        reference_date = (reference_date or datetime.now()) - timedelta(days=1)
        time_string = time_string.replace(" (yesterday)", "")
    if "tomorrow" in time_string:
        # Adjust the reference_date to the previous day
        reference_date = (reference_date or datetime.now()) + timedelta(days=1)
        time_string = time_string.replace(" (tomorrow)", "")
    
    # Parse the time string into a datetime object
    time_obj = datetime.strptime(time_string, "%I:%M %p")
    
    # Combine the reference date with the time
    combined_datetime = datetime.combine(reference_date or datetime.now(), time_obj.time())

    # Return the time part of the combined datetime
    return combined_datetime.strftime("%Y-%m-%d %I:%M %p")


def scrape_members(bot, members):
    cells = bot.web_driver_wait(
        "div.p-grid__cell",
        10,
        EC.presence_of_all_elements_located,
        By.CSS_SELECTOR
    )

    for cell in cells:
        cell.click()
        bot.web_driver_wait(
            ".p-r_member_profile__container",
            5,
            EC.visibility_of_element_located
        )
        member_name = bot.web_driver_wait(
            ".p-r_member_profile__name__text",
            5,
            EC.presence_of_element_located,
            By.CSS_SELECTOR
        )
        local_time = bot.web_driver_wait(
            ".p-local_time__text",
            5,
            EC.presence_of_element_located,
            By.CSS_SELECTOR
        )
        now = datetime.now()
        if local_time:
            local_time = local_time.text
            if " local time" in local_time:
                local_time = local_time.replace(" local time", "")
                local_time = extract_time(local_time, now)
            formatted_time = now.strftime("%Y-%m-%d %I:%M %p")
            members.append([member_name.text, local_time, formatted_time])


def search_admins(bot,):
    bot.driver.get(url)

    # clear_btn = get_clear_btn(bot)
    # if clear_btn:
    #     clear_btn.click()

    print("Searching admins..")
    load_page(bot)
    filter_btn = bot.web_driver_wait(
        "#controls > div > div > div.p-explorer_controls__selects_col.p-explorer_controls__selects_col__left > div > div:nth-child(3) > button",
        3,
        EC.element_to_be_clickable,
        By.CSS_SELECTOR
    )
    # clear_btn = get_clear_btn(bot)
    # clear_btn.click()
    filter_btn.click()
    bot.web_driver_wait(
        "#c-advanced_search_modal-account-types_button",
        10,
        EC.visibility_of_element_located,
        By.CSS_SELECTOR
    )
    acc_types_btn = bot.web_driver_wait(
        "#c-advanced_search_modal-account-types_button",
        5,
        EC.element_to_be_clickable,
        By.CSS_SELECTOR
    )
    acc_types_btn.click()

    filter_admin_btn = bot.web_driver_wait(
        "#c-advanced_search_modal-account-types_option_2",
        5,
        EC.element_to_be_clickable,
        By.CSS_SELECTOR
    )
    filter_admin_btn.click()
    
    search_btn = bot.web_driver_wait(
        "body > div.c-sk-modal_portal > div > div > div.c-sk-modal_footer.c-sk-modal_footer--responsive-column > div > button.c-button.c-button--primary.c-button--medium",
        5,
        EC.element_to_be_clickable,
        By.CSS_SELECTOR
    )
    search_btn.click()
    admins_arr = []
    scrape_members(bot, admins_arr)
    return admins_arr

flag = True
while flag:
    try:
        bot = None
        print("Starting..")
        for letter in letters_arr:
            filename = f"{filepath}{letter}.csv"
            if not os.path.exists(filename):
                if letter in ("A", "I", "Q") or bot == None:
                    bot = SlackBot(
                        service,
                        chrome_options
                    )
                with open(filename, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    load_page(bot)
                    members = search_members(bot, letter, "3")
                    print("Saving...")
                    for member in members:
                        writer.writerow(member)
                    time.sleep(2)
                    if letter in ("H", "P", "Z"):
                        bot.quit()
            else:
                print(f"{letter} done.")
        csv_files = glob.glob(os.path.join(filepath, '*.csv'))
        main_df = pd.DataFrame()
        df_list = []
        for csv in csv_files:
            try:
                sub_df = pd.read_csv(csv, header=None)
                df_list.append(sub_df)
            except:
                pass
        bot = SlackBot(
            service,
            chrome_options
        )
        main_df = pd.concat(df_list, ignore_index=True)
        print(main_df.shape)
        main_df = main_df.drop_duplicates(subset=0)
        print(main_df.shape)

        load_page(bot)
        admins = search_members(bot, None, "2")
        bot.quit()
        names_to_remove = []
        for admin in admins:
            names_to_remove.append(admin[0])
            # main_df = main_df[~main_df.apply(lambda row: row.astype(str).str.contains(admin)).any(axis=1)]
            main_df = main_df[main_df[0] != admin[0]]
        print(names_to_remove)
        main_df.to_csv(f"{csv_path}{group_name}/{csv_name}.csv", index=False, header=None)

        print("Scraping finished...")
        flag = False
    except Exception as ex:
        if os.path.exists(filename):
            os.remove(filename)
        error = ex
        print(f"LINE 242 ERROR: {error}")
        print("Restarting...")
        time.sleep(5)