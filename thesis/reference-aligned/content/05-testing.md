# System testing and evaluation
## Evaluation questions and evidence organization
Evaluation addresses the four questions introduced at the beginning of the thesis. Functional tests examine whether stock changes are bounded and attributed. Concurrency and replay tests examine whether repeated or competing intentions produce acceptable results. Warning tests examine the separation of severity, recovery and review. Browser checks examine presentation and navigation. Local measurements and recorded failure scenarios examine the optional cache path and durable state.

The evidence has several dates and purposes. The backend and frontend result images included here are from 5 October 2026. The original browser acceptance record and performance and recovery records are dated 3 October UTC, corresponding to the local development session that produced them. A later capture run on 5 October obtains the expanded interface collection without posting new business data. These records are not interchangeable samples of one experiment.
@table evidence-dates|Evaluation evidence and its scope
Evidence | Recorded date | What it establishes
Backend result log | 5 October 2026 local time | Twenty-seven integration cases completed without failures
Frontend result log | 5 October 2026 local time | Three threshold presentation tests passed
Original browser journey | 3 October 2026 UTC | Fourteen checks including one receipt and one acknowledgement
Expanded figure capture | 5 October 2026 UTC | Twenty-seven captures role guard checks and no page runtime errors
Warning-query benchmark | 3 October 2026 UTC | Six hundred sequential measured samples per mode
Redis interruption | 3 October 2026 UTC | Equivalent warning result during the recorded cache outage
Restart fingerprint | Preserved repository record | Equal selected product and transaction rows after restart

The prototype uses fictitious records and local services. Tests can provide strong evidence for a specified invariant while still leaving practical questions unanswered. In particular, the study does not measure store-user learning, business losses avoided, supplier lead times or production capacity. The result discussion keeps the units and scope of each claim aligned with the recorded procedure.
## Backend integration testing
### Environment and case coverage
The backend test class uses Testcontainers to create MySQL and Redis instances for the test execution. Its dynamic properties direct the Spring application to those instances. This is valuable because locking, uniqueness and persistence behavior involve the actual database rather than an in-memory substitute. It does not mean that every production database setting or fault mode is reproduced.

The 27 cases cover authentication, CSRF, role restrictions, catalogue validation, quantity changes, audit history, retry behavior, concurrency, shortage transitions, review and account safeguards. The result in {fig:backend-result} reports zero failures, errors and skipped tests. A passing suite means that those executable assertions held in this run. It is not a numerical code-coverage percentage or a proof that all possible requests are correct.
@fig backend-result|evidence/01-backend-tests.png|Backend integration result from the 5 October 2026 execution
@table backend-groups|Main backend acceptance groups
Group | Representative assertions | Reported outcome
Authentication | Anonymous denial invalid credentials and missing login fields | Passed
Authorization | Clerk review denial manager posting denial and threshold boundary | Passed
Catalogue | Unique SKU valid threshold hierarchy and archived movement denial | Passed
Stock arithmetic | Receipt dispatch signed adjustment absolute count and zero count | Passed
Audit behavior | Before and after history and unchanged stocktake observation | Passed
Retries | Equal replay identifier and changed-payload conflict | Passed
Concurrency | No overselling identical submission and first reviewer preservation | Passed
Warnings | Zero equality healthy recovery severity renewal and accurate filters | Passed
Administration | Last enabled administrator cannot be disabled or demoted | Passed
### Negative-stock and audit consistency
The insufficient-stock test attempts a dispatch from an empty product. It expects a domain exception, unchanged transaction count and unchanged quantity. This checks both the arithmetic boundary and the absence of an accepted history row for a rejected operation. The receipt-and-dispatch test then verifies a valid sequence: before zero, receipt eight, dispatch three and final quantity five with two movements.

The absolute-count cases verify the semantic distinction from a relative adjustment. Starting at ten, an adjustment of negative two produces eight; counting three then produces delta negative five and after quantity three. Counting to zero is also accepted and auditable. An unchanged count creates a zero-delta history row. These cases would not be equivalent to a generic test that an input number can be stored in a product field.
### Duplicate and concurrent requests
The exact-replay case sends the same actor-scoped request twice and checks the same movement identifier and one stock effect. A changed quantity with that key produces a conflict. These assertions connect the returned response to the stored result rather than merely checking that the server returns a success status.

The concurrency source in {fig:concurrency-code} shows two demanding scenarios. Twelve unit dispatch attempts compete for a starting balance of seven; the test expects exactly seven successes and quantity zero. Four concurrent identical stock-in submissions must produce one identifier and quantity four. Those bounds directly test the intended outcome under the selected same-product workload.
@fig concurrency-code|code/12-code-concurrency-tests.png|Actual concurrent dispatch and identical-submission integration cases

