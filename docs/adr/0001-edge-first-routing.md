# ADR-0001: Edge-first 80/20 routing

- Status: Accepted
- Date: 2026-08-06

## Context

Most ordinary questions should not consume the Xeon research core. The client must decide whether a task can use a direct provider or needs local specialist processing.

## Decision

Use deterministic client-side routing. Public tasks default to a configured cloud provider. Evidence markers, confidential content, and specialist profiles route to the Xeon API.

## Consequences

The Xeon remains available for high-value workloads. Provider adapters remain replaceable. Policy tests become part of the security boundary.
