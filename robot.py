import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
from diary_reader import DiaryReader
from baidu_ocr import BaiduOcrParser


class DiaryRobot(object):
    _URI = "https://u.jss.com.cn/Contents/usercenter/allow/login/login.jsp?redirecturl=oa&jumpurl=https://oa.jss.com.cn/"

    def __init__(self, cfg_file=None) -> None:
        if cfg_file is None:
            self.cfg = self.load_cfg("robot.json")
        else:
            self.cfg = self.load_cfg(cfg_file)

        self.username = self.cfg["oa_user"]
        self.userpwd = self.cfg["oa_pwd"]

        self.baidu_parser = BaiduOcrParser(self.cfg["baidu_client_id"], self.cfg["baidu_client_secret"])
        self.notion_reader = DiaryReader(self.cfg["notion_api_key"], self.cfg["notion_database_id"])
        
        # option = webdriver.ChromeOptions()
        # option.add_experimental_option("detach", True)

        self.driver = webdriver.Chrome() # options=option)

    def load_cfg(self, cfg_file):
        with open(cfg_file, "rb") as reader:
            cfg = json.loads(reader.read().decode('utf8'))
            return cfg
    
    def close(self):
        self.driver.close()
        self.driver.quit()

    def open_login_page(self, bmaximize=True):
        self.driver.get(self._URI)
        if bmaximize:
            self.driver.maximize_window()
    
    def find_loginpage_element(self):
        input_username = self.get_element("#usernameInput")
        input_userpwd = self.get_element("body > div.g-content.f-pr.g-content-bg > div > div.wrap.m-box.f-clearfix > div.form-box.f-fl > div > div > form:nth-child(1) > div.item.e-mt6.pwd_container > input")
        input_code = self.get_element("body > div.g-content.f-pr.g-content-bg > div > div.wrap.m-box.f-clearfix > div.form-box.f-fl > div > div > form:nth-child(1) > div.item.e-mt6.vcode > input")
        code_img = self.get_element("body > div.g-content.f-pr.g-content-bg > div > div.wrap.m-box.f-clearfix > div.form-box.f-fl > div > div > form:nth-child(1) > div.item.e-mt6.vcode > img")
        button_login = self.get_element("body > div.g-content.f-pr.g-content-bg > div > div.wrap.m-box.f-clearfix > div.form-box.f-fl > div > div > form:nth-child(1) > div.item.e-mt15 > button")
        code_error_text = self.get_element("body > div.g-content.f-pr.g-content-bg > div > div.wrap.m-box.f-clearfix > div.form-box.f-fl > div > div > form:nth-child(1) > p:nth-child(6) > em")

        return input_username, input_userpwd, input_code, code_img, button_login, code_error_text
    
    def get_code_img(self, code_img_elem, save_name):
        # Fixed to 1.25, may be change it on other system.
        r = 1.25
        location = code_img_elem.location
        img_size = code_img_elem.size
        rangle = (
            int(location['x'] * r), int(location['y'] * r), int((location['x'] + img_size['width']) * r),
            int((location['y'] + img_size['height']) * r)
        )

        self.driver.save_screenshot("image/page.png")
        img = Image.open("image/page.png")
        code_img = img.crop(rangle)
        code_img.save(save_name)
    
    def get_element(self, css_selector_value):
        return self.driver.find_element(by=By.CSS_SELECTOR, value=css_selector_value)

    def run(self):
        # Login Page
        self.open_login_page(True)
        input_username, input_userpwd, input_code, code_img, button_login, code_error_text = self.find_loginpage_element()

        input_username.send_keys(self.username)
        input_userpwd.send_keys(self.userpwd)

        is_right = False
        max_try_time = 20

        code_image_file_name = "image/code.png"
        while (not is_right and max_try_time > 0):
            self.get_code_img(code_img, code_image_file_name)
            code = self.baidu_parser.get_image_text(code_image_file_name)
            if code is not None:
                input_code.send_keys(code)
                button_login.click()
                time.sleep(1)
                
                # if the code is correct, the follow code may be raise exeception, because new page is loaded.
                try:
                    if (code_error_text.is_displayed):
                        input_code.clear()
                        is_right = False
                    else:
                        is_right = True
                except:
                    break
            else:
                code_img.click()   # click to refresh if can't recognition
            max_try_time -= 1
        
        # Page 2
        self.driver.implicitly_wait(4)   # implicitly wait 5 seconds for loading page
        try:
            report_menu_item = self.get_element("#root > div > div > div:nth-child(2) > div.g-wrap.oa-clearfix.oa-mt20 > div.menu-wrap.oa-fl > ul > li:nth-child(6) > a")
            report_menu_item.click()

            diary_report_page = self.get_element("body > div.g-content > div > div.g-main.f-fr > div.m-apply > div > ul > li.s-crt > a")
            diary_report_page.click()

            _, today_finished, torrow_plan, _ = self.notion_reader.get_recent_diary()

            txt_today_finished = self.get_element("#z-day-form > div.z-detail > div:nth-child(2) > textarea")
            txt_today_finished.send_keys(today_finished)

            txt_tomorrow_plan = self.get_element("#z-day-form > div.z-detail > div:nth-child(3) > textarea")
            txt_tomorrow_plan.send_keys(torrow_plan)

            # TODO: add today_summary send if you need.

            # PageDown
            self.driver.execute_script("window.scrollTo(0,500)")
            time.sleep(1)
    
            cc_dogs = self.get_element("#z-day-form > div.z-detail > div:nth-child(6) > div")
            cc_dogs.click()
            
            cc_dogs_list = self.cfg['cc']
            if cc_dogs_list is not None:
                edt_dog_search = self.get_element("#z-day-form > div.z-detail > div:nth-child(6) > div > input")
                for dog_name in cc_dogs_list:
                    edt_dog_search.send_keys(dog_name)

                    try:
                        search_span = self.get_element("body > div.ui-search > div > div.search-result > div.search-list > ul > li > span")
                        search_span.click()
                    except:
                        edt_dog_search.clear()
                        continue
            
            # 隐藏抄送框后才可以点击提交
            memory_ = self.get_element("#z-day-form > div.z-detail > div.x-input.item.e-mt20 > div > div.edit.f-clearfix.e-mt10 > textarea")
            memory_.click()

            submit_button = self.get_element("#z-day-form > a.e-ml8.z-submit-day.f-fl.e-mt20.btn-submit")
            submit_button.click()

            return True
        except Exception as e:
            return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        robot = DiaryRobot(sys.argv[1])
    else:
        robot = DiaryRobot()
    
    robot.run()
    robot.close()
