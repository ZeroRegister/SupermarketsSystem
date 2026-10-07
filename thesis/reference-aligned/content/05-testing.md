# System testing and evaluation
## Evaluation questions and evidence organization
The evaluation follows the four questions posed in the introduction. Functional tests check that stock changes are bounded and attributed; replay and concurrency tests check that repeated or competing intentions produce acceptable outcomes; warning tests check that severity, recovery and review stay separate; browser checks examine presentation and navigation; and local measurements and failure scenarios examine the optional cache path and the durability of state.

The evidence was collected at different times and for different releases, as {tab:evidence-dates} shows. The backend integration suite and the frontend threshold tests were rerun against the current source on 7 October 2026. The original browser journey, the benchmark and the recovery records date from 3 October (UTC), and the current interface collection was captured on 6–7 October local time (6 October UTC). The interface images therefore illustrate the recorded application, while the current backend assertions establish the behavior of the expanded batch, purchasing and review workflows.
@table evidence-dates|Evaluation evidence and its scope
Evidence | Recorded date | What it establishes
Backend result log | 7 October 2026 local time | Forty-five integration cases completed without failures
Frontend result log | 7 October 2026 local time | Three threshold presentation tests passed
Original browser journey | 3 October 2026 UTC | Fourteen checks including one receipt and one acknowledgement
Expanded figure capture | 6 October 2026 UTC | Thirty captures, role guard checks and no page runtime errors
Warning-query benchmark | 3 October 2026 UTC | Six hundred sequential measured samples per mode
Redis interruption | 3 October 2026 UTC | Equivalent warning result during the recorded cache outage
Restart fingerprint | Preserved repository record | Equal selected product and transaction rows after restart

All tests use fictitious records and local services. They can establish a specified invariant convincingly while leaving practical questions open: the study does not measure how quickly store staff learn the system, which losses it avoids, supplier lead times or production capacity. Each claim below is stated in the units and scope of the procedure that produced it.
## Backend integration testing
### Environment and case coverage
The backend tests use Testcontainers to start disposable MySQL and Redis instances [@testcontainers], and dynamic properties point the Spring application at them. Locking, uniqueness and persistence assertions therefore run against a real MySQL server rather than an in-memory substitute. The test configuration and synthetic dataset define the environment these results represent.

The current suite contains 45 cases covering authentication, CSRF, role restrictions, catalog validation, quantity changes, audit history, retries, concurrency, shortage transitions, batch allocation, expiry policy, slow-moving detection, purchase approval, partial receipts, stock reviews and account safeguards. {fig:backend-result} shows the dated run, which completed with no failures, errors or skipped tests. {tab:backend-groups} groups the principal assertions, and Appendix B lists every case with the behavior it checks.
@fig backend-result|evidence/01-backend-tests.png|Backend integration result from the 7 October 2026 execution
@table backend-groups|Main backend acceptance groups
Group | Representative assertions | Reported outcome
Authentication | Anonymous denial, invalid credentials and missing login fields | Passed
Authorization | Clerk review denial, manager posting denial and threshold boundary | Passed
Catalog | Unique SKU, valid threshold hierarchy and archived movement denial | Passed
Stock arithmetic | Receipt, dispatch, signed adjustment, absolute count and zero count | Passed
Audit behavior | Before-and-after history and unchanged stocktake observation | Passed
Retries | Equal replay identifier and changed-payload conflict | Passed
Concurrency | No overselling, single identical submission and first-reviewer preservation | Passed
Warnings | Zero, equality, healthy recovery, severity renewal and accurate filters | Passed
Administration | Last enabled administrator cannot be disabled or demoted | Passed
### Negative-stock and audit consistency
The insufficient-stock test attempts to dispatch from an empty product and expects a domain exception with both the transaction count and the quantity unchanged. It thus checks the arithmetic boundary and, equally important, that a rejected operation leaves no accepted history row. The receipt-and-dispatch test then verifies a valid sequence: from zero, a receipt of eight and a dispatch of three leave a final quantity of five and exactly two movements.

The absolute-count cases verify that a stocktake means something different from an adjustment. Starting at ten, an adjustment of minus two yields eight; a subsequent count of three yields a delta of minus five and an after quantity of three. A count of zero is accepted and recorded, and an unchanged count creates a zero-delta row. A generic test that a number can be stored in a product field would capture none of these distinctions.
### Duplicate and concurrent requests
The exact-replay case sends the same actor-scoped request twice and checks that both responses carry the same movement identifier and that stock changed only once; reusing the key with a different quantity produces a conflict. These assertions tie the response to the stored result instead of merely checking for a success status.

{fig:concurrency-code} shows the two concurrency scenarios. In the first, twelve single-unit dispatches compete for a balance of seven, and the test requires exactly seven successes and a final quantity of zero. In the second, four identical stock-in submissions arrive concurrently and must produce one identifier and a quantity of four. Both directly test the intended outcome for concurrent requests on a single product.
@fig concurrency-code|code/12-code-concurrency-tests.png|Actual concurrent dispatch and identical-submission integration cases

