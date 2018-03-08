# -*- coding: utf-8 -*-
__author__ = 'bobby'

from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, Completion, Keyword, Text, Integer
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=["localhost"])


# 直接使用Completion(analyzer="ik_max_word")会报错
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])


class JobboleArticleType(DocType):
    # 搜索建议(关键词联想)
    suggestion = Completion(analyzer=ik_analyzer)

    title = Text(analyzer="ik_max_word")  # analyze this text (分词..
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    vote_up_nums = Integer()
    fav_nums = Integer()
    comment_nums = Integer()
    content = Text(analyzer="ik_smart")
    tags = Text(analyzer="ik_smart")

    class Meta:
        index = "jobbole"  # just like database
        doc_type = "article"  # like table


# 直接在elasticsearch上生成字段对应的mapping
if __name__ == "__main__":
    JobboleArticleType.init()
