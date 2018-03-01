from selenium import webdriver
from scrapy.selector import Selector
import time


browser = webdriver.Chrome(executable_path="D:/tools/drivers/chromedriver.exe")
# browser.get('https://item.taobao.com/item.htm?spm=a219r.lm874.14.37.16ca690cd2NCvZ&id=563360028996&ns=1&abbucket=19')
# print(browser.page_source)

# 自动登录知乎
browser.get('https://www.zhihu.com/signup?next=%2F')
browser.find_element_by_css_selector('.SignContainer-switch span').click()  # switch to login
browser.find_element_by_css_selector('.SignFlow-accountInput input').send_keys('username21312')
browser.find_element_by_css_selector('.SignFlow-password input[name="password"]').send_keys('password131')
browser.find_element_by_css_selector('button.SignFlow-submitButton').click()

# 自动登录微博
browser.get('https://weibo.com/login.php')
# time.sleep(3)
browser.find_element_by_css_selector('.info_list.username input[node-type="username"]').send_keys('username21312')
browser.find_element_by_css_selector('div.info_list.password input[name="password"]').send_keys('password131')
browser.find_element_by_css_selector('div.info_list.login_btn a span').click()

# browser.find_element_by_css_selector()
# browser selector 速度不如 scrapy.selector(written by c语言)
# t_selector = Selector(text=browser.page_source)
# title = t_selector.css('.tb-main-title::text').extract_first()
# price = t_selector.css('#J_PromoPriceNum::text').extract_first()
# print('title:{0}, ${1}'.format(title, price))
# browser.quit()