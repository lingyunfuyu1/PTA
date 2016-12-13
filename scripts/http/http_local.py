# coding:utf-8

"""
Created on 2016年5月21日
@author: hzcaojianglong
"""

# 导入需要的模块，可以导入Java类作为Python模块
from net.grinder.script import Test
from net.grinder.script.Grinder import grinder
from net.grinder.plugin.http import HTTPRequest
from HTTPClient import NVPair
from java.util import Random
from java.util.concurrent.atomic import AtomicInteger
import time

# 修改测试编号和名称，编号用于混合场景测试区分
TEST_ID = 1
TEST_NAME = 'http_get_test'

# 设置时间格式为yyyy-mm-dd hh24:mi:ss
ISOTIMEFORMAT = '%Y-%m-%d %X'

# 根据实际情况选择方案1或2，可以重复利用的测试数据可以选择1或者2，不可重复利用的测试数据选择2。
# 方案1
random = Random()
# 方案2
# processNum = int(grinder.getProperties().get('grinder.processes'))
# threadNum = int(grinder.getProperties().get('grinder.threads'))

# 一般无需修改
ERR_LOG = 'err.log'
logfile = open(ERR_LOG, 'w')
is_open = AtomicInteger(int(grinder.getProperties().get('grinder.threads')))


# 可能需要修改url和headers等值
url = 'http://localhost:7070'
headers = [NVPair('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')]
request = HTTPRequest(url=url, headers=headers)


class TestRunner:
    """A TestRunner instance is created for each worker thread."""
    
    # 构造方法
    def __init__(self):
        pass

    # 发送请求
    def sendRequest(self):
        """A method is called for each recorded page."""
        # print url
        time.sleep(0.4)
        response = request.GET(url)
        code = response.getStatusCode()
        print "code:", code
        data = response.getText().encode('utf-8')
        # print "data:", type(data)
        if code != 200 or data.find('Apache Tomcat') == -1:
            info = time.strftime(ISOTIMEFORMAT,
                                 time.localtime(time.time())) + ' Test:' + TEST_NAME + ' [[]] StatusCode:' + str(
                code) + ' [[]] Content:' + data
            logfile.write(info + '\n')
            grinder.getStatistics().getForCurrentTest().setSuccess(False)

    # 一般无需修改
    request1 = Test(TEST_ID, TEST_NAME).wrap(sendRequest)

    # 初始化休眠
    def initialSleep(self):
        sleepTime = grinder.threadNumber * 100
        grinder.sleep(sleepTime, 0)

    # 入口方法
    def __call__(self):
        """This method is called for every run performed by the worker thread."""
        if grinder.runNumber == 0: self.initialSleep()
        self.request1()

    # 析构方法
    def __del__(self):
        if is_open.decrementAndGet() == 0:
            logfile.close()
