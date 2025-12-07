# 📚 Quick Guide: CSV, Excel, SQL & Your EDA

## FILE FORMATS (Simple Explanation)

### CSV (.csv) - Comma Separated Values
- **What:** Plain text, data separated by commas
- **Example:** `name,age,city` → `John,25,Mumbai`
- **Use:** Store simple tabular data
- **Your project:** `enhanced_iphone_pricing_analysis_deduplicated.csv`

### Excel (.xlsx)
- **What:** Spreadsheet with formulas, formatting, charts
- **Use:** Complex analysis with formulas
- **Your project:** Can export CSVs to Excel for mentor

### SQL (.db, .sqlite)
- **What:** Database with tables and relationships
- **Use:** Store large structured data with links between tables
- **Your project:** `ecommerce.db` (products, reviews, sentiment tables)

### Word (.docx)
- **What:** Text documents
- **Use:** Reports, documentation (NOT for data!)

### Jupyter (.ipynb)
- **What:** Interactive notebook (code + output + text)
- **Use:** EDA, analysis, visualization
- **Your project:** EDA notebooks

---

## YOUR 2 DATASETS & THEIR EDAs

### Dataset 1: Time Series Price Data
- **File:** `enhanced_iphone_pricing_analysis_deduplicated.csv`
- **Used for:** Chronos & Prophet forecasting
- **EDA:** `EDA_TimeSeries_PriceData.ipynb` ✅
- **What we found:** Clear time patterns → justified time series models

### Dataset 2: Review Sentiment Data
- **File:** Database (reviews table) - 60 Flipkart reviews
- **Used for:** Llama 3.3 sentiment analysis
- **EDA:** Need to create this!
- **What to analyze:** Review text, ratings, sentiment distribution

---

## RELATIONSHIP (How they connect)

```
Web Scraping → CSV files → SQLite Database → Python pandas → EDA → Models → Dashboard
```

**Why CSV?** Easy to create, universal, simple

**Why SQL?** Fast queries, relationships (products ← reviews ← sentiment)

**Why Jupyter?** See code + charts together

---

## ANSWER FOR MENTOR

**Q: What file formats did you use?**
> "CSV for data collection, SQLite for storage, Jupyter for EDA. CSV is simple and works with pandas, SQL provides fast queries and relationships between tables."

---

**Simple, right?** Now let me create the second EDA notebook!
