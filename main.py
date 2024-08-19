from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class SlackBot:
    def __init__(self, service, chrome_options, **ignore):
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.retries_limit = 3

    def web_driver_wait(
            self, 
            identifier, 
            timeout=5, 
            condition=EC.element_to_be_clickable,
            locator=By.CSS_SELECTOR, 
            retries=0
        ):
        try:
            return WebDriverWait(self.driver, timeout).until(
                condition((locator, identifier))
            )
        except TimeoutException:
            if retries < self.retries_limit:
                print(f"Retrying ({retries + 1}/{self.retries_limit})...")
                # Use recursion with incremented retries count
                return self.web_driver_wait(
                    identifier,
                    timeout, 
                    condition,
                    locator,
                    retries + 1
                )
            else:
                print(f"Timed out waiting for {identifier}")
                return None
        
    def quit(self):
        self.driver.quit()