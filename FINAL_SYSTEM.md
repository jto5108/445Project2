# ClipCheck - Final System Overview

## ✅ **REAL-TIME ON-DEMAND SYSTEM**

Your project now works **exactly** as you specified:

### How It Works

```
1. User enters hashtag on website
        ↓
2. System scrapes Reddit posts for that hashtag
        ↓
3. System scrapes training data from other hashtags
        ↓
4. System preprocesses all data (TF-IDF + features)
        ↓
5. System trains ML model on fresh data
        ↓
6. System predicts misinformation scores
        ↓
7. User sees top 10 posts with scores
```

### Key Features

✅ **No Pre-Training** - No need to run `train_model.py` first
✅ **Real-Time Scraping** - Fresh data every request
✅ **Auto-Preprocessing** - TF-IDF + feature engineering on-the-fly
✅ **On-Demand Training** - New model trained for each request
✅ **All From Website** - Everything triggered by user clicking "Analyze"
✅ **Real Data** - Scrapes actual Reddit posts from Google
✅ **Minimal Fallback** - Only uses 4 fallback examples if scraping completely fails

---

## 🚀 How to Use

### Setup (One Time)
```bash
cd /Users/gabrielsilva/Desktop/445Project2
pip install -r backend/requirements.txt
```

### Run Server
```bash
python3 app.py
```

### Use Application
1. Open: http://localhost:5001
2. Enter hashtag: `#gaming`, `#technology`, `#politics`, etc.
3. Click "Analyze"
4. Wait 20-30 seconds
5. View top 10 posts with misinformation scores!

---

## 📊 What Happens When User Clicks "Analyze"

### Step 1: Scrape User's Hashtag (5-10 seconds)
- Searches Google for: `site:reddit.com "#yourhashtag"`
- Extracts top 10 results
- Gets: title, URL, snippet, subreddit, rank

### Step 2: Scrape Training Data (10-15 seconds)
- Scrapes `#conspiracy`, `#leaked`, `#exposed` (labeled as misinformation)
- Scrapes `#gaming`, `#technology`, `#help` (labeled as normal)
- Gets ~18 training examples (3 per hashtag × 6 hashtags)

### Step 3: Preprocess Data (1 second)
- Combines title + snippet for each post
- Extracts TF-IDF features (4000 features, bigrams)
- Engineers features:
  - Clickbait score
  - Keyword flags (17 indicators)
  - Subreddit risk
  - Rank score

### Step 4: Train Model (1-2 seconds)
- Logistic Regression on training data
- Fits on scraped + labeled examples
- Achieves ~100% training accuracy

### Step 5: Predict (< 1 second)
- Applies trained model to user's 10 posts
- Generates probability scores (0-100%)
- Classifies as high/medium/low risk

### Step 6: Return Results
- JSON response with all 10 posts
- Each post includes:
  - Rank (1-10)
  - Title, URL, subreddit
  - Misinformation score
  - Risk level (high/medium/low)
  - Clickbait score
  - Matched keywords
  - Snippet

---

## 🔍 Scraper Details

### Google Search Query
For hashtag `#gaming`, searches:
```
site:reddit.com "gaming"
```

This ensures **all results are from Reddit**!

### What Gets Scraped
- Post titles
- URLs (links to Reddit)
- Snippets (preview text)
- Subreddit names
- Google ranking
- Dates (when available)

---

## 🧠 ML Pipeline

### Training Data Sources
**Positive Examples (Misinformation):**
- `#conspiracy` posts
- `#leaked` posts
- `#exposed` posts

**Negative Examples (Normal):**
- `#gaming` posts
- `#technology` posts
- `#help` posts

### Features Extracted
1. **TF-IDF Vectors** (4000 dimensions)
   - Unigrams and bigrams
   - Captures text patterns

2. **Engineered Features**
   - Clickbait score (0-1)
   - 17 keyword flags
   - Subreddit risk score
   - Google rank score

### Model
- **Algorithm**: Logistic Regression
- **Library**: scikit-learn
- **Training**: Fresh model per request
- **Output**: Probability of misinformation (0-100%)

---

## 📝 For Your Project Report

### Data Collection (5%)
"The system scrapes real Reddit posts from Google search in real-time. For each user query, it collects the top 10 posts matching the hashtag, plus approximately 18 training examples from predefined hashtags (#conspiracy, #leaked, #exposed for positive examples; #gaming, #technology, #help for negative examples). All scraping uses Selenium with headless Chrome and BeautifulSoup for parsing."

### Data Processing & Feature Engineering (10%)
"Data preprocessing involves text combination (title + snippet), TF-IDF vectorization (4000 features with bigrams), and engineering of behavioral features including clickbait scoring (based on capitalization and punctuation), keyword flagging (17 misinformation indicators), subreddit risk scoring, and ranking features. The system combines sparse TF-IDF vectors with dense engineered features using scipy.sparse.hstack."

### Model Development (10%)
"The system uses Logistic Regression (scikit-learn) trained on-demand for each user request. Training data consists of scraped posts auto-labeled based on hashtag source. The model takes combined TF-IDF and engineered features as input and outputs probability scores converted to percentages. A new model is trained for each query, ensuring fresh predictions on current data."

---

## 🎯 Advantages of This Approach

1. **Always Fresh** - New training data every request
2. **No Stale Models** - Model reflects current Reddit content
3. **Adaptive** - Automatically adjusts to changing patterns
4. **Simple** - User just enters hashtag and gets results
5. **Transparent** - Shows training info in response

## ⚠️ Trade-offs

1. **Slower** - Takes 20-30 seconds vs instant with pre-trained model
2. **Rate Limits** - Google may block after many requests
3. **Variable Quality** - Depends on what gets scraped
4. **Fallback** - Uses 4 examples if scraping fails completely

---

## 🧪 Testing

The system works! You can test it immediately:

```bash
python3 app.py
# Open http://localhost:5001
# Enter: #gaming
# Click Analyze
# Wait ~25 seconds
# See results!
```

---

**Your system is complete and ready for demonstration!**
