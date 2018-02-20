# -*- coding: utf-8 -*-
import scrapy
import re
from urllib import parse
from scrapy import Request


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        # get all url and use self.parse_detail to parse it
        posts_url = response.css('#archive div.floated-thumb .post-thumb a::attr("href")').extract()
        # post_url may not have base url, so use urljoin to complete it
        for post_url in posts_url:
            print("crawling url:{}........", post_url)
            # 每次调用在此处返回一个Request对象，下次调用再返回下一个Request对象，像iterator一样的生成器函数
            yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse_detail)
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
        # response.xpath('...')  return selector list
        title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first("")
        # title = response.css(".entry-header h1::text")[0].extract()
        # title = response.xpath('//div[@class="entry-header"]').xpath('//h1/text()').extract()[0]

        create_date = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()')[0].extract()
        create_date = create_date.strip().replace("·", " ").strip()

        vote_up_nums = response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract_first("")
        if vote_up_nums:
            vote_up_nums = int(vote_up_nums)
        else:
            vote_up_nums = 0

        fav_nums = response.xpath('//span[contains(@class,"bookmark-btn")]/text()').extract()[0]
        num_regex = r'.*?(\d+).*'
        match_obj = re.match(num_regex, fav_nums)
        if match_obj:
            fav_nums = int(match_obj.group(1))
        else:
            fav_nums = 0

        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]
        match_obj = re.match(num_regex, comment_nums)
        if match_obj:
            comment_nums = int(match_obj.group(1))
        else:
            comment_nums = 0

        content = response.xpath('//div[@class="entry"]').extract()[0]

        tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        tag_list = [e for e in tag_list if not e.strip().endswith('评论')]
        tag_list = ','.join(tag_list)

