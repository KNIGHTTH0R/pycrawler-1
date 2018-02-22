# 知乎模拟登录（现在该方法已无法使用）
import requests

# python2 python3兼容的写法
try:
    import cookielib
except:
    import http.cookiejar as cookielib  # python3
import re

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")  # 方便存取cookies
try:
    session.cookies.load(ignore_discard=True)
except:
    print("cookie未能加载")

user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0"
headers = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": user_agent
}


# 获取 xsrf token (网站为防止跨站请求伪造(CSRF, Cross-site request forgery)...)
def get_xsrf():
    resp = session.get("https://www.zhihu.com", headers=headers)
    match_obj = re.match(r'.*name="_xsrf value="(.*?)"', resp.text)
    if match_obj:
        return match_obj.group(1)
    else:
        return ""


def is_login():
    # 通过个人中心页面返回状态码来判断是否为登录状态
    inbox_url = "https://www.zhihu.com/question/56250357/answer/148534773"
    response = session.get(inbox_url, headers=header, allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


def zhihu_login(account, password):
    if re.match(r'1\d{10}', account):
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "phone_num": account,
            "password": password
        }
    else:
        if "@" in account:
            # 判断用户名是否为邮箱
            print("邮箱方式登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "_xsrf": get_xsrf(),
                "email": account,
                "password": password
            }
    resp_text = session.post(post_url, post_data, headers=headers)
    session.cookies.save()


zhihu_login("124141241", "12445")
