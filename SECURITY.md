# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in grai.build, please report it responsibly.

### How to Report

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email security concerns to: hello@grai.build
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Initial Assessment**: Within 5 business days
- **Resolution Timeline**: Depends on severity, typically:
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release

### Scope

Security issues we're interested in:
- Code injection vulnerabilities
- Authentication/authorization bypasses
- Sensitive data exposure
- Cypher injection in generated queries
- Dependency vulnerabilities

### Recognition

We appreciate responsible disclosure and will:
- Credit reporters in release notes (unless anonymity is requested)
- Work with you on timing of public disclosure

## Security Best Practices

When using grai.build:

1. **Neo4j Credentials**: Never commit credentials. Use environment variables:
   ```bash
   export NEO4J_URI=bolt://localhost:7687
   export NEO4J_USER=neo4j
   export NEO4J_PASSWORD=your-password
   ```

2. **Schema Validation**: Always run `grai validate` before deploying to production

3. **Dry Run**: Use `--dry-run` flags to preview changes before applying

4. **Access Control**: Ensure proper Neo4j RBAC is configured for production databases
