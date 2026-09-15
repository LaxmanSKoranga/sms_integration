### SMS Integration

Two-way Twilio SMS integration for Frappe CRM.

### Install

```bash
bench get-app <copy this repo's URL here> --branch main
bench install-app sms_integration
bench migrate
```

### Add the SMS tab to CRM

```bash
bash apps/sms_integration/sms_integration/crm_frontend/apply_sms_tab.sh
bench restart
```

Requires Node.js + Yarn on the server.

### Configure

1. Set `Account SID` and `Auth Token` on **CRM Twilio Settings**.
2. Set `Sender Phone Number` and enable **SMS Integration Settings**.
3. In Twilio Console, set the number's webhooks:
   - Incoming message: `https://<site>/api/method/sms_integration.sms.webhook.inbound`
   - Status callback: `https://<site>/api/method/sms_integration.sms.webhook.status_callback`

### License

mit
