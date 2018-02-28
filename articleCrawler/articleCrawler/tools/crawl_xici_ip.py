import requests
from scrapy.selector import Selector
import MySQLdb

conn = MySQLdb.connect(host='127.0.0.1', user='root', password='23456', database='pycrawler', charset='utf8')
cursor = conn.cursor()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'
}

def crawl_ips():
    ip_list = []
    # page: 1 - 2734
    for page in range(1, 10):
        resp = requests.get('http://www.xicidaili.com/nn/{0}'.format(page), headers=headers)
        selector = Selector(text=resp.text)
        all_trs = selector.css('#ip_list tr')
        for tr in all_trs[1:]:
            speed = tr.css('.bar::attr(title)').extract_first('')
            if speed:
                speed = float(speed.replace('秒', ''))
            all_tdtext = tr.css('td::text').extract()
            ip = all_tdtext[0]
            port = all_tdtext[1]
            proxy_type = all_tdtext[5]
            ip_list.append((ip, port, speed, proxy_type))

    for ip_info in ip_list:
        cursor.execute("insert into proxy_ip(ip,port,speed,proxy_type) VALUES('{0}','{1}',{2},'{3}') "
                       "ON DUPLICATE KEY UPDATE port=VALUES(port), speed=VALUES(speed)"
                       .format(ip_info[0], ip_info[1], ip_info[2], ip_info[3])
                       )
        conn.commit()
    conn.close()

class GetIP(object):
    # 获取随机ip
    def get_random_ip(self):
        # 这样做效率比较慢，因为要先排序
        # 可以先select count(*)得到总数n，再由后台产生随机数rn(1-n)，然后select .. limit rn,1
        sql = """
            select ip,port,proxy_type,speed from proxy_ip
            ORDER BY RAND()
            limit 1
        """
        attempt_times = 0
        while attempt_times < 20:
            result = cursor.execute(sql)
            ip_info = cursor.fetchone()
            ip = ip_info[0]
            port = ip_info[1]
            proxy_type = ip_info[2].lower()
            speed = ip_info[3]
            if self.judge(ip, port, speed, proxy_type):
                return '{0}://{1}:{2}'.format(proxy_type, ip, port)
            else:
                attempt_times += 1
        return None

    def judge(self, ip, port, speed, proxy_type):
        if speed < 3:
            print("slow ip:{0}".format(ip))
            return False
        http_url = '{0}://www.baidu.com'.format(proxy_type)
        proxy_url = '{0}://{1}:{2}'.format(proxy_type, ip, port)
        if not proxy_type:
            return False
        proxy_dict = {
            # "http": proxy_url,
            proxy_type: proxy_url
        }
        try:
            resp = requests.get(http_url, proxies=proxy_dict, headers=headers)
        except Exception as e:
            print("invalid ip:{0}".format(ip))
            self.delete_ip(ip)
            return False
        else:
            code = resp.status_code
            if code >= 200 and code < 300:
                print("effective ip:{0}".format(ip))
                return True
            else:
                print("invalid ip:{0}".format(ip))
                self.delete_ip(ip)
                return False

    def delete_ip(self, ip):
        # delete invalid ip
        try:
            delete_sql = """
                delete from proxy_ip where ip='{0}'
            """.format(ip)
            cursor.execute(delete_sql)
            conn.commit()
            return True
        except:
            return False

# get_ip = GetIP()
# print("random ip:", get_ip.get_random_ip())
# # crawl_ips()
