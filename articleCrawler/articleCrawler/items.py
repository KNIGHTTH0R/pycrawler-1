# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
import datetime
import re
from articleCrawler.utils.common import extract_num
from articleCrawler.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT


class ArticleItemLoader(ItemLoader):
    # 自定义ItemLoader, 默认输出是取list第一个元素(经默认ItemLoader处理后的item字段全部都是list)
    default_output_processor = TakeFirst()


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums


class JobBoleArticleItem(scrapy.Item):

    def __init__(self):
        self.title = scrapy.Field()
        self.create_date = scrapy.Field(
            input_processor=MapCompose(date_convert)  # using date_convert function map the list items
        )
        self.url = scrapy.Field()
        self.url_object_id = scrapy.Field()
        self.front_image_url = scrapy.Field(
            output_processor=MapCompose(lambda i: i)  # 覆盖默认的output_processor，因为本来就是需要list
        )
        self.front_image_path = scrapy.Field()
        self.vote_up_nums = scrapy.Field(
            input_processor=MapCompose(get_nums)  # MapCompose返回list, 因此default_output_processor=TakeFirst 而不是input
        )
        self.fav_nums = scrapy.Field(
            input_processor=MapCompose(get_nums)
        )
        self.comment_nums = scrapy.Field(
            input_processor=MapCompose(get_nums)
        )
        self.content = scrapy.Field()
        self.tags = scrapy.Field(
            input_processor=MapCompose(self.remove_comment_tags),
            output_processor=Join(",")
        )

    def get_insert_sql(self):
        insert_sql = """
                        insert into jobbole_article(title, url, url_object_id, create_date, fav_nums, tags)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
        params = (self["title"], self["url"], self["url_object_id"], self["create_date"],
                  self["fav_nums"], self["tags"])
        return insert_sql, params

    def remove_comment_tags(value):
        # 去掉tag中提取的评论
        if "评论" in value:
            return ""
        else:
            return value


class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num,
                      watch_user_num, click_num, crawl_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY 
                    update content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
              watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
                    """
        zhihu_id = self['zhihu_id'][0]
        topics = ','.join(self['topics'])
        title = ''.join(self['title'])
        url = ''.join(self['url'])
        content = ''.join(self['content'])
        answer_num = extract_num(''.join(self['answer_num']))
        comments_num = extract_num(''.join(self['comments_num']))
        watch_user_num = int(self['watch_user_num'][0].replace(',', ''))
        click_num = int(self['watch_user_num'][1].replace(',', ''))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num,
                  watch_user_num, click_num, crawl_time)
        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    # 知乎的问题回答item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    parise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, parise_num, comments_num,
              create_time, update_time, crawl_time
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY 
              update content=VALUES(content), comments_num=VALUES(comments_num), parise_num=VALUES(parise_num),
              update_time=VALUES(update_time)
                    """
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self['update_time']).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["parise_num"],
            self["comments_num"], create_time, update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )
        return insert_sql, params