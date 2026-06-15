# API 压测记录

本文档记录压测方法，不预填未经执行的性能数字。

## 准备

启动本地服务：

```bash
prompt-opt serve --host 127.0.0.1 --port 8000
```

准备请求体：

```bash
cat > /tmp/optimize.json <<'JSON'
{"prompt":"你是后端工程师，请生成一个接口设计，包含输入输出和错误处理。","provider":"offline"}
JSON
```

## hey

```bash
hey -n 200 -c 20 -m POST -H "Content-Type: application/json" -D /tmp/optimize.json http://127.0.0.1:8000/api/optimize
```

记录实际输出中的 QPS、平均耗时、P95/P99，再写入简历或 README。

## Locust

可用 Locust 覆盖登录、优化、历史查询和导出链路。提交压测结果前应记录机器配置、并发数、样本数、Provider 类型和数据库位置。