The tests do not establish fairness, sustained throughput or behavior under every lock timeout. The shared revision row can serialize parts of writes across different products. Cross-product reuse of one actor-key pair and database deadlocks require additional targeted cases. MySQL's documentation treats deadlocks as a transaction condition that applications must consider [@mysql-deadlocks]; the current service does not advertise an automatic deadlock-retry policy.
### Warning and review assertions
The threshold test verifies OUT at zero and LOW at exact positive equality. Healthy replenishment removes the active shortage and creates RESTOCKED. A review test verifies that acknowledgement becomes visible through the cache and leaves quantity zero. The concurrent-review case expects both responses to expose the same first reviewer. Archive cases confirm that the product rejects movements and its open warnings are resolved.

The test named for restocked expiry and new shortage exercises renewed shortage after replenishment. It does not advance a clock through twenty-four hours. Its supported conclusion is that a new shortage closes the active recovery episode and opens OUT. Time-based expiry, periodic cleanup and a cached page around the expiry boundary remain incompletely evaluated. This distinction prevents a descriptive test name from becoming stronger evidence than its assertions provide.
## Frontend and browser testing
### Threshold presentation
The frontend unit tests check the zero boundary, exact threshold equality and positive healthy stock. The source in {fig:frontend-test-code} makes those values visible. The result in {fig:frontend-result} confirms three passing cases. The tests protect the labels shown beside quantity so that the browser does not contradict the server's fundamental classification.
@fig frontend-test-code|code/13-code-boundary-tests.png|Frontend test inputs for zero equality and healthy stock
@fig frontend-result|evidence/02-frontend-tests.png|Frontend unit-test result from the current execution

These are small focused tests. They do not cover every modal, asynchronous loading state or component interaction. The broader browser journeys serve a complementary purpose by opening the application and observing rendered behavior. Neither layer establishes full accessibility conformance or practical usability for store employees.
### Earlier operational browser journey
The preserved earlier browser record contains fourteen checks with zero JavaScript runtime errors. It covers administrator login and operational views, an empty search, an actual receipt submission with the correct delta, clerk and manager navigation restrictions, managerial acknowledgement and phone-sized viewport containment. Its write operations make it stronger evidence of an interface-to-server journey than a collection of screenshots alone.

The empty-result interface in {fig:empty-ui} illustrates the recovery state used by the search check. It presents an explanation and a way to clear filters. A successful empty selection should not be confused with a failed request; error handling and query results represent different conditions in the application.
@fig empty-ui|ui/13-empty-search.png|Empty inventory search with a visible recovery action
### Expanded capture verification
The later capture run obtains twenty-seven interfaces and forms. It signs in as all three roles, checks that managers cannot reach staff administration and clerks cannot reach the warning board, and checks document width at 390 pixels. It records zero page runtime errors. The verification image in {fig:browser-result} identifies this capture-specific evidence.
@fig browser-result|evidence/03-browser-verification.png|Capture-run checks and the absence of posted business changes

The capture process opens forms and fills drafts but does not submit stock, account or catalogue changes. Receipt and dispatch images therefore demonstrate the implemented controls and labels, not additional accepted movements. The thesis uses the earlier operational journey and backend cases when discussing accepted writes. This separation allows screenshots to remain useful without assigning them evidential weight they do not have.
## Performance test of the warning query
### Workload and measurement procedure
The performance record compares the warning query with cache enabled and with cache bypassed. It uses sixteen products, sixteen open warning episodes, page size one hundred and concurrency one. Three rounds alternate the mode order. Each mode receives twenty warm-up requests and two hundred measured requests per round, giving six hundred measured samples for each mode. Results include the local HTTP path rather than isolated Redis or MySQL operation time.

The recorded host is Apple Silicon macOS with MySQL and Redis containers accessed over loopback. The script records the operating system, machine type, Python version and backend/database baseline. Authentication, durable revision retrieval, filtering, serialization and network handling can contribute to each response. A cache hit therefore avoids only part of the total request work.
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

The benchmark is preserved evidence, not a newly executed production experiment. The inclusion of warm-up and alternating order improves interpretability, but it does not remove all variation due to the host, containers or background activity. No simultaneous-user or capacity curve can be inferred from sequential requests.
### Descriptive latency results
The summary in {tab:latency} reports pooled median and tail percentiles from the preserved samples. Percentiles use the sorted-sample index implemented by the project's evaluation script. The Redis-enabled path has a median of approximately 5.33 ms, compared with approximately 6.56 ms for bypass. Its p95 is approximately 7.57 ms, compared with 8.11 ms. These are measurements in this particular run, not latency targets guaranteed by the architecture.
@table latency|Warning-query latency from six hundred samples per mode
Mode | Samples | Median ms | p95 ms | p99 ms
Redis enabled | 600 | 5.33 | 7.57 | 8.87
MySQL bypass | 600 | 6.56 | 8.11 | 9.42

