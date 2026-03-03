\# Job AI Workflow



一个可运行的岗位分析与能力差距评估系统。



\## 项目目标



构建一个完整的数据分析 + AI 工作流系统，实现：



\- Excel 导入岗位数据

\- 数据标准化

\- LLM 抽取技能

\- 技能分层与加权匹配

\- 自动能力分级

\- 自动生成求职分析报告



该系统可重复运行、可扩展、可解释。



---



\## 技术栈



\- Python

\- Pandas

\- SQLite

\- OpenAI / Dashscope API

\- Excel 自动读写

\- Git 版本管理



---



\## 系统流程



Excel 导入  

→ 数据清洗  

→ LLM 技能抽取  

→ 技能分层（Core / Extended / Premium）  

→ 加权匹配模型  

→ 自动生成报告  



---



\## 运行方式



1\. 安装依赖



```bash

pip install -r requirements.txt

