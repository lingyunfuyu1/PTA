# coding:utf-8

"""
Created on 2016年5月22日
@author: hzcaojianglong
"""

from net.grinder.script import Test
from net.grinder.script.Grinder import grinder
from java.util import Random
from java.util.concurrent.atomic import AtomicInteger
from org.caojl.xh.app import App
import random
import time

TEST_ID = 1
TEST_NAME = 'call_java_method_test'

ISOTIMEFORMAT = '%Y-%m-%d %X'
number_list = [1, 2, 3, 4, 5, 6, 7]

ERR_LOG = 'err.log'
logfile = open(ERR_LOG, 'w')
is_open = AtomicInteger(int(grinder.getProperties().get('grinder.threads')))


class TestRunner:
    """A TestRunner instance is created for each worker thread."""

    def __init__(self):
        self.app = App()

    def getParam(self):
        fir_idx = random.randint(0, len(number_list) - 1)
        param1 = number_list[fir_idx]
        sec_idx = random.randint(0, len(number_list) - 1)
        param2 = number_list[sec_idx]
        param = [param1, param2]
        return param

    def sendRequest(self, param1, param2):
        """A method is called for each recorded page."""
        time.sleep(random.randint(70, 110) / 1000.0)
        print param1, param2
        result = self.app.callAdd(param1, param2)
        print "result:", result
        # 注意param1和param2都是int类型，需要转换成str
        if result.find(str(param1) + ' + ' + str(param2)) == -1:
            print 'Failed!'
            info = time.strftime(ISOTIMEFORMAT,
                                 time.localtime(time.time())) + ' Test:' + TEST_NAME + ' [[]] Params:' + str(param1) + \
                   ',' + str(param2) + ' [[]] Result:' + result
            logfile.write(info + '\n')
            grinder.getStatistics().getForCurrentTest().setSuccess(False)

    request1 = Test(TEST_ID, TEST_NAME).wrap(sendRequest)

    def initialSleep(self):
        sleepTime = grinder.threadNumber * 100
        grinder.sleep(sleepTime, 0)

    def __call__(self):
        """This method is called for every run performed by the worker thread."""
        if grinder.runNumber == 0: self.initialSleep()
        (param1, param2) = self.getParam()
        self.request1(param1, param2)

    def __del__(self):
        if is_open.decrementAndGet() == 0:
            logfile.close()
