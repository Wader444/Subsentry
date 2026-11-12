# SubSentry setup needs

## What is required for the local demo?

Nothing external is required. The project already supports an offline mock
PayPal client and SQLite:

```env
PAYPAL_MODE=mock
DATABASE_URL=sqlite:///./subsentry.db
LLM_PROVIDER=template
SUBSENTRY_SCHEDULER=0
```

Copy `.env.example` to `.env`, set a long random `SECRET_KEY`, run the seed
script, and start the API and frontend. Do not send credentials in chat or
commit them to source control.

Demo accounts:

- User: `demo@subsentry.local` / `demo1234`
- Admin: `admin@subsentry.local` / `admin1234`

## Credentials needed by integration

### 1. PayPal Sandbox (optional, required only for real PayPal API calls)

Environment variables:

```env
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
```

How to get them:

1. Open the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/).
2. Sign in with a PayPal account or create one.
3. Open **Apps & Credentials**.
4. Select **Sandbox**.
5. Under **My Apps & Credentials**, create an app or open an existing app.
6. Copy its **Client ID** into `PAYPAL_CLIENT_ID`.
7. Click **Show Secret** and copy the secret into `PAYPAL_CLIENT_SECRET`.
8. Keep the app in Sandbox mode. Never use live credentials for local testing.
9. Run `python check_sandbox.py`; a successful check prints `Sandbox check:
   PASS`.

The application uses `https://api-m.sandbox.paypal.com`. PayPal sandbox
accounts and subscription data are separate from live PayPal accounts.

### 2. LLM provider (optional)

The default `LLM_PROVIDER=template` needs no key. To enable AI wording,
provide:

```env
LLM_PROVIDER=openai
LLM_API_KEY=your_provider_api_key
LLM_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
```

How to get an OpenAI key:

1. Open the [OpenAI API platform](https://platform.openai.com/).
2. Sign in or create an account.
3. Open **API keys** in the project settings.
4. Create a secret key and copy it immediately; it may only be shown once.
5. Add billing/usage limits as required by your account.
6. Put the key only in `.env` as `LLM_API_KEY`.

For another OpenAI-compatible provider, use that provider's key, endpoint,
and model in the same three variables. The key is optional because failures
fall back to the template wording.

### 3. SMTP email delivery (optional)

The application currently uses in-app notifications by default. Configure
SMTP only if email notifications are needed:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=notifications@example.com
```

How to get these values:

1. Choose an email provider that supports authenticated SMTP.
2. In that provider's admin/settings area, create a dedicated SMTP user or
   app password. Prefer an app password over your normal mailbox password.
3. Copy the provider's SMTP hostname and port (usually `587` with STARTTLS).
4. Set the SMTP username, app password, and verified sender address.
5. Test with a non-production mailbox before enabling it.

The exact website steps depend on the provider. For Gmail, start at
[Google App Passwords](https://support.google.com/accounts/answer/185833);
an app password requires 2-Step Verification.

### 4. Database (optional)

No database credential is needed for the default SQLite demo. For PostgreSQL,
set a connection URL:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

Create the database and user in your PostgreSQL provider's dashboard or
administration tool, then keep the full URL private.

## Local startup

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In a second terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

For a one-command container deployment, use `docker compose up --build`.
