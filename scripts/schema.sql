-- ============================================================
-- 智能股票推荐系统 数据库 Schema（PostgreSQL）
-- 对应《节点状态信息与运行时数据持久化设计》
-- ============================================================

-- 1. 工作流实例表（元数据）
CREATE TABLE IF NOT EXISTS workflow_instances (
    workflow_id VARCHAR(64) PRIMARY KEY,
    ts_code VARCHAR(16) NOT NULL,
    status VARCHAR(32),        -- pending / running / stage1_done / completed / failed
    current_phase VARCHAR(16), -- stage1 / stage2 / stage3
    strategy_type VARCHAR(32),
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 2. Agent 状态快照表（工作底稿）
CREATE TABLE IF NOT EXISTS agent_state_snapshots (
    id UUID PRIMARY KEY,
    workflow_id VARCHAR(64) REFERENCES workflow_instances(workflow_id),
    agent_name VARCHAR(32),
    phase VARCHAR(16),
    state_data JSONB NOT NULL, -- 完整 Agent State（内嵌 schema_version）
    is_latest BOOLEAN,
    created_at TIMESTAMP
);

-- 3. 最终推荐报告表（结果）
CREATE TABLE IF NOT EXISTS recommendations (
    workflow_id VARCHAR(64) PRIMARY KEY REFERENCES workflow_instances(workflow_id),
    symbol VARCHAR(16),
    action VARCHAR(16),        -- buy / hold / sell
    score DECIMAL(5,2),
    reasoning TEXT,
    report_full JSONB,
    created_at TIMESTAMP
);

-- 4. 自定义算法脚本库
CREATE TABLE IF NOT EXISTS custom_algorithms (
    id UUID PRIMARY KEY,
    workflow_id VARCHAR(64) REFERENCES workflow_instances(workflow_id),
    algorithm_name VARCHAR(128),
    source_type VARCHAR(32),   -- llm_generated / user_written
    code TEXT NOT NULL,
    status VARCHAR(32),
    created_at TIMESTAMP
);

-- 5. 算法执行记录
CREATE TABLE IF NOT EXISTS algorithm_executions (
    id UUID PRIMARY KEY,
    custom_algorithm_id UUID REFERENCES custom_algorithms(id),
    status VARCHAR(32),        -- compiling / running / success / failed
    exit_code INT,
    duration_ms INT,
    result_json JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 6. 算法执行日志流
CREATE TABLE IF NOT EXISTS execution_logs (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID REFERENCES algorithm_executions(id),
    seq INT,
    level VARCHAR(16),
    message TEXT,
    timestamp TIMESTAMP
);

-- 7. 算法执行指标序列
CREATE TABLE IF NOT EXISTS metric_series (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID REFERENCES algorithm_executions(id),
    metric_name VARCHAR(64),
    step INT,
    value DECIMAL(18,6),
    timestamp TIMESTAMP
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_workflow_ts_code ON workflow_instances (ts_code);
CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_instances (status);
CREATE INDEX IF NOT EXISTS idx_workflow_started_at ON workflow_instances (started_at);

CREATE INDEX IF NOT EXISTS idx_snapshot_lookup ON agent_state_snapshots (workflow_id, agent_name, is_latest);

CREATE INDEX IF NOT EXISTS idx_recommendation_created_at ON recommendations (created_at);

CREATE INDEX IF NOT EXISTS idx_algorithm_workflow ON custom_algorithms (workflow_id);

CREATE INDEX IF NOT EXISTS idx_execution_algorithm ON algorithm_executions (custom_algorithm_id, started_at);

CREATE INDEX IF NOT EXISTS idx_log_execution_seq ON execution_logs (execution_id, seq);

CREATE INDEX IF NOT EXISTS idx_metric_lookup ON metric_series (execution_id, metric_name, step);
