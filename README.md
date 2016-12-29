****什么是PTA****

PTA是Performance Testing Automation（性能测试自动化）的缩写，是基于性能测试框架The Grinder，集测试执行、测试报告生成（包括html格式和图表格式）、测试报告发送为一体的一个性能测试自动化工具。

配合系统的定时任务（Windows系统的SchTasks（任务计划程序）、Linux系统的crontab），它支持多个任务定时自动化执行（串行执行，并行会有测试机、服务器资源争用问题），从开始测试到发送报告，整个过程完全无需人工干涉。

除了性能测试自动化，它还可用于单个性能测试调试、手工性能测试执行、性能测试报告生成与图表绘制等工作中，操作易用性上比The Grinder要容易得多。



****怎么用PTA****

唯一的外部依赖是JDK，需要安装JDK并配置环境变量。

用于性能测试自动化：配置task_list.txt，运行pta_run.py
用于性能测试调试：直接使用pta_core.py
用于手工执行性能测试：使用pta_core.py和pta_report.py
用于性能测试报告生成与图表绘制：使用pta_report.py



****PTA的下一步****
性能测试脚自动生成
性能测试基线比对



****有疑问****
请联系caojl01@foxmail.com

