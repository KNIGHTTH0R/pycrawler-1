import hashlib
import os


def get_md5(url):
    if isinstance(url, str):   # if it is  unicode..
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)  # only receive utf-8
    return m.hexdigest()

def get_project_dir():
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
