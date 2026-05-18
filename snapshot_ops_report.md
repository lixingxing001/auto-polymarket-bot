# Snapshot Operations Report

## 已完成

- 后台常驻采集脚本
- 启动脚本
- 状态脚本
- 停止脚本
- 标准输出日志
- 标准错误日志

## 当前现场状态

- 采集进程已经启动
- 当前快照文件持续增长
- 当前已经覆盖多个 5 分钟窗口

## 常用命令

```powershell
.\scripts\start_snapshot_recorder.ps1
.\scripts\status_snapshot_recorder.ps1
.\scripts\stop_snapshot_recorder.ps1
```

## 设计意图

采集器要尽量像基础设施：

- 网络抖动时继续工作
- 可以被启动、观察、停止
- 日志和数据都能独立检查

只有这样，后面的快照驱动回测才会有源源不断的原料。
