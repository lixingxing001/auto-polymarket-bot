# BTC 5m Bot

一个面向 Polymarket `BTC Up or Down - 5 Minutes` 市场的研究型交易机器人骨架。

## 当前目标

先验证三件事：

1. 5 分钟方向信号在样本外是否存在
2. 扣除手续费、滑点、延迟后是否仍有正期望
3. 风控是否能让机器人在没有优势时保持沉默

## 设计原则

- 先纸面交易，后实盘
- 先证明单一信号有效，再考虑组合
- 先优化期望值，再看胜率
- 先限制损失，再讨论放大利润

## 模块

```text
market data -> features -> signal model -> edge gate -> risk manager -> paper/live execution
```

## 快速开始

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests
python -m btc5m_bot.cli
python -m btc5m_bot.live_snapshot
python -m btc5m_bot.paper_once
python -m btc5m_bot.paper_loop --iterations 4 --interval-seconds 15
python -m btc5m_bot.paper_dry_run_cli
python -m btc5m_bot.paper_loop --execution-dry-run --iterations 1
python -m btc5m_bot.live_execution_cli
python -m btc5m_bot.live_execution_cli --adapter mock
python -m btc5m_bot.execution_health_cli
python -m btc5m_bot.canary_readiness_cli
python -m btc5m_bot.mock_execution_smoke_cli
python -m btc5m_bot.canary_monitor_cli
python -m btc5m_bot.canary_kill_switch_cli
python -m btc5m_bot.canary_authorization_cli
python -m btc5m_bot.real_adapter_gate_cli
python -m btc5m_bot.canary_preflight_cli
python -m btc5m_bot.canary_watch_loop --iterations 1
python -m btc5m_bot.historical_cli --windows 48
python -m btc5m_bot.reconcile_cli
python -m btc5m_bot.train_cli --windows 288
python -m btc5m_bot.execution_backtest_cli --windows 48
python -m btc5m_bot.execution_backtest_cli --windows 288 --min-confidence 0.65
python -m btc5m_bot.extended_research_cli --windows 576
python -m btc5m_bot.snapshot_recorder --iterations 12 --interval-seconds 5
python -m btc5m_bot.ws_snapshot_recorder --max-windows 1 --max-seconds-per-window 20
python -m btc5m_bot.snapshot_coverage_cli --windows 288 --snapshots data\ws_orderbook_snapshots.csv
python -m btc5m_bot.snapshot_forward_eval_cli --archive-only
python -m btc5m_bot.snapshot_forward_eval_cli --windows 288
python -m btc5m_bot.snapshot_forward_loop --iterations 1
python -m btc5m_bot.strategy_guardrail_cli
python -m btc5m_bot.strategy_candidate_cli list
python -m btc5m_bot.strategy_candidate_cli compare --candidate-id edge_008
python -m btc5m_bot.candidate_evidence_cli
python -m btc5m_bot.candidate_change_review_cli
python -m btc5m_bot.error_diagnostics_cli --windows 288
python -m btc5m_bot.low_information_research_cli --windows 288
python -m btc5m_bot.execution_safety_cli
python -m btc5m_bot.snapshot_backtest_cli --windows 288
.\scripts\start_snapshot_recorder.ps1
.\scripts\status_snapshot_recorder.ps1
.\scripts\stop_snapshot_recorder.ps1
.\scripts\start_ws_snapshot_recorder.ps1
.\scripts\status_ws_snapshot_recorder.ps1
.\scripts\stop_ws_snapshot_recorder.ps1
.\scripts\start_snapshot_forward_loop.ps1
.\scripts\status_snapshot_forward_loop.ps1
.\scripts\stop_snapshot_forward_loop.ps1
.\scripts\start_canary_watch_loop.ps1
.\scripts\status_canary_watch_loop.ps1
.\scripts\stop_canary_watch_loop.ps1
```

## 当前阶段

当前仓库只包含最小研究骨架：

- 领域模型
- 特征结构
- 一个可替换的基线信号模型
- 风控与纸面成交决策
- 当前 5 分钟 BTC 市场发现
- Polymarket 订单簿快照读取
- Coinbase 公共分钟级行情读取
- 单次纸面交易决策
- 可落 CSV 的纸面信号循环
- 历史标签数据集构建
- 基线方向评估
- 纸面信号结算与前向收益统计
- 训练型逻辑回归与时间切分评估
- 走样本外 walk-forward 评估
- Coinbase 逐笔成交与 L1 盘口微结构特征
- 基于真实成交的可执行价格代理回测
- 回测结果复盘文档
- Polymarket 历史价格特征与市场基线
- market-aware 模型复盘文档
- market-aware 可执行价格回测复盘文档
- 自有盘口快照采集器
- 扩展样本研究入口
- 历史样本缓存
- 快照驱动回测入口
- 快照驱动回测复盘文档
- 快照采集后台脚本
- 快照采集运维文档
- WebSocket 实时盘口采集器
- WebSocket 快照采集复盘文档
- 快照覆盖率检查入口
- 已结算快照归档与前向评估入口
- 前向评估后台循环脚本
- 策略门控与参数冻结审计入口
- 候选策略登记与受控对照入口
- 候选策略证据成熟度审计入口
- 候选策略变更审查入口
- 模型误差分层诊断入口
- 低信息窗口过滤研究入口
- 执行安全预检查入口
- 纸面订单 dry-run 入口
- 默认拒单的实盘适配器接口
- 订单意图状态机与执行审计事件
- 执行健康报告入口
- canary readiness 门槛报告入口
- 受控 mock 执行烟测入口
- canary readiness 自动监控入口
- canary kill switch 报告入口
- canary 授权包生成入口
- 真实适配器前置门禁报告入口
- canary 最终预检聚合入口
- canary 本地 10 分钟 watchdog
- canary 极小金额运行手册

下一步才会接：

- 纸面交易日志
- 实盘执行
