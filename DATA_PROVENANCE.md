# Data provenance and limitations

Ghost Network India is a network-resilience **simulation**, not a live telecom monitoring system.

## What is real and what is simulated?

- The 127-city registry and coordinates are location references maintained in `app.py`.
- By default, graph edges are generated as a deterministic illustrative topology. They are not claims about deployed fibre, carrier routes, or physical links.
- Latency, packet loss, congestion, reliability, risk scores, and failure events are illustrative synthetic values.
- Recovery timings are local Python algorithm timings, not carrier/network recovery measurements.
- The trend forecast and synthetic stress-test evaluation are heuristics over generated data, not validated real-world predictive performance.

## Importing externally sourced city links

Add rows to `data/real_city_links.csv` with these columns:

`city_a,city_b,source,source_url,observed_at`

Both city names must exactly match names in the existing 127-city registry. Every row must include a source name and URL. The app will mark these edges as `EXTERNAL_DATASET_TOPOLOGY`. This label applies only to the existence of the supplied topology relationship; the edge's latency, packet loss, congestion, reliability, and risk values remain synthetic unless separately measured and connected.

Do not translate autonomous-system (AS) relationships into city-to-city telecom links without a documented mapping. A public topology dataset can be real while still not supporting a claim about a particular Indian city pair.
