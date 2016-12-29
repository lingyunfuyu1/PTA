#!/usr/bin/python
# coding:utf-8

"""
Created on 2016年11月23日

@author: hzcaojianglong
"""
import logging
import os
import smtplib
import tarfile
from contextlib import closing
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText


def mail(receiver_list, subject, content, image_list=[], sender="pta_system@pta.server.org", _subtype="html"):
    """
    发送带附件的邮件
    :param receiver_list: 收件人列表，列表格式
    :param subject: 邮件主题，字符串格式
    :param content: 邮件正文内容，字符串格式
    :param image_list: 邮件图片列表，列表格式，可以传多个图片，每个图片需包含路径，避免open的时候找不到
    :param sender: 发件人，字符串格式，可不传，不传默认system
    :param _subtype: 邮件正文内容类型，字符串格式，可不传，不传默认plain
    :return:
    """
    mail_host = "smtp.163.com"
    mail_user = "testcaojl@163.com"
    mail_pass = "perf2016"

    message = MIMEMultipart("related")
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = ",".join(receiver_list)

    for image in image_list:
        fp = open(image, 'rb')
        message_image = MIMEImage(fp.read())
        fp.close()
        image_name = os.path.splitext(os.path.basename(image))[0]
        message_image.add_header('Content-ID', "<image-" + image_name + ">")
        message.attach(message_image)
        content = content + '<img src="cid:image-' + image_name + '">'
    message.attach(MIMEText(content, _subtype, 'utf-8'))
    # for attachment in attachment_list:
    #     attach = MIMEText(open(attachment, 'rb').read(), 'base64', 'utf-8')
    #     attach["Content-Type"] = 'application/octet-stream'
    #     attach["Content-Disposition"] = 'attachment; filename=' + os.path.basename(attachment)
    #     message.attach(attach)

    try:
        smtp_object = smtplib.SMTP()
        smtp_object.connect(mail_host, 25)
        smtp_object.login(mail_user, mail_pass)
        smtp_object.sendmail(mail_user, receiver_list, message.as_string())
        smtp_object.quit()
    except smtplib.SMTPException, e:
        logging.exception("Exception occurred when sending a mail!")


def test():
    log_dir = "log"
    process_log_dir = log_dir + os.sep + "process_log"
    html_report_file_name = "performance_testing.html"
    receiver_list = ["caojl01@gmail.com", "hzcaojianglong@corp.netease.com"]
    # 发送邮件报告，内容为html格式报告，附件为过程日志目录
    subject = u"性能测试自动化报告"
    content = open(process_log_dir + os.sep + html_report_file_name).read()
    image_list = [process_log_dir + os.sep + temp for temp in os.listdir(process_log_dir) if temp.endswith(".png")]
    sender = "pta_system@pta.server.163.org"
    _subtype = "html"
    mail(receiver_list, subject, content, image_list, sender=sender, _subtype=_subtype)


if __name__ == "__main__":
    test()
    pass
