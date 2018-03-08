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
from w3lib.html import remove_tags
import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerDoc, Completion, Keyword, Text, Integer
from articleCrawler.models.es_types import JobboleArticleType


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

def remove_comment_tags(value):
    # 去掉tag中提取的评论
    if "评论" in value:
        return ""
    else:
        return value

from elasticsearch_dsl.connections import connections
# using xxxType to create a connection associated with this xxxType thing
es = connections.create_connection(JobboleArticleType._doc_type.using)
def gen_suggests(index, info_tuple):
    # generate searching suggestions using corresponding info_tuple(text, weight)
    used_word = set()
    suggestions = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, body=text, params={'analyzer':'ik_max_word', 'filter': ["lowercase"]} )
            analyzed_words = set([ w['token'] for w in words['tokens'] if len(w['token']) > 1 ])
            new_words = analyzed_words - used_word
        else:
            new_words = set()

        suggestions.append({"input":list(new_words), "weight":weight})
    return suggestions


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(lambda i: i)
    )
    front_image_path = scrapy.Field()
    vote_up_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field()

    # save item to elasticsearch engine
    def save_to_es(self):
        article = JobboleArticleType()
        article.title = self['title']
        article.create_date = self['create_date']
        article.content = remove_tags(self['content'])
        if "front_image_path" in self:
            article.front_image_url = self['front_image_url']
            article.front_image_path = self['front_image_path']
        article.vote_up_nums = self['vote_up_nums']
        article.fav_nums = self['fav_nums']
        article.comment_nums = self['comment_nums']
        article.url = self['url']
        article.tags = self['tags']
        article.meta.id = self['url_object_id']

        # 生成该文章的搜索建议
        article.suggestion = gen_suggests(JobboleArticleType._doc_type.index, ((article.title,20),(article.tags,10)))
        article.save()

    def get_insert_sql(self):
        insert_sql = """
                        insert into jobbole_article(title, url, url_object_id, create_date, fav_nums, tags)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY update title=VALUES(title), url=VALUES(url), fav_nums=VALUES(fav_nums), tags=VALUES(tags)
                    """
        params = (self["title"], self["url"], self["url_object_id"], self["create_date"],
                  self["fav_nums"], self["tags"])
        return insert_sql, params



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


class LagouJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


def replace_splash(val):
    return val.replace('/', '')


def handle_jobaddr(val):
    addrlist = val.split('\n')
    addrlist = [addr.strip() for addr in addrlist if addr != "查看地图"]
    return ''.join(addrlist)


class LagouJobItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(replace_splash)
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    tags = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(
        input_processor=MapCompose(lambda x: x.strip()),
    )
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr)
    )
    company_name = scrapy.Field(
        input_processor=MapCompose(lambda x: x.strip()),
    )
    company_url = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_job(title, url, salary, job_city, work_years, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_url, company_name, job_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_desc=VALUES(job_desc)
        """

        job_id = extract_num(self["url"])
        params = (self["title"], self["url"], self["salary"], self["job_city"], self["work_years"], self["degree_need"],
                  self["job_type"], self["publish_time"], self["job_advantage"], self["job_desc"], self["job_addr"],
                  self["company_url"],
                  self["company_name"], job_id)

        return insert_sql, params
