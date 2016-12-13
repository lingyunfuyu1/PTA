# coding:utf-8

"""
Created on 2016年5月21日
@author: hzcaojianglong
"""

# 一般无需修改
from net.grinder.script import Test
from net.grinder.script.Grinder import grinder
from net.grinder.plugin.http import HTTPRequest
from HTTPClient import NVPair
from java.util.concurrent.atomic import AtomicInteger
import time

TEST_ID = 2
TEST_NAME = 'http_post_test'

ISOTIMEFORMAT = '%Y-%m-%d %X'

# post数据要注意确认是否可以复用，测试数据要足够多，不然会从头开始用
processNum = int(grinder.getProperties().get('grinder.processes'))
threadNum = int(grinder.getProperties().get('grinder.threads'))

ERR_LOG = 'err.log'
logfile = open(ERR_LOG, 'w')
is_open = AtomicInteger(int(grinder.getProperties().get('grinder.threads')))

param_file = "http_post_test.txt"
infile = open(param_file, 'r')
keyword_list = []
for line in infile.readlines():
    keyword_list.append(line.strip())
infile.close()

url = 'https://www.google.com.hk'
# 只设置Content-Type即可
headers = [
    NVPair('Host', 'www.google.com.hk'),
    NVPair('Connection', 'keep-alive'),
    NVPair('Origin', 'https://www.google.com.hk'),
    NVPair('User-Agent',
           'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'),
    NVPair('Content-Type', 'application/x-www-form-urlencoded;charset=UTF-8'),
    NVPair('Accept', '*/*'),
    NVPair('X-Client-Data', 'CJK2yQEIo7bJAQjBtskBCP2VygEI8JjKAQjunMoB'),
    NVPair('DNT', '1'),
    NVPair('Referer', 'https://www.google.com.hk/'),
    # # 支持的编码类型去掉gzip，否则需要解压缩得到文本
    NVPair('Accept-Encoding', 'deflate'),
    NVPair('Accept-Language', 'zh-CN,zh;q=0.8'),
    # NVPair('Cookie', 'NID=79=OGqTd5oclNAe_E1GdFbfurmSSp0Rm9GlUOsUm7zFcAMX17Hq0aQ2MVTc2NAGN46WsdvKFPOZxSxX7RpRBhWFydQPKYInp2AzgJp7Xx9SwdIEZq2uCzyOoTuJAwuhy5h1; DV=wiQ6QbW_7QM27L5WAuXZL-8emDPCqRJx7Qra6YuOKgAAAHTzw4IiNVMlGUIBAA'),
    # NVPair('Content-Length', '99'), 
]
request = HTTPRequest(url=url, headers=headers)


class TestRunner:
    """A TestRunner instance is created for each worker thread."""

    def __init__(self):
        pass

    def getParam(self, keyword):
        param = "async=translate,sl:en,tl:zh-CN,st:" + keyword + ",id:1464065770244,_id:tw-async-translate,_pms:s"
        return param

    def sendRequest(self, param):
        """A method is called for each recorded page."""
        # print url + param
        response = request.POST(
            '/async/translate?vet=10ahUKEwjKntXo1vHMAhUKH5QKHU2DDoQQqDgIJzAA..i&ei=Nb5DV4qwBIq-0ATNhrqgCA&yv=2', param)
        code = response.getStatusCode()
        print "code:", code
        data = response.getText().encode('utf-8')
        print "data:", data
        if code != 200 or data.find('tw-async-translate') == -1:
            info = time.strftime(ISOTIMEFORMAT,
                                 time.localtime(time.time())) + ' Test:' + TEST_NAME + ' [[]] Param:' + param.encode(
                'utf-8') + ' [[]] StatusCode:' + str(
                code) + ' [[]] Content:' + data
            logfile.write(info + '\n')
            grinder.getStatistics().getForCurrentTest().setSuccess(False)

    request1 = Test(TEST_ID, TEST_NAME).wrap(sendRequest)

    def initialSleep(self):
        sleepTime = grinder.threadNumber * 100
        grinder.sleep(sleepTime, 0)

    def __call__(self):
        """This method is called for every run performed by the worker thread."""
        if grinder.runNumber == 0: self.initialSleep()
        idx = (processNum * threadNum * grinder.getRunNumber() + \
               threadNum * grinder.getProcessNumber() + \
               grinder.getThreadNumber()) % len(keyword_list)
        keyword = keyword_list[idx]
        param = self.getParam(keyword)
        self.request1(param)

    def __del__(self):
        if is_open.decrementAndGet() == 0:
            logfile.close()
