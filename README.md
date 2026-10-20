# Zoho Desk Auto-Confirmation Bot 🤖

An automation script built with **Python** that monitors **Zoho Desk** tickets, extracts booking codes from ticket subjects, validates each booking through the **Juniper SOAP API**, and automatically replies to customers with their hotel confirmation number (HCN) — then updates the ticket's custom fields and closes it.

---

## 🚀 Features

- 🔍 **Keyword-based detection** — Scans incoming ticket subjects for HCN-related keywords (e.g., "HCN Request", "Need Hotel Confirmation", "Reconfirm Booking").
- 🎫 **Booking code extraction** — Uses regex to pull 6-character alphanumeric booking codes from subjects.
- 🌐 **Juniper SOAP integration** — Queries the Juniper `wsBookings` SOAP endpoint to fetch booking status, product group, travel date, customer name, and confirmation reference.
- ✉️ **Smart auto-reply** — Sends one of two HTML email templates:
  - **With HCN** → if the booking already has a hotel confirmation number.
  - **Without HCN** → if the booking is confirmed under allotment but the hotel's direct number is not yet available.
- 📝 **Ticket field updates** — Populates custom fields (booking reference, confirmation number, check-in date, product group, customer name, closed-by, action).
- 🔒 **Blueprint-aware closure** — Fetches the ticket's current blueprint state and performs the correct transition to `Closed`.
- 🔁 **Continuous loop** — Runs every 5 minutes, refreshing the OAuth access token each cycle.
- ⚠️ **Filters & safeguards** — Ignores cancelled/amended/refunded tickets, only processes inbound threads, and skips tickets that already contain a confirmation number.

---

## 🧰 Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3 |
| HTTP | `requests`, `aiohttp` |
| Data | `pandas`, `numpy` |
| Parsing | `xmltodict`, `re`, `json` |
| Utilities | `tqdm`, `retrying`, `datetime` |
| APIs | Zoho Desk REST API · Juniper SOAP API |

---

## ⚙️ How It Works

```
┌─────────────────────┐
│  Fetch tickets from │
│   Zoho Desk API     │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Filter inbound +    │
│ detect HCN keywords │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Extract booking code│
│      (regex)        │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Query Juniper SOAP │
│   for booking data  │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Validate status,   │
│  date & subject     │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Send auto-reply +  │
│  update ticket +    │
│   close ticket      │
└─────────────────────┘
```

---

## 📂 Project Structure

```
chatbotsystem.py   # Main automation script
```

---

## 🔐 Configuration

Before running, replace the placeholder credentials at the top of the script:

```python
juniper_user     = 'YOUR_JUNIPER_USER'
juniper_password = 'YOUR_JUNIPER_PASSWORD'
orgId            = 'YOUR_ZOHO_ORG_ID'
```

And inside `renewAccessToken2()`:

```python
client_id     = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
refresh_token = "YOUR_REFRESH_TOKEN"
```

> ⚠️ **Security note:** Never commit real credentials. Use environment variables or a `.env` file, and add it to `.gitignore`.

---

## ▶️ Usage

```bash
pip install requests pandas xmltodict tqdm aiohttp retrying numpy
python chatbotsystem.py
```

The script will start an infinite loop, polling Zoho Desk every **5 minutes**.

---

## 🛡️ Safety Filters

The script **automatically skips** tickets whose subject contains:

`cancel · amend · waive · modify · modification · refund`

And only processes bookings that are:
- Inbound (`direction == 'in'`)
- With a **future** check-in date
- With status containing `ok` or `con`

---

## 📬 Email Templates

Two branded HTML templates are included:
1. **Confirmed with HCN** — final response with the confirmation number.
2. **Confirmed without HCN** — informs the partner that the direct hotel confirmation is pending.

Both are sent from `customer.care@eetglobal.net` with CC to the same address.

---

## 📝 License

Internal use — EET Global.