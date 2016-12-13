#!/usr/bin/python
# coding:utf-8

"""
Created on 2016年11月23日

@author: hzcaojianglong
"""
import logging
import os
import re
import socket
import sys

import shutil


class PTACore(object):
    def __init__(self, java_path, grinder_home, grinder_properties_file):
        """
        构造方法，主要是初始化传入性能测试执行依赖的内容，如java、Grinder等
        :param java_path: 如"/usr/bin/java"、"D:\Program Files\Java\jdk1.7.0_79\bin\java\exe"，如果包含在环境变量PATH中，可直接使用"java"
        :param grinder_home: Grinder的家目录，如"/home/hzcaojianglong/grinder-3.11"，"C:\grinder-3.11"
        :param grinder_properties_file: grinder.properties文件，如"/tmp/PTA/grinder.properties"、"D:\PTA\grinder.properties"
        """
        self.java_path = java_path.strip()
        self.grinder_home = grinder_home.strip()
        self.grinder_properties_file = grinder_properties_file.strip()

    def self_check(self):
        """
        对各个实例变量进行检查，判断是否可用，所需依赖是否满足
        :return:
        """
        # 检查指定的java是否可用
        if self.java_path != "java":
            if not os.path.exists(self.java_path):
                logging.error("No such directory! [%s]" % self.java_path)
                sys.exit(1)
            else:
                self.java_path = os.path.abspath(self.java_path)
                self.java_path = '"' + self.java_path + '"'
        if os.name == "nt":
            null_device = "nul"
        elif os.name == "posix":
            null_device = "/dev/null"
        else:
            logging.error("This platform is not supported! [%s]" % os.name)
            sys.exit(1)
        if os.system('"' + self.java_path + '"' + ' -version >' + null_device + ' 2>' + null_device) != 0:
            logging.error("The specified java is not available! [%s]" % self.java_path)
            sys.exit(1)
        # 检查Grinder是否可用
        if not os.path.exists(self.grinder_home + os.sep + "lib" + os.sep + "grinder.jar"):
            logging.error("No such directory! [%s]" % self.grinder_home)
            sys.exit(2)
        else:
            self.grinder_home = os.path.abspath(self.grinder_home)
        # 检查grinder_properties_file是否存在
        if not os.path.exists(self.grinder_properties_file):
            logging.error("No such file! [%s]" % self.grinder_properties_file)
            sys.exit(3)
        else:
            self.grinder_properties_file = os.path.abspath(self.grinder_properties_file)

    def _update_grinder_properties_file(self, script_file, vuser_number):
        """
        更新grinder.properties文件，动态调整本次测试使用的脚本和并发数
        :param script_file: 脚本文件，如"/tmp/PTA/scripts/demo/hello_world.py"、"D:\PTA\scripts\demo\hello_world.py"
        :param vuser_number: 并发数，正整数，不超过1000（保护客户机安全起见）
        :return:
        """
        # 检查脚本是否存在
        script_file = script_file.strip()
        if not os.path.exists(script_file):
            logging.error("No such file! [%s]" % script_file)
            sys.exit(4)
        else:
            script_file = os.path.abspath(script_file)
        # 检查并发数是否合理
        if not isinstance(vuser_number, int) and not isinstance(vuser_number, str):
            logging.error("Not a valid string or integer! [%s]" % vuser_number)
            sys.exit(4)
        if isinstance(vuser_number, str):
            vuser_number = vuser_number.strip()
            if not vuser_number.isdigit():
                logging.error("It's not a positive integer! [%s]" % vuser_number)
                sys.exit(4)
        if int(vuser_number) <= 0 or int(vuser_number) > 1000:
            logging.error("The value of vuser_number should be 0<vuser_number<=1000! [%d]" % int(vuser_number))
            sys.exit(4)
        # 修改grinder.properties
        script_line = re.compile(r'grinder.scr(.*?)\n')
        script_new = "ipt = " + script_file.replace(os.sep, "/")
        vuser_number_line = re.compile(r'[^G]grinder.thre(.*?)\n')
        vuser_number_new = "ads = " + str(vuser_number)
        property_update_dict = {script_line: script_new, vuser_number_line: vuser_number_new}
        content = open(self.grinder_properties_file, 'r').read()
        for pattern, value_new in property_update_dict.items():
            if not pattern.search(content):
                logging.error("No such property_line in grinder.properties! [%s]" % pattern)
                sys.exit(5)
            value_old = pattern.findall(content)[0]
            logging.info("The old value is %s" % value_old)
            logging.info("The new value is %s" % value_new)
            content = content.replace(value_old, value_new)
        with open(self.grinder_properties_file, 'w') as result_file:
            result_file.write(content)

    def perform(self, script_file, vuser_number, lib_dir=""):
        """
        核心方法，传入脚本和并发数进行性能测试。
        :param script_file: 脚本文件，如"/tmp/PTA/scripts/demo/hello_world.py"、"D:\PTA\scripts\demo\hello_world.py"
        :param vuser_number: 并发数，正整数，不超过1000（保护客户机安全起见）
        :param lib_dir: 依赖Jar的目录，如"/tmp/PTA/lib"、、"D:\PTA\lib"，可不传，默认为空
        :return:
        """
        self._update_grinder_properties_file(script_file, vuser_number)
        # 检查依赖Jar目录是否存在，不存在后续使用时不影响
        lib_dir = lib_dir.strip()
        if lib_dir:
            if os.path.exists(lib_dir):
                lib_dir = os.path.abspath(lib_dir)
            else:
                logging.warn("No such directory! [%s]" % lib_dir)
        # 构造java命令并执行
        if os.name == "nt":
            split_symbol = ";"
        elif os.name == "posix":
            split_symbol = ":"
        else:
            logging.error("This platform is not supported! [%s]" % os.name)
            sys.exit(1)
        logging.info("-------%s-------" % script_file)
        # 构造CLASSPATH
        classpath = '".' + split_symbol
        script_dir = os.path.abspath(os.path.dirname(script_file))
        for temp_path in [script_dir, lib_dir, self.grinder_home + os.sep + "lib"]:
            if os.path.exists(temp_path):
                # 增加辅助jar，避免jar目录为空时报错
                temp_file = open(os.sep.join([temp_path, "testcaojl.jar"]), 'w')
                temp_file.write("This a assistant jar file which ensures the lib direcotry is not empty.")
                temp_file.close()
                classpath += temp_path + os.sep + "*" + split_symbol
        classpath += '"'
        # 构造命令并执行
        if os.name == "nt":
            cmd = 'call ' + self.java_path + ' -cp ' + classpath + ' net.grinder.Grinder ' + self.grinder_properties_file
        elif os.name == "posix":
            cmd = self.java_path + ' -cp ' + classpath + ' net.grinder.Grinder ' + self.grinder_properties_file
        else:
            logging.error("This platform is not supported! [%s]" % os.name)
            sys.exit(1)
        logging.info("cmd: %s" % cmd)
        work_dir = os.getcwd()
        os.chdir(script_dir)
        os.system(cmd)
        os.chdir(work_dir)
        # 清理辅助Jar文件
        for jar_path in classpath.split(split_symbol):
            if jar_path.endswith("*"):
                jar_path = jar_path.replace("*", "testcaojl.jar")
                os.remove(jar_path)
        # 将Grinder产生的运行日志重命名，增加脚本名作前缀标识符
        hostname = socket.gethostname()
        log_file_prefix = os.path.splitext(os.path.basename(script_file))[0]
        grinder_data_log_file = script_dir + os.sep + "log" + os.sep + hostname + "-0-data.log"
        grinder_main_log_file = script_dir + os.sep + "log" + os.sep + hostname + "-0.log"
        for grinder_log_file in [grinder_data_log_file, grinder_main_log_file]:
            if os.path.exists(grinder_log_file):
                grinder_log_dir_name = os.path.dirname(grinder_log_file)
                grinder_log_base_name = os.path.basename(grinder_log_file)
                grinder_log_base_name_new = log_file_prefix + "-" + grinder_log_base_name
                shutil.move(grinder_log_file, grinder_log_dir_name + os.sep + grinder_log_base_name_new)
            else:
                logging.warn("No such grinder log file! [%s]" % grinder_log_file)


def test():
    pta_core = PTACore("java", "C:\grinder-3.11", "C:\grinder-3.11\examples\grinder.properties")
    pta_core.perform("F:\caojl-log\java\call_java_method_test.py", 3, "F:\caojl-log\lib")


if __name__ == "__main__":
    # test()
    pass
