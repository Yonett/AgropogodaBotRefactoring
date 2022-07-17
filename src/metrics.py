from prometheus_client import Counter
from labels import Labels

fails_counter = Counter('bot_fails', 'Counter of internal fails')
commands_counter = Counter('bot_commands', 'Number of issued commands', ['command'])

[commands_counter.labels(f"{label.value}") for label in Labels]
