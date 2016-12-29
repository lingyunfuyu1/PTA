#!/usr/bin/env python
# coding:utf-8

"""
Created on 20161208
Updated on 20161228

@author: hzcaojianglong
"""

import logging
import math
import os
import re
import shutil
import socket
import sys
import time

import matplotlib
import numpy as np

matplotlib.use('Agg')
from matplotlib import pyplot


def log_file_backup(archive_log_dir, process_log_dir):
    """
    历史日志的归档，运行PTA时，需要将上次运行的结果进行备份（从process_log_dir到archive_log_dir）
    :param archive_log_dir: 归档日志目录
    :param process_log_dir: 当次运行日志目录
    :return:
    """
    if not os.path.exists(archive_log_dir):
        os.makedirs(archive_log_dir)
    time_now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
    if os.path.exists(process_log_dir):
        base_name = os.path.basename(process_log_dir)
        base_name_new = base_name + "_" + time_now
        shutil.move(process_log_dir, archive_log_dir + os.sep + base_name_new)


def _get_testing_result_main(grinder_main_log_file):
    """
    从主日志提取结果数据，将结果保存到字典
    :param grinder_main_log_file: 主日志
    :return: 结果字典result_dict
    """
    # 构造字典保存结果信息
    key_list = ["test_case_name", "virtual_user_number", "tps", "mrt", "success_number", "failure_number"]
    result_dict = dict().fromkeys(key_list, "-")
    # # 测试用例名称临时用日志名保存，似乎没有必要，先注释掉
    # test_case_name = os.path.splitext(os.path.basename(grinder_main_log_file))[0]
    # result_dict["test_case_name"] = test_case_name
    # 判断主日志文件是否存在
    if not os.path.exists(grinder_main_log_file):
        return result_dict
    # 提取测试用例名称、成功次数、失败次数、平均响应时间、TPS、并发数
    # 测试用例名称。这里用文件名，不用脚本里的测试名称，主要是为了避免脚本忘记改测试名称，出现重复。
    # TODO: 脚本文件名也有重复的可能性，怎么保证唯一呢？小概率事件，主要靠规范控制吧。
    pattern_1 = re.compile(r'running "(.*?).py"')
    # 并发数
    pattern_2 = re.compile(r'thread-(.*?): starting, will')
    # 用count控制搜索虚拟用户次数，提高搜索效率，和并发数多少以及日志内容有关，设置10万行应该足够了
    count = 0
    # 将虚拟用户存到列表，统计长度得到并发数
    virtual_user_list = []
    # 成功次数、失败次数、平均响应时间、TPS
    pattern_3 = re.compile(r'Totals\s+(.*?)\s+(.*?)\s+(.*?)\s+\d+.?\d*\s+(.*?)\s+.*?')
    for line in open(grinder_main_log_file):  # 大文件性能优化？
        if result_dict["test_case_name"] == "-" and pattern_1.search(line):
            result_dict["test_case_name"] = pattern_1.findall(line)[0]
        if count < 100000 and pattern_2.search(line):
            virtual_user_list.append(pattern_2.findall(line))
            count += 1
        if pattern_3.search(line):
            tmp = pattern_3.findall(line)[0]
            result_dict["success_number"] = tmp[0]
            result_dict["failure_number"] = tmp[1]
            result_dict["mrt"] = tmp[2]
            result_dict["tps"] = tmp[3]
    if virtual_user_list:
        virtual_user_number = str(len(virtual_user_list))
        result_dict["virtual_user_number"] = virtual_user_number
    return result_dict


