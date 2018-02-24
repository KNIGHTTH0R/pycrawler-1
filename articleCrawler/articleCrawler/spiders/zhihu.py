# -*- coding: utf-8 -*-
import scrapy
import re
import json
from urllib import parse
from scrapy.loader import ItemLoader
from articleCrawler.items import ZhihuAnswerItem, ZhihuQuestionItem
import datetime

user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0"
headers = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": user_agent
}


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    # start_urls = ['https://www.zhihu.com/question/29775447', 'https://www.zhihu.com/question/267501074']
    topics = ['https://www.zhihu.com/topic/19569409', 'https://www.zhihu.com/topic/20004246/hot']

    # answers api (return answers json)
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}'

    crawled_topics = []  # 已爬取过的话题
    crawled_questions = []  # 已爬取过的问题

    def start_requests(self):
        for url in self.topics:
            yield scrapy.Request(url, dont_filter=True, headers=headers)

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
                if question_url not in self.crawled_questions:
                    self.crawled_questions.append(question_url)
                    yield scrapy.Request(question_url, callback=self.parse_question, headers=headers)
            elif match_topic:
                pass
                topic_url = match_topic.group(1)
                if topic_url not in self.crawled_topics:
                    self.crawled_topics.append(topic_url)
                    yield scrapy.Request(topic_url, callback=self.parse, headers=headers)
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
                             headers=headers)  # 未登录状态无法获取！通过api获取该问题下的答案
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
            yield scrapy.Request(next_url, callback=self.parse_answer, headers=headers)

    # override this method to add login logic before start crawling
    # does not work for 2018 zhihu
    # def start_requests(self):
    #     return [scrapy.Request('https://www.zhihu.com/#signin', callback=self.login, headers=headers)]
    #
    # def login(self, response):
    #     response_text = response.text
    #     match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)  # re默认只对一行进行匹配
    #     xsrf = ''
    #     if match_obj:
    #         xsrf = (match_obj.group(1))
    #     if xsrf:
    #         post_url = "https://www.zhihu.com/login/phone_num"
    #         post_data = {
    #             "_xsrf": xsrf,
    #             "phone_num": "18782902568",
    #             "password": "admin123"
    #         }
    #
    #         return [scrapy.FormRequest(
    #             url=post_url,
    #             formdata=post_data,
    #             headers=headers,
    #             callback=self.check_login
    #         )]
    #
    # def check_login(self, response):
    #     #验证服务器的返回数据判断是否成功
    #     text_json = json.loads(response.text)
    #     if "msg" in text_json and text_json["msg"] == "登录成功":
    #         for url in self.start_urls:
    #             yield scrapy.Request(url, dont_filter=True, headers=self.headers)
