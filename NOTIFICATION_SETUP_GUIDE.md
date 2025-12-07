# 🔔 Email Notification System - Setup Guide

## Module 4: Real-Time Alerts for Price Drops & Sentiment Changes

---

## ✨ Features

### 1. **Price Drop Alerts**
- Automatic email when price drops >= 5%
- Shows old price, new price, savings
- Includes deal score and buy recommendation
- Beautiful HTML email template

### 2. **Sentiment Change Alerts**
- Email when sentiment changes >= 10%
- Tracks positive/negative review trends
- Warns about product quality issues
- Celebrates improvements

---

## 🚀 Quick Setup (5 Minutes)

### **Step 1: Gmail App Password**

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** (left sidebar)
3. Enable **2-Step Verification** if not already enabled
4. Click **App Passwords** (under "How you sign in to Google")
5. Select app: **Mail**
6. Select device: **Windows Computer**
7. Click **Generate**
8. **Copy the 16-character password** (looks like: `xxxx xxxx xxxx xxxx`)

### **Step 2: Run Setup Script**

```bash
python setup_notifications.py
```

**You'll be asked:**
1. Gmail address: `your-email@gmail.com`
2. App Password: `xxxx xxxx xxxx xxxx` (the one you just generated)
3. Recipient emails: Who should receive alerts (can add multiple)
4. Enable now? `y` or `n`
5. Send test email? `y` (recommended)

### **Step 3: Verify Test Email**

Check your inbox for:
```
Subject: Test: E-Commerce Sentiment Tracker Notifications
```

If received: ✅ Setup complete!
If not: ❌ Check spam folder or verify credentials

---

## 📧 How It Works

### **Price Drop Alert Example:**

**Trigger:** iPhone 14 price drops from Rs.56,000 to Rs.52,000 (7% drop)

**Email Sent:**
```
Subject: Price Drop Alert: Apple iPhone 14 - Save Rs.4,000!

---------------------------------------------------
GREAT NEWS!

Apple iPhone 14 (128GB) - Flipkart

Rs.56,000 → Rs.52,000

YOU SAVE: Rs.4,000 (7.1% off!)

Deal Score: 92/100
Recommendation: BUY NOW

[View in Dashboard]
---------------------------------------------------
```

### **Sentiment Change Alert Example:**

**Trigger:** Positive sentiment drops from 78% to 65% (13% decrease)

**Email Sent:**
```
Subject: Warning: Apple iPhone 14 Sentiment Declining

---------------------------------------------------
CUSTOMER SENTIMENT WARNING

Apple iPhone 14 (128GB) - Amazon

Positive Sentiment:
78.0% → 65.0%
Change: -13.0%

⚠️ More negative reviews detected
⚠️ Consider waiting for product improvements

[View Details]
---------------------------------------------------
```

---

## 🔧 Configuration

### **Email Config File:** `notifications/email_config.json`

```json
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "recipient_emails": [
        "recipient1@example.com",
        "recipient2@example.com"
    ],
    "enabled": true
}
```

### **Alert Thresholds:**

Can be customized in `check_alerts.py`:

```python
results = alert_manager.check_all_alerts(
    price_threshold=5.0,      # Alert if price drops >= 5%
    sentiment_threshold=10.0  # Alert if sentiment changes >= 10%
)
```

**Recommended Settings:**
- **Price threshold**: 3-7% (too low = spam, too high = miss deals)
- **Sentiment threshold**: 8-15% (significant enough to matter)

---

## 📊 Checking for Alerts

### **Manual Check:**

```bash
python check_alerts.py
```

This will:
1. Check current prices vs. last known prices
2. Check current sentiment vs. last known sentiment
3. Send emails if thresholds are met
4. Save state for next comparison

### **Automated Checking:**

**Option A: Windows Task Scheduler (Recommended)**

1. Open **Task Scheduler**
2. Create Basic Task
3. Name: "E-Commerce Alert Checker"
4. Trigger: Daily at 9:00 AM (or your preference)
5. Action: Start a program
   - Program: `python`
   - Arguments: `check_alerts.py`
   - Start in: `path\to\infosys-competitor-tracker`
6. Finish

**Option B: Python Script Loop (Simple)**

Create `run_alerts_daemon.py`:
```python
import time
from notifications.alert_manager import AlertManager

alert_manager = AlertManager()

while True:
    print("Checking alerts...")
    alert_manager.check_all_alerts()
    print("Sleeping for 1 hour...")
    time.sleep(3600)  # Check every hour
```

Run: `python run_alerts_daemon.py`

---

## 🎯 Integration with Dashboard

The notification system works independently but can be integrated into your Streamlit dashboard:

