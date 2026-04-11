---
title: License Compliance
impact: HIGH
impactDescription: License violations can force open-sourcing proprietary code or trigger legal liability
tags: licenses, compliance, gpl, spdx, copyleft, legal
---

# License Compliance

## License Classification

### Permissive

No restrictions on use in proprietary software. Safe for all projects.

- **MIT**: do anything, keep copyright notice
- **Apache-2.0**: MIT + patent grant + state changes
- **BSD-2-Clause**: MIT equivalent, different wording
- **BSD-3-Clause**: BSD-2 + no endorsement clause
- **ISC**: MIT equivalent, simpler wording
- **0BSD**: public domain equivalent
- **Unlicense**: public domain dedication

### Copyleft (Weak)

Modifications to the library itself must be open-sourced, but your application code is not affected.

- **LGPL-2.1 / LGPL-3.0**: dynamically link freely, static linking has requirements
- **MPL-2.0**: file-level copyleft -- modified files must be shared, rest of your code is unaffected
- **EPL-2.0**: similar to MPL, Eclipse ecosystem

### Copyleft (Strong)

Derivative works must be distributed under the same license. Using these in proprietary software is a legal risk.

- **GPL-2.0 / GPL-3.0**: any linked code becomes GPL-covered
- **AGPL-3.0**: GPL + network use triggers distribution (SaaS counts)
- **SSPL**: MongoDB's license, controversial, not OSI-approved
- **EUPL-1.2**: EU copyleft, compatible with GPL

### Proprietary / Non-Free

Cannot be used without a commercial license.

- **BSL (Business Source License)**: free for non-production, paid for production
- **Commons Clause**: restricts selling the software
- **Elastic License 2.0**: restricts managed service offering
- **No License**: all rights reserved by default -- cannot legally use

## GPL Contamination

GPL's copyleft is **transitive**. If any dependency in your tree is GPL, the entire application may need to be GPL-licensed. This applies to:

1. Direct dependencies linked at compile time
2. Transitive dependencies pulled in by direct dependencies
3. Code copied from GPL projects (even a single function)

**Does NOT apply to**:
- Separate processes communicating via pipes, sockets, or HTTP (generally safe)
- System libraries (GPL system library exception)
- Development-only dependencies (test frameworks, linters) -- they are not distributed

**Detection**:
```bash
# JavaScript
npx license-checker --summary
npx license-checker --failOn "GPL-2.0;GPL-3.0;AGPL-3.0"

# Python
pip-licenses --format=table
pip-licenses --fail-on="GPL-2.0;GPL-3.0"

# Rust
cargo-license
cargo deny check licenses

# Go
go-licenses check ./...

# Elixir
# No standard tool -- check hex.pm pages manually or use mix deps | grep License

# Ruby
license_finder
```

## Conflict Detection

License conflicts occur when two dependencies impose incompatible requirements:

- **GPL-2.0 + Apache-2.0**: incompatible (GPL-2.0 only, Apache-2.0 patent clause conflicts)
- **GPL-3.0 + Apache-2.0**: compatible (resolved in GPL-3.0)
- **MIT + anything permissive**: always compatible
- **AGPL-3.0 + proprietary**: incompatible for any distribution or network use

When conflicts are found:
1. Check if the conflicting dependency can be replaced
2. Check if the dependency offers dual licensing
3. Consult legal counsel for edge cases

## SPDX Identifiers

Always use SPDX identifiers (https://spdx.org/licenses/) for unambiguous license references. Examples:

- `MIT` not "MIT License" or "Expat"
- `Apache-2.0` not "Apache License 2.0"
- `GPL-3.0-only` vs `GPL-3.0-or-later` (important distinction)
- `UNLICENSED` = proprietary (npm convention)
- `NOASSERTION` = license not determinable

Compound expressions: `MIT OR Apache-2.0` (dual license, user chooses), `MIT AND BSD-2-Clause` (both apply).
