from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import csv
import yaml
import time


class SlackSendMessage:
    def __init__(self, service, chrome_options, url, csv_path, group_name):
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.url = f"{url}/dms"
        self.csv_path = csv_path
        self.css_selector = By.CSS_SELECTOR

        self.clickable_element = EC.element_to_be_clickable
        self.check_visibility = EC.visibility_of_element_located
        self.count = 0
        self.group_name = group_name

    def web_driver_wait(self, css, timeout=5, condition=EC.element_to_be_clickable):
        return WebDriverWait(self.driver, timeout).until(
            condition((self.css_selector, css))
        )
    
    def build_message(self, member, message_input, main_message=True):
        if main_message:
            message = f"""This is a test message"""
        else:
            message = f"""This is a test message"""

        for line in message.split('\n'):
            message_input.send_keys(line)
            message_input.send_keys(Keys.SHIFT, Keys.ENTER)
        return message

    
    def send_message(self, members, main_message=True):
        self.driver.get(self.url)
        for member in members:
            try: 
                dm_field = self.web_driver_wait(
                    "#dms_tab_page__destination"
                )
                dm_field.click()
                dm_field.send_keys(member[0], Keys.RETURN)
                member_dropdown = self.web_driver_wait(
                    "#dms_tab_page__destination_option_0 > span > div > div > div > div > span > span.c-member__member-name.c-member_name.c-member_name--inverted.c-base_entity__text > span > strong"
                )
                member_dropdown.click()

                message_input_css = "div.ql-editor.ql-blank"
                self.web_driver_wait(
                    message_input_css,
                    7, 
                    self.check_visibility
                )

                message_input = self.web_driver_wait(
                    message_input_css,
                    7,
                    self.clickable_element
                )
                message_input.click()
                self.build_message(member[0], message_input, main_message)
                message_input.send_keys(Keys.RETURN)
                self.count += 1
            except TimeoutException:
                print(member)
                pass

        self.driver.quit()



config = yaml.safe_load(open('selenium/config.yaml'))


def get_members(filepath):
    with open(f"{filepath}", mode='r', newline='', encoding='utf-8') as file:
        reader  = csv.reader(file)
        members = list(reader)
        first_20_members = members[:40]
        remaining_members = members[40:]

    with open(f"{filepath}", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(remaining_members)
    return first_20_members


filepath = f'{config["csv_path"]}{config["group_name"]}/{config["csv_name"]}.csv'
first_40_members = get_members(filepath)
flag = True
sent_messages = 0
less_prio = False
while flag:
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={config['user_data_dir']}") 
    chrome_options.add_argument(f"profile-directory={config['profile'][0]}") 

    service = Service(config["chromedriver"])
    slack_dm = SlackSendMessage(
        service, 
        chrome_options, 
        config["workspace_url"], 
        config["csv_path"],
        config["group_name"]
    )
    print(config["group_name"])
    main_message = False if less_prio else True
    slack_dm.send_message(first_40_members, main_message)
    sent_messages += slack_dm.count
    print(f"Message sent: {sent_messages}")
    print("Getting new member list")
    time.sleep(1)
    first_40_members = get_members(filepath)
    if not first_40_members:
        filepath = f'{config["csv_path"]}{config["group_name"]}/{config["csv_name2"]}.csv'

        if not less_prio:
            less_prio = True
        else:
            print(f"Total messages sent: {sent_messages}")
            flag = False