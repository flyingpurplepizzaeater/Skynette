# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. Email security concerns to: security@skynette.io
3. Or use GitHub's private vulnerability reporting feature

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Target**: Within 30 days for critical issues

### What to Expect

1. Acknowledgment of your report
2. Assessment of the vulnerability
3. Regular updates on our progress
4. Credit in the security advisory (if desired)

## Security Best Practices

### For Users

1. **API Keys**: Store API keys securely using the built-in keyring integration
2. **Credentials**: Never commit credentials to workflows
3. **Updates**: Keep Skynette updated to the latest version
4. **Permissions**: Run with minimum required permissions

### For Developers

1. **Input Validation**: All user inputs are validated
2. **SQL Injection**: Using parameterized queries via SQLAlchemy
3. **XSS Prevention**: UI properly escapes user content
4. **Dependency Scanning**: Regular dependency audits
5. **Code Review**: All changes require review

## Security Features

- **Keyring Integration**: System keyring for API key storage
- **Encrypted Storage**: Sensitive data encrypted at rest
- **Sandboxed Execution**: Plugin code runs in sandbox
- **Rate Limiting**: Built-in rate limiting for API calls
- **Audit Logging**: Workflow execution audit trails

## Known Limitations

- Local AI models run with full system access
- Custom Python nodes can execute arbitrary code
- Workflow exports may contain sensitive data

## Acknowledgments

We thank the security researchers who have helped improve Skynette's security.