def _get_testing_result_data(grinder_data_log_file):
    """
    从数据日志提取数据，将结果保存到字典
    :param grinder_data_log_file: 数据日志
    :return: 结果字典result_dict
    """
    # 构造字典保存结果信息
    key_list = ["start_time_list", "time_since_list", "time_format_list", "test_time_list"]
    result_dict = dict().fromkeys(key_list, "-")
    # 判断文件是否存在
    if not os.path.exists(grinder_data_log_file):
        return result_dict
    # 开始时间列表、响应时间列表
    pattern = re.compile(r"\d+, \d+, \d+, (.*?), (.*?), \d+")
    tmp_list = []
    for line in open(grinder_data_log_file):
        if not pattern.search(line):
            continue
        tmp = pattern.findall(line)[0]
        tmp_list.append(tmp)
    # 如果data文件提取到有效信息，则分离数据到各个列表
    if not tmp_list:
        return result_dict
    start_time_list = []
    time_since_list = []
    time_format_list = []
    test_time_list = []
    # TODO: 不知道这个性能怎么样，可能有风险
    tmp_list.sort()
    # tmp_list = sorted(tmp_list, key=lambda x: x[0])
    for index in range(len(tmp_list)):
        start_time = tmp_list[index][0]
        start_time_list.append(start_time)
        # 计算测试时间线1，从开始到现在过去多久
        time_since = int(int(tmp_list[index][0]) / 1000 - int(tmp_list[0][0]) / 1000)
        time_since_list.append(time_since)
        # 计算测试时间线2，当前时刻的标准格式
        time_format = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(start_time) / 1000))
        time_format_list.append(time_format)
        # 每个run的执行时间，单位毫秒
        test_time = int(tmp_list[index][1])  # 必须整形保存，后续计算50rt、90rt需要排序
        test_time_list.append(test_time)
    result_dict["start_time_list"] = start_time_list
    result_dict["time_since_list"] = time_since_list
    result_dict["time_format_list"] = time_format_list
    result_dict["test_time_list"] = test_time_list
    return result_dict


def _get_testing_result(grinder_main_log_file, grinder_data_log_file):
    """
    合并主日志和数据日志提取结果，并计算附加结果数据（如失败率、时间线、平均响应时间线、TPS线），将结果保存到字典
    :param grinder_main_log_file: 主日志
    :param grinder_data_log_file: 数据日志
    :return: 合并然后扩展的结果字典result_dict
    """
    # 风险判断，判断主日志和数据日志是否配套
    if os.path.abspath(grinder_main_log_file.replace("-main.log", "-data.log")) != os.path.abspath(
            grinder_data_log_file):
        logging.warn("The grinder_main_log_file and the grinder_data_log_file do not match! ")
        exit(1)

    # 提取主日志中的结果数据，保存到字典result_dict_main
    result_dict_main = _get_testing_result_main(grinder_main_log_file)

    # 提取数据日志中的结果数据，保存到字典result_dict_data
    result_dict_data = _get_testing_result_data(grinder_data_log_file)

    # 构造字典保存附加结果信息
    key_list = ["test_number", "failure_rate", "rt_50", "rt_90", "rt_99", "mrt_this_second_list",
                "tps_this_second_list", "time_since_unique_list"]
    result_dict_additional = dict().fromkeys(key_list, "-")

    # 合并3个结果字典，得到最终结果字典
    result_dict = {}
    result_dict.update(result_dict_main)
    result_dict.update(result_dict_data)
    result_dict.update(result_dict_additional)

    # 计算测试次数
    success_number = result_dict.get("success_number")
    failure_number = result_dict.get("failure_number")
    if success_number == "-" or failure_number == "-":
        logging.warn("Failed to calculate the value of test_number! [%s]" % result_dict["test_case_name"])
    else:
        test_number = str(int(success_number) + int(failure_number))
        result_dict["test_number"] = test_number
    # 计算失败率
    test_number = result_dict.get("test_number")
    if test_number == "-" or test_number == "0":
        logging.warn("Failed to calculate the value of failure_rate! [%s]" % result_dict["test_case_name"])
    else:
        failure_rate = str(int(failure_number) / float(test_number) * 100)[0:5] + "%"
        result_dict["failure_rate"] = failure_rate
    # 计算50%、90%、99%的响应时间
    test_time_list = result_dict["test_time_list"]
    if test_time_list == "-":
        logging.warn("Failed to calculate the value of 50percentRT、90percentRT、99percentRT! [%s]" % result_dict[
            "test_case_name"])
    else:
        # 此段代码慎改，建议用少量数据边测试边修改
        test_time_list_sorted = sorted(result_dict["test_time_list"])
        rt_list_length = len(test_time_list_sorted)
        index_50 = int(math.ceil(rt_list_length / 2.0))
        result_dict["rt_50"] = test_time_list_sorted[index_50 - 1]
        index_90 = int(math.ceil(rt_list_length * 9 / 10.0))
        result_dict["rt_90"] = test_time_list_sorted[index_90 - 1]
        index_99 = int(math.ceil(rt_list_length * 99 / 100.0))
        result_dict["rt_99"] = test_time_list_sorted[index_99 - 1]
    # 计算MRT_list、TPS_list
    virtual_user_number = result_dict["virtual_user_number"]
    time_since_list = result_dict["time_since_list"]
    if virtual_user_number == "-" or time_since_list == "-":
        logging.warn("Failed to calculate the value of MRT_list、TPS_list! [%s]" % result_dict["test_case_name"])
    else:
        mrt_this_second_list = []
        tps_this_second_list = []
        time_since_unique_list = []
        tmp_time_since = time_since_list[0]  # time_since_list存放的是每个run的时刻，以秒为单位，同一秒可能多个run
        sum_test_time = float(test_time_list[0])  # time_time_list存放的是每个run的执行耗时，单位是毫秒
        count = 1  # 计数器，统计同一秒有多少个run
        for i in range(1, len(time_since_list)):
            if time_since_list[i] == tmp_time_since:
                count += 1
                sum_test_time += float(test_time_list[i])
            else:
                mrt_this_second = round(sum_test_time / count, 3)  # 计算这一秒所有run的平均响应时间MRT
                mrt_this_second_list.append(mrt_this_second)
                tps_this_second = round(int(virtual_user_number) / mrt_this_second * 1000, 3)  # 计算这一秒所有run的TPS
                tps_this_second_list.append(tps_this_second)
                time_since_unique_list.append(time_since_list[i - 1])  # time_since_unique_list是time_since_list的去重复
                tmp_time_since = time_since_list[i]
                sum_test_time = float(test_time_list[i])
                count = 1
        mrt_this_second = round(sum_test_time / count, 3)
        mrt_this_second_list.append(mrt_this_second)
        tps_this_second = round(int(virtual_user_number) / mrt_this_second * 1000, 3)
        tps_this_second_list.append(tps_this_second)
        time_since_unique_list.append(time_since_list[len(time_since_list) - 1])

        result_dict["mrt_this_second_list"] = mrt_this_second_list
        result_dict["tps_this_second_list"] = tps_this_second_list
        result_dict["time_since_unique_list"] = time_since_unique_list
    return result_dict


