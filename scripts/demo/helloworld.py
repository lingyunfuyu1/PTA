# Hello World
#
# A minimal script that tests The Grinder logging facility.
#
# This script shows the recommended style for scripts, with a
# TestRunner class. The script is executed just once by each worker
# process and defines the TestRunner class. The Grinder creates an
# instance of TestRunner for each worker thread, and repeatedly calls
# the instance for each run of that thread.

from net.grinder.script.Grinder import grinder
from net.grinder.script import Test
import random
import time

# A shorter alias for the grinder.logger.info() method.
log = grinder.logger.info

# Create a Test with a test number and a description. The test will be
# automatically registered with The Grinder console if you are using
# it.
test1 = Test(1, "Hello World")

# A TestRunner instance is created for each thread. It can be used to
# store thread-specific data.
class TestRunner:

    def fun1(self):
        time.sleep(random.randint(700, 1100) / 1000.0)
        print "Hello, hzcaojianglong!"
        log("Hello, Grinder!")

    # This method is called for every run.
    def __call__(self):
        self.fun1()

# Instrument the info() method with our Test.
test1.record(TestRunner.fun1)
