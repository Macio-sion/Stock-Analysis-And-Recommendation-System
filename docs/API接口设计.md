# API 接口设计

## 概述
系统接口分为两类：REST API（任务提交/查询）与 WebSocket（实时事件推送）。前端采用 Streamlit，后端通过 FastAPI 暴露接口。

## REST API

### 1. 提交分析任务
```
POST /api/workflows
Body:
{
  "ts_code": "000001.SZ",
  "start_date": "20250101",
  "end_date": "20260831",
  "strategy_type": "价值型",            // 可选，默认均衡型
  "weights": {                          // 自定义权重，strategy_type=自定义时必填
    "fundamental": 0.7, "technical": 0.2, "sentiment": 0.1
  }
}
Response:
{ "workflow_id": "wf_20260831_001", "status": "pending" }
```

### 2. 查询任务状态
```
GET /api/workflows/{workflow_id}
Response:
{
  "workflow_id": "wf_20260831_001",
  "status": "completed",          // pending/running/stage1_done/completed/failed
  "current_phase": "stage3",      // stage1/stage2/stage3
  "error_message": null
}
```

### 3. 查询推荐结果
```
GET /api/workflows/{workflow_id}/recommendation
Response:
{
  "action": "买入",
  "score": 72.3,
  "reasoning": "基本面稳健且估值合理...",
  "report_full": { ... }
}
```

### 4. 提交自定义算法
```
POST /api/algorithms
Body:
{
  "workflow_id": "wf_20260831_001",
  "algorithm_name": "自定义加权算法",
  "source_type": "llm_generated",   // llm_generated / user_written
  "description": "根据三维度得分加权...",   // llm_generated 时必填
  "code": "def recommend(...)"       // user_written 时必填
}
Response:
{ "algorithm_id": "alg_20260831_001" }
```

### 5. 执行自定义算法
```
POST /api/algorithms/{algorithm_id}/execute
Response:
{ "execution_id": "exec_20260831_001", "status": "compiling" }
```

### 6. 查询执行结果
```
GET /api/executions/{execution_id}
Response:
{
  "execution_id": "exec_20260831_001",
  "status": "success",
  "exit_code": 0,
  "result_json": { "action": "买入", "score": 72.3 }
}
```

## WebSocket 事件协议

连接：`WS /ws/workflows/{workflow_id}`（需携带鉴权 token）。

### 事件消息结构
```json
{
  "type": "code | log | metric | status",
  "execution_id": "exec_20260831_001",
  "seq": 12,
  "payload": {},
  "timestamp": "2026-08-31T10:00:00Z"
}
```

### 事件类型
| type | 触发时机 | payload 示例 |
|------|----------|--------------|
| `status` | 阶段/节点状态变更 | `{"phase": "stage3", "status": "compiling"}` |
| `code` | 代码生成完成 | `{"code": "def recommend(...)"}` |
| `log` | 执行产生日志 | `{"level": "info", "message": "编译通过"}` |
| `metric` | 产生指标数据点 | `{"metric_name": "score", "step": 1, "value": 72.3}` |

## 错误码
| 错误码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误（ts_code 格式、权重和不为 1 等） |
| 401 | 未鉴权 |
| 403 | 无权限（非管理员修改系统参数） |
| 404 | 资源不存在（workflow_id / execution_id 无效） |
| 409 | 状态冲突（任务已存在/正在执行） |
| 422 | 算法校验失败（AST 拦截危险代码） |
| 429 | 触发限流 |
| 500 | 服务端内部错误 |
| 504 | 执行超时（沙箱 30s 超时） |
