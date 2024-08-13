from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import yaml
import time
import logging
import datetime
import os
import typer

app = typer.Typer()

config = yaml.safe_load(open('selenium/config.yaml'))

#log_file = f'{config["csv_path"]}{config["group_name"]}/logs/'
log_file = f'selenium/logs/'
os.makedirs(log_file, exist_ok=True)
# Configure logging

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
        try:
            return WebDriverWait(self.driver, timeout).until(
                condition((self.css_selector, css))
            )
        except TimeoutException:
            logging.warning(f"Timed out waiting for {css}")
            return None

    def build_message(self, member, message_input):
        message = f"""Would love to network with you over on X/Twitter if you're open to it, {member}

On X, I teach people how to launch, grow, and scale their business online...the new way.

You can add me here: https://twitter.com/intent/user?screen_name=StuartIsaacBest

Feel free to DM over there, if you need any marketing advice."""
        for line in message.split('\n'):
            message_input.send_keys(line)
            message_input.send_keys(Keys.SHIFT, Keys.ENTER)
        return message

    def send_message(self, members):
        self.driver.get(self.url)
        successful_members = []
        for member in members:
            try:
                dm_field = self.web_driver_wait("#dms_tab_page__destination")
                if dm_field:
                    dm_field.click()
                    dm_field.send_keys(member[0], Keys.RETURN)
                    member_dropdown = self.web_driver_wait(
                        "#dms_tab_page__destination_option_0 > span > div > div > div > div > span > span.c-member__member-name.c-member_name.c-member_name--inverted.c-base_entity__text > span > strong"
                    )
                    if member_dropdown:
                        member_dropdown.click()

                        message_input_css = "div.ql-editor.ql-blank"
                        message_input = self.web_driver_wait(
                            message_input_css,
                            7,
                            self.clickable_element
                        )
                        if message_input:
                            message_input.click()
                            # self.build_message(member[0], message_input)
                            # message_input.send_keys(Keys.RETURN)
                            self.count += 1
                            # successful_members.append(member)
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(f"Error: {e}")
            finally:
                time.sleep(1)  # Add a small delay between messages

        self.driver.quit()
        return successful_members

def get_members(filepath):
    with open(filepath, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        members = list(reader)
        first_40_members = members[:40]
    return first_40_members

def remove_successful_members(filepath, successful_members):
    with open(filepath, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        all_members = list(reader)

    remaining_members = [member for member in all_members if member not in successful_members]

    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(remaining_members)


@app.command()
def main(part):
    if part == "main":
        filepath = f'{config["csv_path"]}{config["group_name"]}/{config["group_name"]}.csv'
    else:
        filepath = f'{config["csv_path"]}{config["group_name"]}/{config["group_name"]}-{part}.csv'
    logging.basicConfig(
        level=20, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=f'{log_file}{config["group_name"]}-{datetime.datetime.now().strftime("%Y-%m-%d")}-{part}.log', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if part == "p1":
        profile = config['profile'][0]
    elif part == "p2":
        profile = config['profile'][1]
    else:
        profile = config['profile'][0]
    print(profile)

    first_40_members = get_members(filepath)
    flag = True
    sent_messages = 0
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={config['user_data_dir']}")
    chrome_options.add_argument(f"profile-directory={profile}")

    service = Service(config["chromedriver"])

    error = 0

    while flag:
        try:
            slack_dm = SlackSendMessage(
                service,
                chrome_options,
                config["workspace_url"],
                config["csv_path"],
                config["group_name"]
            )
            successful_members = slack_dm.send_message(first_40_members)
            sent_messages += slack_dm.count
            print(f"Messages sent: {sent_messages}")
            
            remove_successful_members(filepath, successful_members)
            time.sleep(1)
            first_40_members = get_members(filepath)
            if not first_40_members:
                print(f"Total messages sent: {sent_messages}")
                flag = False
        except Exception as e:
            error += 1
            logging.error(f"Exception: {e}")
            if 'slack_dm' in locals():
                slack_dm.driver.quit()
            if error == 3:
                flag = False
                logging.error("ERROR: Try to login in Slack group.")

if __name__ == "__main__":
    app()