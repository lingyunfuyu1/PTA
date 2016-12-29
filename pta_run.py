#!/usr/bin/env python
# coding:utf-8

"""
Created on 2016年11月23日

@author: hzcaojianglong
"""
import logging
import os

from pta_core import PTACore
import pta_mail
import pta_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s(%(lineno)d): %(funcName)s] PID-%(process)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=os.getcwd() + os.sep + "pta.log",
    filemode="a")
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s]  PID-%(process)d  %(funcName)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


def work1(java_path, grinder_home, grinder_properties_file, log_dir, lib_dir, task_list):
    # 初始化实例
    pta_core = PTACore(java_path, grinder_home, grinder_properties_file, log_dir)

    # 准备测试任务，格式为"脚本|并发数|测试时间|测试次数"，串行执行测试
    for index in range(len(task_list)):
        try:
            script_file = task_list[index].split("|")[0]
            grinder_threads = task_list[index].split("|")[1]
            grinder_duration = task_list[index].split("|")[2]
            grinder_runs = task_list[index].split("|")[3]
            logging.info("Task %d: script_file=%s, grinder_threads=%s, grinder_duration=%s(s), grinder_runs=%s" % (
                index + 1, script_file, grinder_threads, grinder_duration, grinder_runs))
            pta_core.perform(script_file, grinder_threads, grinder_duration, grinder_runs, lib_dir)
        except Exception as e:
            logging.exception("Exception occurred when performing task! [%s]" % task_list[index])

# 日志目录
log_dir = "log"
# 过程日志目录
process_log_dir = log_dir + os.sep + "process_log"
# 归档日志目录
archive_log_dir = log_dir + os.sep + "archive_log"
# 测试任务获取
task_file = "task_list.txt"
task_list = []
for line in open(task_file):
    line = line.strip()
    if not line.startswith("#"):
        task_list.append(line)
# html表格测试报告名称
html_report_file_name = "performance_testing.html"


def work1():
    # #######性能测试自动化执行#######
    # 备份历史日志
    pta_report.log_file_backup(archive_log_dir, process_log_dir)
    # 初始化一个PTACore实例
    pta_core = PTACore("java", "grinder-3.11", "grinder.properties", process_log_dir)
    # 执行测试任务
    if not task_list:
        logging.error("No tasks! Please check the task file. [%s]" % task_file)
    for task in task_list:
        try:
            tmp = task.split("|")
            script_file = tmp[0].strip()
            grinder_threads = tmp[1].strip()
            grinder_duration = tmp[2].strip()
            grinder_runs = tmp[3].strip()
            pta_core.perform(script_file, grinder_threads, grinder_duration, grinder_runs)
        except Exception as e:
            logging.exception("Exception occurred when performing task! [%s]" % task)


def work2():
    # #######日志处理生成报告#######
    # 测试执行完成后开始提取测试数据
    result_dict_list = pta_report.get_testing_result_batch(process_log_dir)
    # 生成html表格测试报告
    pta_report.generate_html_report(result_dict_list, process_log_dir, html_report_file_name)
    # 绘制Time-TPS/RT曲线图
    pta_report.draw_chart(result_dict_list, process_log_dir)


def work3():
    # #######发送邮件#######
    mail_receiver_list = ["caojl01@gmail.com", ]
    mail_subject = u"性能测试自动化执行报告"
    # 邮件正文
    content = open(process_log_dir + os.sep + html_report_file_name).read()
    # 邮件图片列表
    image_list = [process_log_dir + os.sep + temp for temp in os.listdir(process_log_dir) if temp.endswith(".png")]
    image_list.sort()
    # 发送邮件
    pta_mail.mail(mail_receiver_list, mail_subject, content, image_list=image_list)


def main():
    work1()
    work2()
    work3()

if __name__ == "__main__":
    main()
