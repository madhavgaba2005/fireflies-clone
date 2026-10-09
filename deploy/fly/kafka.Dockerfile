# Kafka for Fly.io. Fly volumes are mounted root-owned, so the broker runs as root inside its own
# private microVM (it publishes no ports to the internet; only the Fly private network reaches it).
FROM apache/kafka:3.9.1
USER root
