from selenium import webdriver
from scrapy.selector import Selector
import time


browser = webdriver.Chrome(executable_path="D:/tools/drivers/chromedriver.exe")
print(browser.page_source)

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

# 自动下拉滚动条
browser.get('https://www.oschina.net/blog')
for i in range(7):
    time.sleep(1.2)
    browser.execute_script('window.scrollTo(0,document.body.scrollHeight);')

# 设置chrome不加载图片
chrome_opt = webdriver.ChromeOptions()
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_opt.add_experimental_option('prefs', prefs)
browser2 = webdriver.Chrome(executable_path="D:/tools/drivers/chromedriver.exe", chrome_options=chrome_opt)
browser2.get('https://www.taobao.com/')

# browser.find_element_by_css_selector()
# browser selector 速度不如 scrapy.selector(written by c语言)
# t_selector = Selector(text=browser2.page_source)
# title = t_selector.css('.tb-main-title::text').extract_first()
# price = t_selector.css('#J_PromoPriceNum::text').extract_first()
# print('title:{0}, ${1}'.format(title, price))
# browser.quit()

# #phantomjs, 无界面的浏览器， 多进程情况下phantomjs性能会下降很严重
# browser = webdriver.PhantomJS(executable_path="E:/home/phantomjs-2.1.1-windows/bin/phantomjs.exe")
# browser.get("https://detail.tmall.com/item.htm?spm=a230r.1.14.3.yYBVG6&id=538286972599&cm_id=140105335569ed55e27b&abbucket=15&sku_properties=10004:709990523;5919063:6536025")
# print(browser.page_source)
# browser.quit()
