# 项目日记

## 2026-01-02
from MasterAgent
- 更新 `PROJECT/TASK_METRICS.md`：为“论文来源获取”调研与模块搭建任务补充验收标准与交付物定义。
- 更新 `PROJECT/SPECIFICATION.md`：补全 v0.1“论文来源获取（Paper Ingest）”的约束、能力边界、API 草案与数据模型草案，作为后端实现依据。
from Human
- 人工审核: 第一次委托后端Agent执行任务，发现Agent直接写入的main文件里，而不是拉取main到沙盒环境中,推测是角色提示词的问题。TODO
- 人工审核: 发现仅创建了头部注解，对于函数等没有写入注释。TODO
- 人工审核: 发现日志的时间颗粒度太粗，应该显示时分秒级的。TODO
- 人工审核: 发现Agent并无创建记忆和操作日志。TODO
- 人工操作: 已将相关代码手动移动至 `AGENT\BACKEND_AGENT\SANDBOX`中
