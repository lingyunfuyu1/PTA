#!/usr/bin/python
# coding:utf-8

"""
Created on 2016年11月23日

@author: hzcaojianglong
"""
import logging
import os

from pta_core import PTACore
from pta_mail import mail
from pta_report import log_file_backup, log_file_collect, get_testing_data, generate_html_report, draw_chart

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


def work1(task_list):
    # 初始化准备
    java_path = "java"
    grinder_home = "grinder-3.11"
    # TODO：依赖grinder.properties，内容必须是原版的，否则有风险（注意grinder.logDirectory、grinder.processes、grinder.runs、grinder.duration要初始化配置好）
    grinder_properties_file = "grinder.properties"
    lib_dir = "lib"
    # 初始化实例
    pta_core = PTACore(java_path, grinder_home, grinder_properties_file)
    # 程序依赖可用性检查
    pta_core.self_check()

    # 准备测试任务，格式为"脚本|并发数"，串行执行测试
    for index in range(len(task_list)):
        try:
            script_file = task_list[index].split("|")[0]
            vuser_number = task_list[index].split("|")[1]
            pta_core.perform(script_file, vuser_number, lib_dir)
        except Exception as e:
            logging.exception("Exception occurred when performing task! [%s]" % task_list[index])


def work2(task_list, process_log_dir, archive_log_dir, html_report_file_name):
    # 测试执行完成后开始收集数据
    # 备份旧日志
    log_file_backup(process_log_dir, archive_log_dir)
    # 收集新日志
    log_dir_src_list = []
    for task in task_list:
        log_dir_src = os.path.dirname(task.split("|")[0]) + os.sep + "log"
        if log_dir_src not in log_dir_src_list:
            log_dir_src_list.append(log_dir_src)
            log_file_collect(log_dir_src, process_log_dir)
    # 提取测试数据
    testing_data_list = get_testing_data(process_log_dir)
    # 生成测试报告
    generate_html_report(testing_data_list, process_log_dir, html_report_file_name)
    # 绘制Time-TPS/RT曲线图
    draw_chart(testing_data_list, process_log_dir)


def work3(receiver_list, subject, process_log_dir, html_report_file_name):
    # 发送邮件报告，内容为html格式报告，附件为过程日志目录
    # 邮件正文
    content = open(process_log_dir + os.sep + html_report_file_name).read()
    # 邮件图片列表
    image_list = [process_log_dir + os.sep + temp for temp in os.listdir(process_log_dir) if temp.endswith(".png")]
    # 发件人
    sender = "pta_system@pta.server.163.org"
    # 邮件正文格式
    _subtype = "html"
    # 发送邮件
    mail(receiver_list, subject, content, image_list, sender=sender, _subtype=_subtype)


def main():
    # 测试任务配置
    task_list = [
        r"scripts\demo\helloworld.py|100",
        r"scripts\java\call_java_method_test.py|100",
        r"scripts\fund\homePage.py|100",
        r"scripts\fund\getLcProductList.py|100",
        r"scripts\fund\getLcProductDetail.py|100",
        r"scripts\fund\getAllNotice.py|100",
        r"scripts\fund\getLcAsset.py|100",
    ]
    # 日志目录配置
    log_dir = "log"
    # 过程日志目录
    process_log_dir = log_dir + os.sep + "process_log"
    # 归档日志目录
    archive_log_dir = log_dir + os.sep + "archive_log"
    # 测试报告文件名
    html_report_file_name = "performance_testing.html"
    # 收件人列表
    receiver_list = ["caojl01@gmail.com", "hzcaojianglong@corp.netease.com"]
    # 邮件主题
    subject = u"性能测试自动化执行报告"
    # 三步工作流程
    work1(task_list)
    work2(task_list, process_log_dir, archive_log_dir, html_report_file_name)
    work3(receiver_list, subject, process_log_dir, html_report_file_name)


if __name__ == "__main__":
    main()
