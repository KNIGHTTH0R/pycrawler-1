# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from fake_useragent import UserAgent
from articleCrawler.tools.crawl_xici_ip import GetIP

# 动态ip代理middleware
class RandomProxyMiddleware(object):
    def __init__(self):
        self.get_ip = GetIP()

    def process_request(self, request, spider):
        request.meta['proxy'] = self.get_ip.get_random_ip()


class RandomUserAgentMiddleware(object):

    def __init__(self, crawler):
        super(RandomUserAgentMiddleware, self).__init__()  # 有必要吗？
        self.ua = UserAgent()  # 国外网站维护的一大堆user-agent，加载速度比较慢
        self.ua_type = crawler.settings.get('RANDOM_UA_TYPE', 'random')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)  # just like RandomUserAgentMiddleware(crawler)

    def process_request(self, request, spider):
        def get_ua():
            return getattr(self.ua, self.ua_type)

        request.headers.setdefault('User-Agent', get_ua())
        # ip proxy
        # request.meta['proxy'] = 'http://183.48.91.80:8118'

from scrapy.http import HtmlResponse
class JSPageMiddleware(object):
    # 通过selenium chrome请求动态页面

    def process_request(self, request, spider):
        if spider.name == "jobbole":  # and request.url == re.match......
            spider.browser.get(request.url)
            print("使用chrome访问:{0}".format(request.url))
            resp = HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source, encoding='utf-8')
            return resp


class ArticlecrawlerSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
