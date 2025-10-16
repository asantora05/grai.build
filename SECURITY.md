# Security Policy

## 🔒 Supported Versions

We provide security updates for the following versions of grai.build:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## 🐛 Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. **DO NOT** Create a Public Issue

Please do not report security vulnerabilities through public GitHub issues.

### 2. Report Privately

**Preferred Method:** Use [GitHub Security Advisories](https://github.com/asantora05/grai.build/security/advisories/new)

**Alternative:** Email security concerns to: `security@grai.build`

### 3. Include Detailed Information

When reporting, please include:

- **Type of vulnerability** (e.g., SQL injection, command injection, XSS)
- **Full path** to the source file(s) with the vulnerability
- **Location** of affected code (tag/branch/commit or direct URL)
- **Steps to reproduce** the vulnerability
- **Proof-of-concept or exploit code** (if possible)
- **Impact** of the vulnerability
- **Suggested fix** (if you have one)

### 4. What to Expect

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Status Updates:** Every 7 days until resolved
- **Fix Timeline:** Depends on severity
  - **Critical**: Within 7 days
  - **High**: Within 30 days
  - **Medium**: Within 90 days
  - **Low**: Next regular release

### 5. Disclosure Policy

- We will work with you to understand and validate the issue
- We will develop and test a fix
- We will release a security advisory and patched version
- We will credit you for the discovery (unless you prefer anonymity)

## 🛡️ Security Best Practices

When using grai.build in production:

### Neo4j Connections

- **Never commit credentials** to version control
- Use environment variables for passwords:
  ```bash
  export NEO4J_PASSWORD="your-secure-password"
  grai run --password "$NEO4J_PASSWORD"
  ```
- Use TLS/SSL for Neo4j connections in production
- Implement least-privilege access (read-only users when possible)

### YAML Files

- **Validate YAML sources** before building
- Be cautious with YAML from untrusted sources
- Review compiled Cypher before executing in production

### File Permissions

- Restrict access to `.grai/` directory (contains cache)
- Use appropriate file permissions for sensitive configurations
- Don't expose `grai.yml` or entity/relation files publicly if they contain sensitive schema information

### CI/CD Pipelines

- **Protect secrets** in CI/CD workflows
- Use GitHub Secrets or equivalent for credentials
- Implement approval workflows for production deployments
- Scan dependencies regularly (Dependabot is enabled)

### Dependencies

- Keep grai.build and dependencies up to date
- Review `pip` output for security warnings
- Use virtual environments to isolate dependencies

## 🔍 Known Security Considerations

### Cypher Injection (Currently Not Applicable)

grai.build does **not** accept user input for Cypher generation. All Cypher is generated from validated YAML schemas. However:

- Do not programmatically generate YAML from untrusted user input
- Validate entity/relation YAML before using in production

### File Path Traversal

- grai.build reads files relative to project root
- Validate any custom file paths passed to the CLI
- Don't allow untrusted users to specify arbitrary file paths

### Command Injection

- Be cautious when using grai.build in scripts that accept user input
- Sanitize any user input before passing to grai CLI commands

## 📞 Contact

- **Security Issues:** security@grai.build or [GitHub Security Advisories](https://github.com/asantora05/grai.build/security/advisories)
- **General Questions:** [GitHub Discussions](https://github.com/asantora05/grai.build/discussions)
- **Non-Security Bugs:** [GitHub Issues](https://github.com/asantora05/grai.build/issues)

## 🙏 Security Researchers

We appreciate the efforts of security researchers who help keep grai.build and our users safe. Responsible disclosure is highly valued.

Thank you for helping keep grai.build secure! 🔒
