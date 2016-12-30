#!/usr/bin/env python
# coding:utf-8

"""
Created on 20161123
Updated on 20161230

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
    count = 0
    for task in task_list:
        try:
            count += 1
            tmp = task.split("|")
            script_file = tmp[0].strip()
            grinder_threads = tmp[1].strip()
            grinder_duration = tmp[2].strip()
            grinder_runs = tmp[3].strip()
            logging.info("[Task-%d: %s] Performing testing..." % (count, script_file))
            pta_core.perform(script_file, grinder_threads, grinder_duration, grinder_runs)
        except Exception as e:
            logging.exception("Exception occurred when performing task! [%s]" % task)


def work2():
    # #######日志处理生成报告#######
    # 测试执行完成后开始提取测试数据
    logging.info("Collecting testing result...")
    result_dict_list = pta_report.get_testing_result_batch(process_log_dir)
    # 生成html表格测试报告
    logging.info("Generating html report...")
    pta_report.generate_html_report(result_dict_list, process_log_dir, html_report_file_name)
    # 绘制Time-TPS/RT曲线图
    logging.info("Drawing charts...")
    pta_report.draw_chart(result_dict_list, process_log_dir)


def work3():
    # #######发送邮件#######
    mail_receiver_list = ["caojl01@gmail.com", "hzcaojianglong@corp.netease.com", ]
    mail_subject = u"性能测试自动化执行报告"
    # 邮件正文
    content = open(process_log_dir + os.sep + html_report_file_name).read()
    # 邮件图片列表
    image_list = [process_log_dir + os.sep + temp for temp in os.listdir(process_log_dir) if temp.endswith(".png")]
    image_list.sort()
    # 发送邮件
    logging.info("Sending email to %s" % str(mail_receiver_list))
    pta_mail.mail(mail_receiver_list, mail_subject, content, image_list=image_list)


def main():
    work1()
    work2()
    work3()

if __name__ == "__main__":
    main()
