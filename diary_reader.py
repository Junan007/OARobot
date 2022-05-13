import requests
import json
import datetime
from dateutil.parser import parse


class DiaryReader(object):
    __host__ = 'https://api.notion.com'

    def __init__(self, api_key, database_id) -> None:
        self.api_key = api_key
        self.database_id = database_id
    
    def init_header(self, content_type=None):
        headers = {"Authorization": "Bearer " + self.api_key,
                   "Notion-Version": "2021-08-16"}

        if content_type is not None:
            headers.update({"Content-Type": content_type})

        return headers
    
    def do_post(self, url, data):
        headers = self.init_header(content_type="application/json")
        rsp = requests.post(url, headers=headers, json=data)
        if rsp.status_code != 200:
            print('Get Notion data error:', rsp.text)
            return None

        obj = json.loads(rsp.text)
        return obj
    
    def get_node_property_text(self, node, property_name, type_name='rich_text'):
        property_node = node['properties'][property_name][type_name]
        return self.get_node_text(property_node)
    
    @staticmethod
    def get_node_text(node):
        if len(node) > 0:
            return node[0]['plain_text']
        else:
            return None
    
    @staticmethod
    def get_today_str():
        d = datetime.date.today()
        return d.isoformat()
    
    @staticmethod
    def to_isoformat(date_str):
        d = parse(date_str)
        return d.date().isoformat()

    def get_recent_diary(self, find_date=None):
        url = '{}/v1/databases/{}/query'.format(self.__host__, self.database_id)
        all_report = self.do_post(url, {})
        if all_report['object'] != 'list':
            raise Exception("Object type error!")
        
        if find_date is None:
            find_date = self.get_today_str()
        
        for idx, report_page in enumerate(all_report['results']):
            page_id = report_page['id']
            
            date_str = self.get_node_property_text(report_page, 'Date', 'title')
            if date_str is None:
                continue
            
            date_str = self.to_isoformat(date_str)
            if date_str == find_date:
                today_finished = self.get_node_property_text(report_page, 'Today Finished')
                torrow_plan = self.get_node_property_text(report_page, 'Torrow Plan')
                today_summary = self.get_node_property_text(report_page, 'Today Summary')

                return date_str, today_finished, torrow_plan, today_summary        
        return None, None, None, None
