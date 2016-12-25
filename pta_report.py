#!/usr/bin/python
# coding:utf-8

"""
Created on 2016年12月8日

@author: hzcaojianglong
"""

import logging
import math
import os
import re
import socket
import sys
import time

import matplotlib
import shutil

import numpy as np

matplotlib.use('Agg')
from matplotlib import pyplot


def log_file_backup(process_log_dir, archive_log_dir):
    """
    历史日志的归档（从process_log_dir到archive_log_dir）
    :param process_log_dir: 当次日志目录
    :param archive_log_dir: 历史日志目录
    :return:
    """
    if not os.path.exists(archive_log_dir):
        os.makedirs(archive_log_dir)
    time_now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
    if os.path.exists(process_log_dir):
        base_name = os.path.basename(process_log_dir)
        base_name_new = base_name + "_" + time_now
        shutil.move(process_log_dir, archive_log_dir + os.sep + base_name_new)


def log_file_collect(log_dir_src, process_log_dir):
    """
    当次运行日志的收集（从log_dir_src到process_log_dir）
    :param log_dir_src: 当次运行日志的源目录
    :param process_log_dir: 当次运行日志的目标目录
    :return:
    """
    if not os.path.exists(process_log_dir):
        os.makedirs(process_log_dir)
    grinder_log_file_list = [log_dir_src + os.sep + temp for temp in os.listdir(log_dir_src) if
                             temp.endswith(".log")]
    if not grinder_log_file_list:
        logging.warn("No grinder_main_log file! [%s]" % log_dir_src)
    for grinder_log_file in grinder_log_file_list:
        grinder_log_base_name = os.path.basename(grinder_log_file)
        shutil.move(grinder_log_file, process_log_dir + os.sep + grinder_log_base_name)


def _get_testing_result_main(grinder_main_log_file):
    # 构造字典保存结果信息
    key_list = ["testcase_name", "vuser_number", "tps", "mrt", "test_number", "success_number", "failed_number",
                "failed_rate"]
    result_dict = dict().fromkeys(key_list, "-")
    # 测试用例名称。这里用文件名，不用脚本里的测试名称，主要是为了避免脚本忘记改测试名称，出现重复。文件名也有重复的可能，怎么保证唯一呢？
    hostname_length = len(socket.gethostname())
    testcase_name = os.path.basename(grinder_main_log_file)[0:-(hostname_length + 7)]
    result_dict["testcase_name"] = testcase_name
    # 判断文件是否存在
    if not os.path.exists(grinder_main_log_file):
        return result_dict
    # 虚拟用户数
    pattern = re.compile(r'thread-(.*?): starting, will')
    vuser_list = []
    for line in open(grinder_main_log_file):
        if not pattern.search(line):
            continue
        vuser_list.append(pattern.findall(line))
    if vuser_list:
        vuser_number = str(len(vuser_list))
        result_dict["vuser_number"] = vuser_number
    # 成功次数、失败次数、平均响应时间、TPS
    pattern = re.compile(r'Totals\s+(.*?)\s+(.*?)\s+(.*?)\s+\d+.?\d*\s+(.*?)\s+.*?')
    for line in open(grinder_main_log_file):
        if not pattern.search(line):
            continue
        result = pattern.findall(line)[0]
        result_dict["success_number"] = result[0]
        result_dict["failed_number"] = result[1]
        result_dict["mrt"] = result[2]
        result_dict["tps"] = result[3]
    # 计算测试次数
    success_number = result_dict.get("success_number")
    failed_number = result_dict.get("failed_number")
    if success_number == "-" or failed_number == "-":
        logging.warn("Failed to calculate the value! [%s]" % grinder_main_log_file)
    else:
        test_number = str(int(success_number) + int(failed_number))
        result_dict["test_number"] = test_number
    # 计算失败率
    test_number = result_dict.get("test_number")
    if test_number == "-" or test_number == "0":
        logging.warn("Failed to calculate the value! [%s]" % grinder_main_log_file)
    else:
        failed_rate = str(int(failed_number) / float(test_number) * 100)[0:5] + "%"
        result_dict["failed_rate"] = failed_rate
    return result_dict


