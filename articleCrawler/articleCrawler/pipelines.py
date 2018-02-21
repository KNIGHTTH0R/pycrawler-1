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


class ArticlecrawlerPipeline(object):
    def process_item(self, item, spider):
        return item


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
        for ok, value in results:
            image_file_path = value["path"]
            item["front_image_url_path"] = image_file_path
        return item
