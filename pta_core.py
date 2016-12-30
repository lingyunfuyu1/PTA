#!/usr/bin/python
# coding:utf-8

"""
Created on 20161123
Updated on 20161230

@author: hzcaojianglong
"""
import logging
import os
import socket
import sys

import shutil


class PTACore(object):
    def __init__(self, java_path, grinder_home, grinder_properties_file, process_log_dir):
        """
        构造方法，主要是初始化传入性能测试执行依赖的内容，如java、Grinder等
        :param java_path: 如"/usr/bin/java"、"D:\Program Files\Java\jdk1.7.0_79\bin\java\exe"，如果包含在环境变量PATH中，可直接使用"java"
        :param grinder_home: Grinder的家目录，如"/home/hzcaojianglong/grinder-3.11"，"C:\grinder-3.11"
        :param grinder_properties_file: grinder.properties文件，如"/tmp/PTA/grinder.properties"、"D:\PTA\grinder.properties"
        :param process_log_dir: PTA执行测试生成的日志保存目录，如"/tmp/PTA/log/process_log"、"D:\PTA\log\process_log"
        """
        self.java_path = java_path.strip()
        self.grinder_home = grinder_home.strip()
        self.grinder_properties_file = grinder_properties_file.strip()
        self.process_log_dir = process_log_dir

    def _check_and_prepare(self):
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
            sys.exit(1)
        else:
            self.grinder_home = os.path.abspath(self.grinder_home)
        # grinder_properties_file需要转换为绝对路径
        self.grinder_properties_file = os.path.abspath(self.grinder_properties_file)
        # process_log_dir需要转换为绝对路径
        self.process_log_dir = os.path.abspath(self.process_log_dir)
        logging.debug("The PTA properties file is set to [%s]" % self.process_log_dir)
        if not os.path.exists(self.process_log_dir):
            os.makedirs(self.process_log_dir)
            logging.debug("The PTA log directory is set to [%s]" % self.process_log_dir)
            # logging.info("No such directory! Automatically created. [%s]" % self.process_log_dir)

    def _update_grinder_properties_file(self, script_file, grinder_threads, grinder_duration, grinder_runs):
        """
        更新grinder.properties文件，动态调整本次测试使用的脚本和并发数
        :param script_file: 脚本文件，如"/tmp/PTA/scripts/demo/hello_world.py"、"D:\PTA\scripts\demo\hello_world.py"
        :param grinder_threads: 并发数，正整数，不超过1000（保护客户机安全起见）
        :param grinder_duration: 每个测试执行时长，单位为秒
        :param grinder_runs: 每个线程执行次数
        :return:
        """
        # 检查脚本是否存在
        script_file = script_file.strip()
        if not os.path.exists(script_file):
            logging.error("No such file! [%s]" % script_file)
            sys.exit(1)
        else:
            script_file = os.path.abspath(script_file)
        # 检查属性值是否合理
        properties_dict = {
            "grinder_threads": grinder_threads,
            "grinder_duration": grinder_duration,
            "grinder_runs": grinder_runs,
        }
        for key, value in properties_dict.items():
            if not isinstance(value, int) and not isinstance(value, str):
                logging.error("Not a valid string or integer! [%s=%s]" % (key, value))
                sys.exit(1)
            if isinstance(value, str):
                value = value.strip()
                if not value.isdigit():
                    logging.error("It's not a positive integer! [%s=%s]" % (key, value))
                    sys.exit(1)
            if int(value) < 0:
                logging.error(
                    "The value should not be less than 0! [%s=%s]" % (key, value))
                sys.exit(1)
        if int(grinder_threads) == 0:
            logging.error(
                "The value of grinder_threads should be 0! [grinder_threads=%d]" % int(grinder_threads))
            sys.exit(1)
        if int(grinder_threads) > 1000:
            logging.error(
                "The value of grinder_threads should be <= 1000! [grinder_threads=%d]" % int(grinder_threads))
            sys.exit(1)
        if int(grinder_duration) == 0 and int(grinder_runs) == 0:
            message_info = "The values of grinder_duration and grinder_runs should not be 0 simultaneously!"
            params_info = "[grinder_duration=%s, grinder_runs=%s]" % (grinder_duration, grinder_runs)
            logging.error(message_info + " " + params_info)
            sys.exit(1)
        logging.info("\nscript_file = %s\ngrinder_threads = %s\ngrinder_duration = %s(s)\ngrinder_runs = %s" % (
            script_file, grinder_threads, grinder_duration, grinder_runs))
        # 生成grinder.properties
        result_file = open(self.grinder_properties_file, 'w')
        result_file.write("grinder.useConsole = false\n")
        result_file.write("grinder.logDirectory = %s\n" % self.process_log_dir.replace(os.sep, "/"))
        result_file.write("grinder.numberOfOldLogs = 1\n")
        result_file.write("grinder.script = %s\n" % script_file.replace(os.sep, "/"))
        result_file.write("grinder.processes = 1\n")
        result_file.write("grinder.threads = %s\n" % grinder_threads)
        result_file.write("grinder.duration = %s\n" % str(int(grinder_duration) * 1000))
        result_file.write("grinder.runs = %s\n" % grinder_runs)
        result_file.close()

    def perform(self, script_file, grinder_threads=1, grinder_duration=60, grinder_runs=0, lib_dir="lib"):
        """
        核心方法，传入脚本和并发数进行性能测试。
        :param script_file: 脚本文件，如"/tmp/PTA/scripts/demo/hello_world.py"、"D:\PTA\scripts\demo\hello_world.py"
        :param grinder_threads: 并发数，正整数，不超过1000（保护客户机安全起见）
        :param grinder_duration: 每个测试执行时长，单位为秒
        :param grinder_runs: 每个线程执行次数
        :param lib_dir: 依赖Jar的目录，如"/tmp/PTA/lib"、、"D:\PTA\lib"，可不传，默认为空
        :return:
        """
        self._check_and_prepare()
        self._update_grinder_properties_file(script_file, grinder_threads=grinder_threads,
                                             grinder_duration=grinder_duration, grinder_runs=grinder_runs)
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
        logging.debug("cmd: %s" % cmd)
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
        grinder_data_log_file = self.process_log_dir + os.sep + hostname + "-0-data.log"
        grinder_main_log_file = self.process_log_dir + os.sep + hostname + "-0.log"
        for grinder_log_file in [grinder_data_log_file, grinder_main_log_file]:
            if os.path.exists(grinder_log_file):
                grinder_log_base_name = os.path.basename(grinder_log_file)
                grinder_log_base_name_new = log_file_prefix + "-" + grinder_log_base_name
                grinder_log_base_name_new = grinder_log_base_name_new.replace("-" + hostname + "-0", "")
                # 将主日志文件名后面加-main标记，便于后续判断是否主日志
                if not grinder_log_base_name_new.endswith("-data.log"):
                    grinder_log_base_name_new = os.path.splitext(grinder_log_base_name_new)[0] + "-main.log"
                shutil.move(grinder_log_file, self.process_log_dir + os.sep + grinder_log_base_name_new)
            else:
                logging.warn("No such grinder log file! [%s]" % grinder_log_file)
        logging.info("The testing for %s is completed." % log_file_prefix)


def test():
    pta_core = PTACore("java", "grinder-3.11", "grinder.properties", "log/process_log")
    script_file = "scripts/java/call_java_method_test.py"
    pta_core.perform(script_file, grinder_threads=1, grinder_duration=0, grinder_runs=1, lib_dir="")


if __name__ == "__main__":
    test()
    pass