def get_testing_result_batch(process_log_dir):
    """
    从Grinder运行日志目录的日志文件提取性能测试数据
    :param process_log_dir:当次日志目录
    :return:
    """
    if not os.path.exists(process_log_dir):
        logging.error("No such directory! [%s]" % process_log_dir)
        sys.exit(1)
    grinder_main_log_file_list = [process_log_dir + os.sep + temp for temp in os.listdir(process_log_dir) if
                                  temp.endswith("-main.log")]
    if not grinder_main_log_file_list:
        logging.error("No grinder_main_log file in this directory! [%s]" % grinder_log_dir)
        sys.exit(1)
    result_dict_list = []
    grinder_main_log_file_list.sort()
    for index in range(0, len(grinder_main_log_file_list)):
        # 遍历Grinder主日志列表
        grinder_main_log_file = grinder_main_log_file_list[index]
        # 找到当前主日志文件对应的数据日志文件
        grinder_data_log_file = grinder_main_log_file.replace("-main.log", "-data.log")
        # 获取最终的结果数据，保存到字典result_dict
        result_dict = _get_testing_result(grinder_main_log_file, grinder_data_log_file)
        # 将当前结果字典追加到结果字典列表（可能需要循环处理多个用例的数据，所以结果以列表形式保存，元素为结果字典result_dict）
        result_dict_list.append(result_dict)
    return result_dict_list