These tests do not establish fairness, sustained throughput or the behavior under every lock timeout. The shared revision row may also serialize parts of writes to different products. Reusing one actor key across products and provoking database deadlocks would need further targeted cases; MySQL treats deadlocks as a normal transactional condition that applications must be prepared to handle [@mysql-deadlocks], and the current service has no automatic deadlock-retry policy.
### Warning and review assertions
The threshold test confirms OUT at zero and LOW at exact positive equality, and a healthy replenishment removes the active shortage and opens RESTOCKED. Expiry tests confirm the inclusive expiry-day boundary in the configured timezone. The slow-moving test confirms that only sales count: an ordinary dispatch leaves the open SLOW episode with the same identifier, and only a SALE clears it. A review test shows that an acknowledgement becomes visible through the cache while the quantity stays at zero, and the concurrent-review case requires both responses to report the same first reviewer. Archive cases confirm that an archived product rejects movements and that its open warnings are resolved.

The recovery test named after RESTOCKED expiry actually exercises a renewed shortage after replenishment, while separate expiry tests cover business-day boundaries, rejection of an invalid timezone and expiry-aware sellable balances. None of them measures the reliability of the scheduler over long periods. The supported conclusion is that the rules behave as specified at the tested boundaries; longer-running clock, cache and scheduling workloads remain future work.
## Batch, purchasing and review workflow testing
The expanded backend cases cover receipt metadata on replay, concurrent receipts, FEFO allocation of dated batches, exclusion of expired or quarantined batches, and disposal approval after a batch remainder has changed. The FIFO fallback for undated stock, implemented as ordering by receipt time and identifier, was verified by source inspection rather than by a dedicated test. Together, the assertions connect physical stock, sellable stock and the retained batch allocations.

Purchase tests cover multi-line drafts, rejection and editing, completion, partial receipt, receipt replay, cancellation and concurrent approval. Because approval rechecks the current replenishment suggestion, and because each receipt is both a purchasing event and an audited stock movement, a replayed receipt must create neither a second batch nor a second movement—which the tests confirm.

Stock-review tests cover count and disposal submissions, stale snapshots, idempotent submission, long but bounded reasons and role denials. A COUNT is approved only against an unchanged quantity and version snapshot, a DISPOSAL only within the selected batch's remainder, and an ADJUSTMENT is applied to the current locked balance. These executable cases are far stronger evidence for the review workflow than a screenshot of its buttons, although they remain synthetic single-store scenarios.
## Frontend and browser testing
### Threshold presentation
The frontend unit tests in frontend/src/inventory.spec.ts check the labels for zero stock, exact threshold equality and healthy stock, ensuring that the browser classifies stock exactly as the server does. {fig:frontend-result} shows the three passing cases.
@fig frontend-result|evidence/02-frontend-tests.png|Frontend threshold-test result from the 7 October 2026 execution

These focused tests do not cover every dialog, loading state or component interaction. The browser journeys complement them by opening the running application and observing its rendered behavior, though neither layer establishes full accessibility conformance or practical usability for store employees.
### Earlier operational browser journey
The earlier browser record contains fourteen checks and no JavaScript runtime errors. It covers administrator sign-in and the operational views, an empty search, an actual receipt submission with the correct delta, the navigation restrictions for clerks and managers, a managerial acknowledgement and the containment of content in a phone-sized viewport. Because it performs real writes, it provides stronger evidence of an end-to-end journey than screenshots alone. Its empty-search check confirms that a successful query without matches is distinguished from a failed request and offers a filter reset; the corresponding image is part of the supplementary collection.
### Expanded capture verification
The later capture run records thirty interfaces and forms. It signs in under all three roles, confirms that managers cannot reach staff administration and that clerks cannot reach the warning board, checks the document width at 390 pixels and records no runtime errors on any page. {fig:browser-result} summarizes these checks.
@fig browser-result|evidence/03-browser-verification.png|Capture-run checks and the absence of posted business changes

The capture run opens forms and fills in drafts but never submits stock, account or catalog changes. Its images document controls, labels and layout, whereas evidence for accepted writes comes from the earlier browser journey and the backend integration cases.
## Performance test of the warning query
### Workload and measurement procedure
The performance record compares the warning query with the cache enabled and with the cache bypassed, using the workload in {tab:benchmark-workload}: sixteen products, sixteen open warning episodes, a page size of one hundred and one request at a time. Three rounds alternate the order of the two modes; in each round, each mode receives twenty warm-up requests followed by two hundred measured ones, giving six hundred measured samples per mode. The timings cover the full local HTTP path, not isolated Redis or MySQL operations.

The host was an Apple Silicon Mac running MySQL and Redis in containers reached over loopback, and the script records the operating system, machine type, Python version and backend and database baseline. Authentication, reading the durable revision, filtering, serialization and network handling all contribute to each response, so a cache hit saves only part of the work.
@table benchmark-workload|Recorded local benchmark workload
Parameter | Value
Products | 16
Open warning episodes | 16
Page size | 100
Concurrent requests | 1
Alternating measurement rounds | 3
Warm-up requests per mode per round | 20
Measured requests per mode per round | 200
Pooled measured samples per mode | 600
Network and service placement | Loopback HTTP and local Colima containers