**Add to `dashboard/app.py` sidebar:**

```python
with st.sidebar:
    st.header("🔔 Notifications")

    if st.button("Check Alerts Now"):
        from notifications.alert_manager import AlertManager
        alert_manager = AlertManager()
        results = alert_manager.check_all_alerts()
        st.success(f"Sent {results['total']} alerts!")

    # Show alert history
    with st.expander("Recent Alerts"):
        alerts = alert_manager.get_alert_history(limit=5)
        for alert in alerts:
            st.text(f"{alert['type']}: {alert['timestamp']}")
```

---

## 🧪 Testing

### **Test Price Alert:**

```python
from notifications.email_notifier import EmailNotifier

notifier = EmailNotifier()
notifier.send_price_drop_alert(
    product_name="Apple iPhone 14 (128GB)",
    platform="Flipkart",
    old_price=56000,
    new_price=52000,
    drop_percentage=7.14,
    deal_score=92,
    recommendation="BUY_NOW"
)
```

### **Test Sentiment Alert:**

```python
from notifications.email_notifier import EmailNotifier

notifier = EmailNotifier()
notifier.send_sentiment_change_alert(
    product_name="Apple iPhone 14 (128GB)",
    platform="Amazon",
    old_sentiment_pct=78.0,
    new_sentiment_pct=65.0,
    sentiment_change=-13.0,
    trend="declining"
)
```

---

## 🔐 Security Best Practices

1. **Never commit `email_config.json` to Git**
   - Add to `.gitignore`
   - Keep credentials private

2. **Use App Passwords, not Gmail password**
   - More secure
   - Can revoke without changing main password

3. **Limit recipients**
   - Only send to trusted emails
   - Avoid public mailing lists

4. **Monitor usage**
   - Gmail free tier: 500 emails/day
   - More than enough for alerts

---

## 🐛 Troubleshooting

### **Error: "Authentication failed"**
- ✅ Verify Gmail address is correct
- ✅ Check App Password (16 characters, no spaces)
- ✅ Ensure 2-Step Verification is enabled
- ✅ Generate new App Password if needed

### **Error: "Connection timeout"**
- ✅ Check internet connection
- ✅ Verify SMTP port: 587 (not 465 or 25)
- ✅ Check firewall settings

### **Emails not arriving**
- ✅ Check spam/junk folder
- ✅ Verify recipient email is correct
- ✅ Look for Gmail security alerts

### **Too many/few alerts**
- ✅ Adjust price_threshold (default: 5%)
- ✅ Adjust sentiment_threshold (default: 10%)
- ✅ Check alert_state.json for last values

---

## 📈 Email Templates

### **Customizing HTML Templates:**

Edit `notifications/email_notifier.py`:

**Change colors:**
```python
# Line ~80 (price drop header)
.header { background-color: #28a745; }  # Green
# Change to your color, e.g., #007bff for blue
```

**Add logo:**
```python
# Add after <div class="header">
<img src="https://your-logo-url.com/logo.png" width="100">
```

**Change button link:**
```python
# Line ~140 (dashboard link)
<a href="http://localhost:8501">
# Change to deployed URL if you have one
```

---

## 📚 Module 4 Deliverables Checklist

- [x] Email notification system implemented
- [x] Price drop alerts working
- [x] Sentiment change alerts working
- [x] Configuration setup script
- [x] Test email functionality
- [x] Alert history tracking
- [x] Threshold customization
- [x] Beautiful HTML email templates
- [x] Security (App Password)
- [x] Documentation

---

## 🎓 For Your Presentation

**Demo Flow:**

1. **Show Configuration:**
   - Open `notifications/email_config.json`
   - Explain SMTP, credentials, recipients

2. **Run Manual Check:**
   - `python check_alerts.py`
   - Show console output

3. **Show Email:**
   - Open inbox
   - Display price drop email
   - Display sentiment alert email

4. **Explain Thresholds:**
   - Price: 5% drop triggers
   - Sentiment: 10% change triggers

5. **Show Integration Potential:**
   - Mention Task Scheduler for automation
   - Dashboard sidebar integration

**Key Points:**
- Real-time monitoring without constant checking
- Intelligent threshold-based alerts
- Professional email templates
- Scalable (can add more products, platforms)
- Secure (App Passwords, not main password)

---

## 🚀 Next Steps

1. **Run Setup:** `python setup_notifications.py`
2. **Test Alerts:** `python check_alerts.py`
3. **Customize Thresholds** (if needed)
4. **Set up Automation** (Task Scheduler)
5. **Take Screenshots** for presentation

---

**Need help? Check the error messages or review this guide!** 📖
