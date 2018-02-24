import hashlib
import os
import re


def get_md5(url):
    if isinstance(url, str):   # if it is  unicode..
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)  # only receive utf-8
    return m.hexdigest()

def get_project_dir():
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def extract_num(text):
    # 从字符串中提取一个整数
    match_re = re.match(".*?(\d+).*", text)
    if match_re:
        num = int(match_re.group(1))
    else:
        num = 0
    return num