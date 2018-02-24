# -*- coding: utf-8 -*-

# Define your item pipelines here
# item will flow through every pipeline setting in the settings.py
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
import codecs
from articleCrawler.utils.common import get_project_dir
import json
from scrapy.exporters import JsonItemExporter
import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi


class ArticlecrawlerPipeline(object):
    def process_item(self, item, spider):
        return item


class MySQLPipeline(object):

    def __init__(self):
        self.conn = MySQLdb.connect(host="127.0.0.1", user="root", password="23456", database="pycrawler",
                                    charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(title, url, url_object_id, create_date, fav_nums, tags)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql,
                            (item["title"], item["url"], item["url_object_id"], item["create_date"], item["fav_nums"],
                             item["tags"]))
        self.conn.commit()

    def spider_closed(self, spider):
        self.conn.close()

    # twisted提供的异步数据库操作


class MysqlTwistedPipeline(object):

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod  # another constructor   instance = clazz.from_settings
    def from_settings(cls, settings):
        params = dict(
            host=settings["MYSQL_HOST"],
            database=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            password=settings["MYSQL_PASSWORD"],
            charset="utf8",
            use_unicode=True,
            cursorclass=MySQLdb.cursors.DictCursor
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **params)  # !!!
        return cls(dbpool)  # __init__(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)
        return item

    def do_insert(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)

    def handle_error(self, failure, item, spider):
        # 处理异步操作过程中发生的异常
        print(failure)


class JsonWithEncodingPipeline(object):
    # 自定义的json导出
    def __init__(self):
        self.file = codecs.open(get_project_dir() + '\\json\\article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"  # 并不确保是ascii
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    # 使用scrapy提供的json导出... 还有CsvItemExporter, XmlItemExporter....
    def __init__(self):
        self.file = codecs.open(get_project_dir() + '\\json\\article_exporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()  # self.file.write(b"[")

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def spider_closed(self, spider):
        self.exporter.finish_exporting()  # self.file.write(b"]")
        self.file.close()


class ArticleImagePipeline(ImagesPipeline):
    # results : [(ok, dict),....]
    def item_completed(self, results, item, info):
        if "front_image_path" in item:
            for ok, value in results:
                image_file_path = value["path"]
                item["front_image_path"] = image_file_path
        return item