The benchmark is preserved from that run rather than newly executed. Warm-up and alternating order make its results easier to interpret but cannot remove all variation caused by the host, the containers or background activity, and sequential requests reveal nothing about concurrent users or capacity.
### Descriptive latency results
{tab:latency} reports the pooled median and tail percentiles of the preserved samples, computed with the sorted-sample index of the project's evaluation script. With Redis enabled, the median latency is about 5.33 ms against 6.56 ms for the bypass path, and the 95th percentile is about 7.57 ms against 8.11 ms. These values describe this run; they are not latency targets guaranteed by the architecture.
@table latency|Warning-query latency from six hundred samples per mode
Mode | Samples | Median ms | p95 ms | p99 ms
Redis enabled | 600 | 5.33 | 7.57 | 8.87
MySQL bypass | 600 | 6.56 | 8.11 | 9.42

{fig:latency-summary} presents the same statistics as a bar chart, separating typical from upper-tail behavior. The difference between the pooled medians, about 1.24 ms, is small in absolute terms, partly because the measured path includes costs that the cache cannot remove.
@fig latency-summary|evidence/04-latency-summary.png|Pooled local median and tail latency for cached and bypass warning queries

The empirical cumulative distribution in {fig:latency-ecdf} plots, for every latency, the fraction of responses at or below it, and so retains every observation. The two distributions overlap, and both upper tails contain occasional slow responses. The comparison is descriptive: no hypothesis test or confidence interval is reported. A box plot of the same samples is included in the supplementary material.
@fig latency-ecdf|evidence/05-latency-ecdf.png|Empirical distribution of the preserved warning-query latencies
### Interpretation and remaining performance work
In the tested workload the cache avoids repeated page assembly, but every read still fetches the durable revision and checks session authority, so a high hit ratio does not mean that the database is bypassed. Because the write path also advances a shared revision row, testing many concurrent writers across different products is a necessary step before drawing conclusions for a larger store.

A fuller study would vary catalog size, warning count, page size and the numbers of concurrent readers and writers, and would report warm and cold cache behavior, latency distributions, rejected requests and database resource use, with raw samples preserved. These are proposals for further evaluation, not results obtained here.
## Recorded failure and persistence checks
The Redis recovery check stops and restarts only the cache service while MySQL stays available, comparing a cache-enabled query during the outage with the uncached baseline. During the outage the query returned the same warning result from the database, and the cache service recovered afterwards. The individual query times observed were about 10.49 ms before the interruption, 12.25 ms during it and 25.94 ms after recovery; as single observations, they say nothing about the distribution of recovery times. {tab:recovery} summarizes the checks.
@table recovery|Recorded cache interruption and restart observations
Observation | Recorded result | Supported interpretation
Redis stopped with MySQL available | Same warning result | Cache outage did not remove authoritative warning data
Redis restarted | Recovered service and equivalent result | Normal cache service resumed in this check
Application restarted | Same selected stock and movement rows | Durable MySQL state survived ordinary process restart
Selected-row fingerprint | 34 rows and equal SHA-256 | Compared product and transaction data remained equal

A separate persistence check fingerprints selected product and transaction rows before and after an application restart and finds all thirty-four rows equal. This supports the ordinary persistence of those records, but it is not a test of backup restoration, disk failure or full database recovery. Sessions behave differently: in-process login state may be lost on restart even though stock data persists.
## Traceability and validity of the conclusions
The evidence is strongest where a requirement maps to a direct assertion: non-negative stock under concurrency is checked through the final balance and the number of successes, exact replay through the identifier and quantity, batch allocation through sellable balances and remainders, purchase approval through recheck, receipt and replay assertions, and acknowledgement and review through reviewer and snapshot checks. Sustained multi-user workload, supplier integration and operational usability, by contrast, have weak or no evidence and are reported as such.

Internal validity is limited by the chosen test scenarios and the execution environment, and external validity by the demonstration data and the single-store boundary. Construct validity depends on measuring what is intended: movement counts are not sales, current-price value is not profit, and the latency of one sequential query is not throughput capacity. The figures and result tables observe these distinctions throughout.

In summary, the evidence supports the specified stock, authorization, warning and recovery behavior in local single-store scenarios. Generalizing beyond them is limited by synthetic data, selected concurrency patterns and a sequential benchmark of a single read operation. Production capacity, reduced stockouts and employee usability would require broader workloads and evaluation in an operating store, and deployment security and recovery would need assessment beyond a cache interruption and a process restart.
## Chapter summary
Functional tests support the implemented stock arithmetic, audit path, role boundaries and warning transitions, and browser evidence supports the rendered workflow and selected end-to-end journeys. Under a small sequential workload, the cache-enabled warning query shows a lower pooled median latency, and the failure records support the cache fallback and ordinary persistence. The conclusion relates these findings to the research questions and outlines the work needed for a broader deployment.
