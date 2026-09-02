# Production Checklist

- [ ] HTTPS/TLS
- [ ] Random JWT secret in secret manager
- [ ] Production MySQL credentials in secret manager
- [ ] Database backups + restore testing
- [ ] SMTP email verification/password reset
- [ ] Object storage for medical reports
- [ ] Antivirus/malware scan for uploaded files
- [ ] Rate limiting on auth and upload APIs
- [ ] Security headers / reverse proxy
- [ ] Access-control review and patient-consent workflow
- [ ] Audit-log retention policy
- [ ] Data retention/deletion policy
- [ ] Encryption at rest and key management
- [ ] Legal/privacy review for health data
- [ ] Clinical validation of any ML model before real clinical use