The bar chart in {fig:latency-summary} presents the same descriptive statistics. It helps separate the typical result from the upper-tail values. The approximately 1.24 ms difference between pooled medians is small in absolute terms. It is associated with the optional cache path under this dataset, while the benchmark includes costs that the cache cannot remove.
@fig latency-summary|evidence/04-latency-summary.png|Pooled local median and tail latency for cached and bypass warning queries

The empirical cumulative distribution in {fig:latency-ecdf} shows the proportion of measured responses below each latency. It reveals overlapping distributions instead of implying that every cached request is faster than every bypass request. The plotted tail also makes occasional slower observations visible. No statistical hypothesis test or confidence interval is reported.
@fig latency-ecdf|evidence/05-latency-ecdf.png|Empirical distribution of the preserved warning-query latencies

The box plot in {fig:latency-box} shows variability and outlying observations. Those observations should not be silently removed merely to improve the visual result. They also should not be generalized into a production reliability rate. The sample is small in business scope and restricted to one read operation with sequential local traffic.
@fig latency-box|evidence/06-latency-boxplot.png|Local latency variability including observed outliers
### Interpretation and remaining performance work
The cache reduces repeated page assembly in the tested workload, but each read still obtains a durable revision and checks session authority. A high cache-hit ratio is not equivalent to eliminating database access. The prototype's write path also advances a shared revision row. Testing many writers across different products is therefore a necessary next step before drawing conclusions about larger-store workload behavior.

Useful extensions would vary catalogue size, warning count, page size, concurrent readers and concurrent writers. They would report warm and cold cache behavior, latency distributions, rejected requests and database resource use. A production comparison should control relevant deployment variables and preserve raw samples. These proposed tests describe additional evaluation, not results already obtained.
## Recorded failure and persistence checks
The Redis recovery record stops and restarts only the cache service while MySQL remains available. A cache-enabled query during interruption is compared with the uncached baseline. The record reports the same database warning result during the outage and a recovered service afterward. Individual observed query times are approximately 10.49 ms before interruption, 12.25 ms while unavailable and 25.94 ms after recovery. They are individual observations, not estimates of a recovery-time distribution.
@table recovery|Recorded cache interruption and restart observations
Observation | Recorded result | Supported interpretation
Redis stopped with MySQL available | Same warning result | Cache outage did not remove authoritative warning data
Redis restarted | Recovered service and equivalent result | Normal cache service resumed in this check
Application restarted | Same selected stock and movement rows | Durable MySQL state survived ordinary process restart
Selected-row fingerprint | 34 rows and equal SHA-256 | Compared product and transaction data remained equal

A separate persistence record compares selected product and transaction rows around an application restart using a fingerprint. It reports equality for thirty-four selected rows. This supports ordinary persistence of those records. It is not a backup restoration, disk-failure or full-database recovery test. Session survival is also a different property: the in-process login state may be lost while stock remains durable.
## Traceability and validity of the conclusions
The acceptance evidence is strongest where a requirement has a direct assertion. Non-negative concurrent stock has a final balance and a success-count check. Exact replay has an identifier and quantity check. Acknowledgement has a reviewer and unchanged-stock check. Weaker or absent evidence is identified separately, including complete expiry timing, sustained multi-user workload and operational usability.

Internal validity is limited by the particular test scenarios and the execution environment. External validity is limited by demonstration data and the single-store boundary. Construct validity depends on using the intended metric: movement counts are not sales, current-price value is not profit, and response latency under one sequential query is not throughput capacity. The thesis maintains those distinctions throughout its figures and result tables.

The current evidence supports a working bounded inventory system with selected consistency and recovery properties. It does not establish a production SLA, a quantified reduction in supermarket stockouts or the safety of unrestricted public deployment. Those conclusions require additional operational controls, workloads and field observations beyond this development study.
## Chapter summary
Functional tests support the implemented stock arithmetic, audit path, role boundaries and selected warning transitions. Browser evidence supports the rendered workflow and selected operational journeys. The local cache benchmark reports a lower pooled median for the enabled path under a small sequential workload. Failure records support cache fallback and ordinary persistence. The following conclusion relates these findings to the original engineering questions and identifies the next work needed for a broader deployment.