def generate_html_report(result_dict_list, grinder_log_dir, html_report_file_name):
    """
    从Grinder运行日志目录的日志文件提取性能测试数据，生成html格式报告
    :param result_dict_list:
    :param grinder_log_dir:当次运行日志目录
    :param html_report_file_name: 生成的html报告的文件名
    :return:
    """
    td_content = "<tr>" + "<td><b>测试用例名称</b></td>" + "<td><b>并发数</b></td>" + "<td><b>TPS</b></td>" + \
                 "<td><b>MRT(ms)</b></td>" + "<td><b>50%RT(ms)</b></td>" + "<td><b>90%RT(ms)</b></td>" + \
                 "<td><b>99%RT(ms)</b></td>" + "<td><b>测试次数</b></td>" + "<td><b>成功次数</b></td>" + \
                 "<td><b>失败次数</b></td>" + "<td><b>失败率</b></td>" + "</tr>"
    for result_dict in result_dict_list:
        try:
            td_content += "<tr>"
            td_content += "<td><b>%s</b></td>" % result_dict["test_case_name"]
            td_content += "<td>%s</td>" % result_dict["virtual_user_number"]
            td_content += "<td>%s</td>" % result_dict["tps"]
            td_content += "<td>%s</td>" % result_dict["mrt"]
            td_content += "<td>%s</td>" % result_dict["rt_50"]
            td_content += "<td>%s</td>" % result_dict["rt_90"]
            td_content += "<td>%s</td>" % result_dict["rt_99"]
            td_content += "<td>%s</td>" % result_dict["test_number"]
            td_content += "<td>%s</td>" % result_dict["success_number"]
            td_content += "<td>%s</td>" % result_dict["failure_number"]
            td_content += "<td>%s</td>" % result_dict["failure_rate"]
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
    :param grinder_log_dir:当次运行日志目录
    :return:
    """
    if not os.path.exists(grinder_log_dir):
        logging.error("No such directory! [%s]" % grinder_log_dir)
        sys.exit(1)
    for result_dict in result_dict_list:
        try:
            time_since_unique_list = result_dict.get("time_since_unique_list")
            mrt_this_second_list = result_dict.get("mrt_this_second_list")
            tps_this_second_list = result_dict.get("tps_this_second_list")
            mrt = result_dict.get("mrt")
            tps = result_dict.get("tps")
            if "-" in [time_since_unique_list, mrt_this_second_list, tps_this_second_list, mrt, tps]:
                logging.error("Some params are None! Unable to draw a line! [%s]" % result_dict.get("test_case_name"))
                continue
            # 列表里只有一个元素（即一个点）的时候无法画线
            if len(mrt_this_second_list) <= 1:
                logging.error(
                    "Only one point! Unable to draw a line! [%s]" % result_dict.get("test_case_name"))
                continue
            # 画折线图
            test_case_name = result_dict.get("test_case_name")
            figure = pyplot.figure()
            # 设置标题
            pyplot.title("Time-TPS/RT <TestCase: " + test_case_name + ">")
            # 网格效果
            pyplot.grid(True)
            ax1 = figure.add_subplot(111)
            pyplot.plot(result_dict.get("time_since_unique_list"), result_dict.get("mrt_this_second_list"), 'r')
            ax2 = ax1.twinx()
            pyplot.plot(result_dict.get("time_since_unique_list"), result_dict.get("tps_this_second_list"), 'g')
            ax1.set_xlabel("Time Since Starting (in s)")
            ax1.set_ylabel("RT  (Response Time in ms)")
            ax2.set_ylabel("TPS  (Transactions Per Second)")
            # 设置坐标轴
            mrt = math.ceil(float(result_dict.get("mrt")))
            tps = math.ceil(float(result_dict.get("tps")))
            max_mrt = math.ceil(int(max(result_dict.get("mrt_this_second_list"))))
            max_tps = math.ceil(int(max(result_dict.get("tps_this_second_list"))))
            # 计算坐标轴最大值和刻度，刻度值为5、50、500的倍数
            # TODO: 这里试行方案，需详细考证
            y_mrt = int(max(2.0 * mrt, max_mrt))
            for scale in [1000, 100, 10, 1]:
                if scale == 1:
                    ax1.set_yticks(np.linspace(0, y_mrt, y_mrt + 1))
                    break
                if y_mrt / scale > 0:
                    y_mrt = (y_mrt / (scale / 2) + 1) * (scale / 2)
                    ax1.set_yticks(np.linspace(0, y_mrt, y_mrt / (scale / 2) + 1))
                    break
            y_tps = int(max(2.0 * tps, max_tps))
            ax1.legend(['$RT(time)$'], loc='upper left')
            for scale in [1000, 100, 10, 1]:
                if scale == 1:
                    ax2.set_yticks(np.linspace(0, y_tps, y_tps + 1))
                    break
                if y_tps / scale > 0:
                    y_tps = (y_tps / (scale / 2) + 1) * (scale / 2)
                    ax2.set_yticks(np.linspace(0, y_tps, y_tps / (scale / 2) + 1))
                    break
            ax2.legend(['$TPS(time)$'], loc='upper right')
            # 保存为文件
            pyplot.savefig(grinder_log_dir + os.sep + test_case_name + ".png")
            # 清空，避免影响下次
            pyplot.cla()
        except Exception, e:
            logging.exception("Exception occurred when drawing chart!")


def test():
    """单元测试"""
    log_dir = "log"
    process_log_dir = log_dir + os.sep + "process_log"
    result_dict_list = get_testing_result_batch(process_log_dir)
    html_report_file_name = "performance_testing.html"
    generate_html_report(result_dict_list, process_log_dir, html_report_file_name)
    draw_chart(result_dict_list, process_log_dir)


if __name__ == '__main__':
    test()
    pass
