# -*- coding: utf-8 -*-
import scrapy
import re
import json
from urllib import parse
from scrapy.loader import ItemLoader
from articleCrawler.items import ZhihuAnswerItem, ZhihuQuestionItem
# from articleCrawler.utils.zhihu_login_new import *
import datetime



class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    # start_urls = ['https://www.zhihu.com/question/29775447', 'https://www.zhihu.com/question/267501074']
    topics = ['https://www.zhihu.com/topic/19569409', 'https://www.zhihu.com/topic/20004246/hot']

    # answers api (return answers json)
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}'

    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0"
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": user_agent
    }

    # override this method to add login logic before start crawling
    # does not work for 2018 zhihu
    def start_requests(self):
        for url in self.topics:
            yield scrapy.Request(url, dont_filter=True, headers=self.headers)

    def parse(self, response):
        """
        提取html页面里所有的url，并跟踪提取的url进一步提取
        :param response:
        :return:
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda url: True if url.startswith("https") else False, all_urls)
        for url in all_urls:
            match_question = re.match(r'(.*zhihu.com/question/(\d+)).*', url)
            match_topic = re.match(r'(.*zhihu.com/topic/(\d+)).*', url)
            if match_question:
                question_url = match_question.group(1)
                yield scrapy.Request(question_url, callback=self.parse_question, headers=self.headers)
            elif match_topic:
                topic_url = match_topic.group(1)
                yield scrapy.Request(topic_url, callback=self.parse, headers=self.headers)
            # yield scrapy.Request(url, callback=self.parse, headers=headers)  # 对所有url都进一步深入

    def parse_question(self, response):
        # deal with question, extract question item

        match_obj = re.match(r'(.*zhihu.com/question/(\d+)).*', response.url)
        if match_obj:
            question_id = match_obj.group(2)

        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_value("zhihu_id", question_id)
        item_loader.add_css('title', 'h1.QuestionHeader-title::text')
        item_loader.add_value("url", response.url)
        item_loader.add_css('content', '.QuestionHeader-detail')
        item_loader.add_css("answer_num", '#QuestionAnswers-answers .List-headerText span::text')
        item_loader.add_css('comments_num', '.QuestionHeader-Comment button::text')
        item_loader.add_css('watch_user_num', '.QuestionFollowStatus-counts .NumberBoard-itemValue::text')
        item_loader.add_css('click_num', '.QuestionFollowStatus-counts .NumberBoard-itemValue::text')
        item_loader.add_css('topics', '.QuestionHeader-topics .Popover div::text')

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), callback=self.parse_answer,
                             headers=self.headers)  # 未登录状态无法获取！通过api获取该问题下的答案
        yield question_item

    def parse_answer(self, response):
        ans_json = json.load(response.text)
        is_end = ans_json['paging']['is_end']
        totals = ans_json['paging']['totals']
        next_url = ans_json['paging']['next']

        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]['id'] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()
            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, callback=self.parse_answer, headers=self.headers)




    # 新版知乎让模拟登录变得异常麻烦，验证码更是使用了颠倒的汉字
    # def login(self, response):
    #     signin_url = 'https://www.zhihu.com/api/v3/oauth/sign_in'
    #     headers = getheaders()
    #     data = getdata("username21312", "password")
    #     checkcapthca(headers)
    #     # multipart_encoder = MultipartEncoder(fieles=data, boundary='----WebKitFormBoundarycGPN1xiTi2hCSKKZ')
    #     # todo:boundary后面的几位数可以随机，现在是固定的
    #     encoder = MultipartEncoder(data, boundary='----WebKitFormBoundarycGPN1xiTi2hCSKKZ')
    #     headers['Content-Type'] = encoder.content_type
    #     print(encoder.to_string())
    #     return [scrapy.FormRequest(
    #         url=signin_url,
    #         formdata=encoder.to_string(),
    #         headers=headers,
    #         callback=self.check_login
    #     )]

    #  通过 scrapy的 yield request方式
    # 可以保证所有的request都在同一个session下，（sessionID的cookie相同）
    # def apicture(self):
    #     yield scrapy.Request(url="aaa picture", callback=self.btext)
    #
    # def btext(self):
    #     yield scrapy.Request(url="bbb text", callback=self.crar)
    #
    # def check_login(self, response):
    #     #验证服务器的返回数据判断是否成功
    #     text_json = json.loads(response.text)
    #     if "msg" in text_json and text_json["msg"] == "登录成功":
    #         for url in self.topics:
    #             yield scrapy.Request(url, dont_filter=True, headers=self.headers)
