# Notes: BTC 5分钟涨跌交易机器人

## Sources

### Polymarket 5分钟 BTC 市场
- URL: https://polymarket.com/event/btc-updown-5m-1771263300/btc-updown-5m-1771263300
- Key points:
  - 5 分钟窗口按起点和终点价格比较决定 Up 或 Down。
  - 结算源是 Chainlink BTC/USD data stream。
  - 现场验证显示 slug 采用 `btc-updown-5m-{window_start_epoch}` 格式。

### Polymarket 事件与订单簿接口
- URL: https://docs.polymarket.com/api-reference/events/get-event-by-slug
- URL: https://docs.polymarket.com/trading/orderbook
- Key points:
  - 可按 slug 直接获取事件。
  - 可按 token id 获取订单簿。
  - 官方建议实时订单簿使用 WebSocket，REST 更适合快照读取。

### Polymarket 历史价格与成交
- URL: https://docs.polymarket.com/api-reference/markets/get-prices-history
- URL: https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets
- Key points:
  - `prices-history` 的 `interval` 与 `startTs/endTs` 互斥，不能混用。
  - `trades` 支持按 condition ID 过滤，返回实际成交的方向、价格、规模和时间戳。

### Polymarket 市场列表接口
- URL: https://docs.polymarket.com/api-reference/markets/list-markets
- Key points:
  - 市场对象包含 `closed` 与 `outcomePrices` 字段，可用于识别已结算窗口与结果。

### Coinbase Exchange 历史 candles
- URL: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles
- Key points:
  - 支持 60 秒粒度历史 candles。
  - 单次请求最多 300 根，较长时间范围需要分块抓取。

### Coinbase Exchange trades 与 order book
- URL: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-trades
- URL: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductbook
- Key points:
  - trades 接口提供最新逐笔成交。
  - `side` 表示 maker 侧，`sell` 可视作向上成交冲击，`buy` 可视作向下成交冲击。
  - book 接口可提供盘口快照，官方建议高实时性场景改用 WebSocket。

### Polymarket CLOB V2 迁移说明
- URL: https://docs.polymarket.com/v2-migration
- Key points:
  - CLOB V2 已于 2026-04-28 上线。
  - 旧版 V1 SDK 与 V1 签名订单在生产环境已不可用。

### Polymarket 交易与费用文档
- URL: https://docs.polymarket.com/trading/overview
- URL: https://docs.polymarket.com/trading/fees
- Key points:
  - 当前推荐使用官方 V2 SDK。
  - Crypto 类市场存在 taker fee，且 50% 附近费用最重。

### Coinbase Advanced Trade WebSocket
- URL: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels
- Key points:
  - 提供 5 分钟 candles。
  - 提供 market_trades 流，可用于成交方向与短期冲击特征。

## Synthesized Findings

### Initial framing
- 5 分钟方向判断首先是一个交易问题，其次才是分类问题。
- 如果没有把手续费、滑点、延迟、仓位规则一起建模，单看准确率会产生严重幻觉。

### Market design implications
- 对 Polymarket 来说，目标不是预测 BTC 本身，而是预测“在当前盘口价格下是否仍有正期望值”。
- 因为 crypto 市场存在 taker fee，接近 50% 概率时交易成本最伤，策略要优先寻找显著偏离而不是频繁出手。
- 外部价格源可以先用 Coinbase 5 分钟 candles 与逐笔成交做基线特征，后续再接更细粒度盘口数据。
- 对当前市场发现，优先使用时间推导 slug，再以 REST 读取事件元数据。
- 优势判断必须按 `fee = feeRate * p * (1-p)` 动态扣除 crypto taker fee，不能用固定常数近似。
- 历史训练样本先在开窗后 60 秒统一取点，避免决策时刻漂移带来的标签污染。
- 提升目标要拆成两部分：全量样本泛化能力，以及高置信度子集的命中率和覆盖率。
- 历史订单簿快照没有在当前公开文档中暴露，因此现阶段用真实成交构造可执行价格代理，比只看 midpoint 更接近交易现实。
- Polymarket 展示价格本质上来自盘口中点，价差过宽时使用最近成交，因此它天然是强基线，模型必须正面击败它。
