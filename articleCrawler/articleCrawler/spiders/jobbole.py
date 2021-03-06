# -*- coding: utf-8 -*-
import scrapy
import re
from urllib import parse
from scrapy import Request
from articleCrawler.items import JobBoleArticleItem, ArticleItemLoader
from articleCrawler.utils.common import get_md5
import datetime
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    # def __init__(self):
    #     self.browser = webdriver.Chrome('D:/tools/drivers/chromedriver.exe')
	#	  super(JobboleSpider, self).__init__() # must be called or _rules stuff can't be initialized
    #     # scrapy信号量，doing specified things when receiving the specified signal (an event happening)
    #     dispatcher.connect(self.spider_closed, signal=signals.spider_closed)
    #
    # def spider_closed(self, spider):
    #     print('spider---{0} closed!'.format(self.name))
    #     self.browser.quit()

    # # scrapy数据收集器放在crawler,stats里面
    # #收集伯乐在线所有404的url以及404页面数
    # handle_httpstatus_list = [404]
    #
    # def __init__(self, **kwargs):
    #     self.fail_urls = []
    #     dispatcher.connect(self.handle_spider_closed, signals.spider_closed)
    #
    # def handle_spider_closed(self, spider, reason):
    #     self.crawler.stats.set_value("failed_urls", ",".join(self.fail_urls))


    def parse(self, response):
        post_nodes = response.css('#archive div.floated-thumb .post-thumb a')
        for post_node in post_nodes:
            # url may not have base url(domain), so use urljoin to complete it; 没有则使用response.url补全，有则忽视
            img_url = parse.urljoin(response.url, post_node.css('img::attr(src)').extract_first(""))
            post_url = parse.urljoin(response.url, post_node.css('::attr(href)').extract_first(""))
            print("crawling url={}........".format(post_url))
            # 每次调用在此处返回一个Request对象，下次调用再返回下一个Request对象，像iterator一样的生成器函数
            # 通过meta写入response传递参数到parse_detail
            yield Request(url=post_url, meta={"front_image_url":img_url}, callback=self.parse_detail)
        # next page  class="next page-numbers"
        next_page = response.css('.next.page-numbers::attr(href)').extract_first("")
        if next_page:
            yield Request(url=parse.urljoin(response.url, next_page), callback=self.parse)


    def parse_detail(self, response):
        """
        parse each article
        :param response:
        :return:
        """

        front_image_url = response.meta.get("front_image_url", "")  # 文章封面图(点进去之前的缩略图..)
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_xpath("title", '//div[@class="entry-header"]/h1/text()')
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_css("vote_up_nums", ".vote-post-up h10::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        article_item = item_loader.load_item()

        yield article_item # deliver this item to pipelines

        # # response.xpath('...')  return selector list
        # title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first("")
        # # title = response.css(".entry-header h1::text")[0].extract()
        # # title = response.xpath('//div[@class="entry-header"]').xpath('//h1/text()').extract()[0]
        #
        # front_image_url = response.meta.get("front_image_url", "")# 文章封面图(点进去之前的缩略图..)
        #
        # create_date = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()')[0].extract()
        # create_date = create_date.strip().replace("·", " ").strip()
        # try:
        #     create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        # except Exception as e:
        #     create_date = datetime.datetime.now().date()
        #
        # vote_up_nums = response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract_first("")
        # if vote_up_nums:
        #     vote_up_nums = int(vote_up_nums)
        # else:
        #     vote_up_nums = 0
        #
        # fav_nums = response.xpath('//span[contains(@class,"bookmark-btn")]/text()').extract()[0]
        # num_regex = r'.*?(\d+).*'
        # match_obj = re.match(num_regex, fav_nums)
        # if match_obj:
        #     fav_nums = int(match_obj.group(1))
        # else:
        #     fav_nums = 0
        #
        # comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]
        # match_obj = re.match(num_regex, comment_nums)
        # if match_obj:
        #     comment_nums = int(match_obj.group(1))
        # else:
        #     comment_nums = 0
        #
        # content = response.xpath('//div[@class="entry"]').extract()[0]
        #
        # tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        # tag_list = [e for e in tag_list if not e.strip().endswith('评论')]
        # tag_list = ','.join(tag_list)
        #
        # article_item = JobBoleArticleItem()
        # article_item["title"] = title
        # article_item["url"] = response.url
        # article_item["url_object_id"] = get_md5(response.url)
        # article_item["front_image_url"] = [front_image_url]
        # article_item["create_date"] = create_date
        # article_item["vote_up_nums"] = vote_up_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["comment_nums"] = comment_nums
        # article_item["tags"] = tag_list
        # article_item["content"] = content