def _get_testing_result_data(grinder_data_log_file):
    # 构造字典保存结果信息
    key_list = ["rt_50", "rt_90", "rt_99", "time_line_list", "mrt_list", "tps_list"]
    result_dict = dict().fromkeys(key_list, "-")
    # 判断文件是否存在
    if not os.path.exists(grinder_data_log_file):
        return result_dict
    # 虚拟用户数
    pattern = re.compile(r"(.*?), \d+, \d+, \d+, \d+, \d+")
    vuser_list_tmp = []
    vuser_list = []
    for line in open(grinder_data_log_file):
        if not pattern.search(line):
            continue
        vuser_list_tmp.append(pattern.findall(line))

    # 开始时间列表、响应时间列表
    pattern = re.compile(r"(.*?), \d+, \d+, (.*?), (.*?), \d+")
    result_list = []
    for line in open(grinder_data_log_file):
        if not pattern.search(line):
            continue
        result = pattern.findall(line)[0]
        result_list.append(result)
    # 如果data文件提取到有效信息，则分离数据到各个列表
    if not result_list:
        return result_dict
    vuser_tmp_list = []
    start_time_list = []
    test_time_list = []
    # result_list.sort()
    result_list = sorted(result_list, key=lambda x: x[1])
    for index in range(len(result_list)):
        vuser_tmp = result_list[index][0]
        vuser_tmp_list.append(vuser_tmp)
        start_time = int((int(result_list[index][1]) - int(result_list[0][1])) / 1000)
        start_time_list.append(start_time)
        test_time = float(result_list[index][2])
        test_time_list.append(test_time)
    # 计算并发数
    vuser_list = []
    for vuser in vuser_tmp_list:
        if vuser not in vuser_list:
            vuser_list.append(vuser)
    vuser_number = str(len(vuser_list))
    # 计算50%和90%的响应时间
    test_time_list_sorted = sorted(test_time_list)
    rt_list_length = len(test_time_list_sorted)
    index_50 = int(math.ceil(rt_list_length / 2))
    result_dict["rt_50"] = test_time_list_sorted[index_50 - 1]
    index_90 = int(math.ceil(rt_list_length * 9 / 10))
    result_dict["rt_90"] = test_time_list_sorted[index_90 - 1]
    index_99 = int(math.ceil(rt_list_length * 99 / 100))
    result_dict["rt_99"] = test_time_list_sorted[index_99 - 1]
    # 计算时间线和MRT、TPS
    time_line_list = []
    mrt_list = []
    tps_list = []
    temp_time = start_time_list[0]
    temp_cost = test_time_list[0]
    cnt = 1
    for i in range(1, len(start_time_list)):
        if temp_time == start_time_list[i]:
            cnt += 1
            temp_cost += test_time_list[i]
        else:
            mrt = temp_cost / cnt
            tps = int(vuser_number) / mrt * 1000
            time_line_list.append(start_time_list[i - 1])
            mrt_list.append(mrt)
            tps_list.append(tps)
            temp_time = start_time_list[i]
            temp_cost = test_time_list[i]
            cnt = 1
    mrt = temp_cost / cnt
    tps = int(vuser_number) / mrt * 1000
    time_line_list.append(start_time_list[len(start_time_list) - 1])
    mrt_list.append(mrt)
    tps_list.append(tps)
    result_dict["time_line_list"] = time_line_list
    result_dict["mrt_list"] = mrt_list
    result_dict["tps_list"] = tps_list
    return result_dict


def get_testing_result(grinder_log_dir):
    """
    从Grinder运行日志目录的日志文件提取性能测试数据
    :param grinder_log_dir:当次日志目录
    :return:
    """
    if not os.path.exists(grinder_log_dir):
        logging.error("No such directory! [%s]" % grinder_log_dir)
        sys.exit(3)
    else:
        grinder_log_dir = os.path.abspath(grinder_log_dir)
    grinder_main_log_file_list = [grinder_log_dir + os.sep + temp for temp in os.listdir(grinder_log_dir) if
                                  temp.endswith("-0.log")]
    if not grinder_main_log_file_list:
        logging.error("No grinder_main_log file! [%s]" % grinder_main_log_file_list)
        sys.exit(2)
    result_dict_list = []
    grinder_main_log_file_list.sort()
    for index in range(0, len(grinder_main_log_file_list)):
        grinder_main_log_file = grinder_main_log_file_list[index]
        result_dict_main = _get_testing_result_main(grinder_main_log_file)
        testcase_name = result_dict_main.get("testcase_name")
        dir_name = os.path.dirname(grinder_main_log_file)
        grinder_data_log_file = dir_name + os.sep + testcase_name + "-" + socket.gethostname() + "-0-data.log"
        result_dict_data = _get_testing_result_data(grinder_data_log_file)
        result_dict = result_dict_main.copy()
        result_dict.update(result_dict_data)
        result_dict_list.append(result_dict)
    return result_dict_list


