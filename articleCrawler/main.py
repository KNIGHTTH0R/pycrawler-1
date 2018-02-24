from scrapy.cmdline import execute
import sys
import os

# set current path = project root directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(["scrapy", "crawl", "zhihu"])  # scrapy crawl zhihu
