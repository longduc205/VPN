class DummyMetric:
    """Mock metric class to avoid dependency crashes for prometheus_client."""
    def inc(self, *args, **kwargs):
        pass

    def observe(self, *args, **kwargs):
        pass

    def labels(self, *args, **kwargs):
        return self


GENERATED_CONFIGS_COUNT = DummyMetric()
REQUEST_COUNT = DummyMetric()
REQUEST_LATENCY = DummyMetric()
LOGIN_SUCCESS_COUNT = DummyMetric()
LOGIN_FAILURE_COUNT = DummyMetric()
ACTIVE_SESSIONS_GAUGE = DummyMetric()
