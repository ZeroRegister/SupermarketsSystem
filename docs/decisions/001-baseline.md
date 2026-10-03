# ADR 001: baseline and assumptions

Status: accepted, 2026-10-04. The requester authorized autonomous implementation and instructed us to use placeholders for personal and institutional fields.

Use a single-store modular monolith, Java 21 and Spring Boot 3.5, Vue 3 with TypeScript, MySQL 8.4 LTS, Redis 7.4 and Flyway migrations. Include suppliers and warning acknowledgement. Fixed roles are permission bundles; administrators assign users to bundles rather than editing arbitrary permission expressions. Prices are decimal values in a single configurable display currency; stock quantities are whole units. No multi-store, payment, accounting or forecasting claims.

Sessions and CSRF protection are used instead of browser-stored bearer tokens. MySQL remains authoritative. Pessimistic row locks serialize a product's stock changes. Idempotency keys are scoped by actor with a canonical payload comparison. Warnings are persisted episodes; acknowledgements never change stock. A committed database revision namespaces short-lived Redis warning pages, preventing stale repopulation under a newer revision.

Use the standard LaTeX `report` class with a locally authored, MIT-licensed layout rather than adopting an unrelated institution's branding. pdfLaTeX, A4, 25 mm margins, one-and-a-half body spacing, numeric bibliography, front matter, appendices and standard float packages compile offline with TeX Live 2025. University formatting, degree, author and supervisor remain explicit placeholders. No institutional compliance is claimed.

Validation environment is this macOS host with local container services, not a store trial. Latency is exploratory descriptive evidence; no user study, production SLA or statistical population inference is assumed. Source/PDF publication policy: commit editable source, stable figures and raw evaluation data; attach the final PDF as a release asset rather than tracking TeX intermediates.