def generate_html_report(result_dict_list, grinder_log_dir, html_report_file_name):
    """
    从Grinder运行日志目录的日志文件提取性能测试数据，生成html格式报告
    :param result_dict_list:
    :param grinder_log_dir: 当次日志目录
    :param html_report_file_name: 生成的html报告的文件名
    :return:
    """
    td_content = "<tr>" + "<td><b>测试用例名称</b></td>" + "<td><b>并发数</b></td>" + "<td><b>TPS</b></td>" + \
                 "<td><b>MRT(ms))</b></td>" + "<td><b>50%RT(ms)</b></td>" + "<td><b>90%RT(ms)</b></td>" + \
                 "<td><b>99%RT(ms)</b></td>" + "<td><b>测试次数</b></td>" + "<td><b>成功次数</b></td>" + \
                 "<td><b>失败次数</b></td>" + "<td><b>失败率</b></td>" + "</tr>"
    for result_dict in result_dict_list:
        try:
            td_content += "<tr>"
            td_content += "<td><b>%s</b></td>" % result_dict["testcase_name"]
            td_content += "<td>%s</td>" % result_dict["vuser_number"]
            td_content += "<td>%s</td>" % result_dict["tps"]
            td_content += "<td>%s</td>" % result_dict["mrt"]
            td_content += "<td>%s</td>" % result_dict["rt_50"]
            td_content += "<td>%s</td>" % result_dict["rt_90"]
            td_content += "<td>%s</td>" % result_dict["rt_99"]
            td_content += "<td>%s</td>" % result_dict["test_number"]
            td_content += "<td>%s</td>" % result_dict["success_number"]
            td_content += "<td>%s</td>" % result_dict["failed_number"]
            td_content += "<td>%s</td>" % result_dict["failed_rate"]
            td_content += "</tr>"
        except Exception, e:
            logging.exception("Exception occurred when generating html report!")
    html_page = '<html><head><meta http-equiv="Content-Type" content="text/html";charset="utf-8"></head>'
    html_page += '<body><table border="1"><h3>性能测试结果如下：</h3><p/>%s</table>' % td_content
    time_now = time.strftime("%Y-%m-%d %X", time.localtime(time.time()))
    html_page += '</p><p>报告生成时间：%s</p></body></html>' % time_now
    with open(grinder_log_dir + os.sep + html_report_file_name, 'w') as result_file:
        result_file.write(html_page)


def draw_chart(result_dict_list, grinder_log_dir):
    """
    从Grinder运行日志目录的日志文件提取性能测试详细过程数据，并绘制图表
    :param result_dict_list:
    :param grinder_log_dir:当次日志目录
    :return:
    """
    if not os.path.exists(grinder_log_dir):
        logging.error("No such directory! [%s]" % grinder_log_dir)
        sys.exit(3)
    for result_dict in result_dict_list:
        try:
            if result_dict.get("time_line_list") == "-" or result_dict.get("mrt_list") == "-" or result_dict.get(
                    "tps_list") == "-" or result_dict.get("mrt") == "-" or result_dict.get("tps") == "-":
                logging.error("time_line_list or mrt_list or tps_list or mrt or tps is/are None!")
                continue
            testcase_name = result_dict.get("testcase_name")
            figure = pyplot.figure()
            ax1 = figure.add_subplot(111)
            pyplot.plot(result_dict.get("time_line_list"), result_dict.get("mrt_list"), 'r')
            ax2 = ax1.twinx()
            pyplot.plot(result_dict.get("time_line_list"), result_dict.get("tps_list"), 'g')
            ax1.set_xlabel("Time Since Starting(in s)")
            ax1.set_ylabel("RT (Response Time in ms)")
            ax2.set_ylabel("TPS (Transactions Per Second)")

            mrt = math.ceil(float(result_dict.get("mrt")))
            tps = math.ceil(float(result_dict.get("tps")))
            max_mrt = math.ceil(int(max(result_dict.get("mrt_list"))))
            max_tps = math.ceil(int(max(result_dict.get("tps_list"))))
            y_mrt = int(max(2.0 * mrt, max_mrt))
            y_tps = int(max(2.0 * tps, max_tps))
            if y_mrt / 1000 > 0:
                y_mrt = (y_mrt / 500 + 1) * 500
                ax1.set_yticks(np.linspace(0, y_mrt, y_mrt / 500 + 1))
            elif y_mrt / 100 > 0:
                y_mrt = (y_mrt / 50 + 1) * 50
                ax1.set_yticks(np.linspace(0, y_mrt, y_mrt / 50 + 1))
            elif y_mrt / 10 > 0:
                y_mrt = (y_mrt / 5 + 1) * 5
                ax1.set_yticks(np.linspace(0, y_mrt, y_mrt / 5 + 1))
            else:
                ax1.set_yticks(np.linspace(0, y_mrt, y_mrt + 1))
            if y_tps / 1000 > 0:
                y_tps = (y_tps / 500 + 1) * 500
                ax2.set_yticks(np.linspace(0, y_tps, y_tps / 500 + 1))
            elif y_tps / 100 > 0:
                y_tps = (y_tps / 50 + 1) * 50
                ax2.set_yticks(np.linspace(0, y_tps, y_tps / 50 + 1))
            elif y_mrt / 10 > 0:
                y_tps = (y_tps / 5 + 1) * 5
                ax2.set_yticks(np.linspace(0, y_tps, y_tps / 5 + 1))
            else:
                ax2.set_yticks(np.linspace(0, y_tps, y_tps + 1))
            ax1.legend(['$RT(x)$'], loc='upper left')
            ax2.legend(['$TPS(x)$'], loc='upper right')

            pyplot.title("Time-TPS/RT <" + testcase_name + ">")
            pyplot.grid(True)
            pyplot.savefig(grinder_log_dir + os.sep + testcase_name + ".png")
            pyplot.cla()
        except Exception, e:
            logging.exception("Exception occurred when drawing chart!")


def test1():
    grinder_log_dir = "log/process_log"
    result_dict_list = get_testing_result(grinder_log_dir)
    html_report_file_name = "performance_testing.html"
    generate_html_report(result_dict_list, grinder_log_dir, html_report_file_name)
    draw_chart(result_dict_list, grinder_log_dir)


if __name__ == '__main__':
    test1()
    pass
