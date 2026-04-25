# Engine API

## Engine

::: protokol.Engine

### Retry Strategies

The engine accepts a `retry_strategy` argument that implements `protokol.engine.retry.RetryStrategy`. Three strategies ship out-of-the-box:

| Strategy | Behavior | When to use |
| --- | --- | --- |
| `SimpleRetryStrategy` | Retries until `max_retries` regardless of exception type. | Default option for most use cases where temporary LLM/tool failures should be retried. |
| `ExceptionRetryStrategy` | Retries only when the raised exception matches `retry_for`. | When certain errors (e.g., timeouts) should retry but validation errors should fail fast. |
| `NoRetryStrategy` | Never retries and surfaces the first exception. | For deterministic pipelines where retries should be handled outside Protokol. |

You can also implement your own strategy by subclassing `RetryStrategy` and overriding `should_retry(attempt, error) -> bool`.