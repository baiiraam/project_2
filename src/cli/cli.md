# CLI Commands for Your Food Analyzer

Your CLI supports **three commands**:

---

## 1. Analyze a Meal Photo

```bash
python -m src.cli.main analyze <image_path>
```

**Example:**
```bash
python -m src.cli.main analyze data/rice_chicken_broccoli.png
```

**Output:**
```
ingredient                g   kcal protein  carbs    fat
-------------------------------------------------------
white rice              150    195    4.1   42.0    0.4
broccoli florets         80     27    2.2    5.6    0.3
grilled steak           200    500   52.0    0.0   34.0
-------------------------------------------------------
TOTAL                   430    722   58.3   47.6   34.8
```

---

## 2. List Recent Analyses

```bash
python -m src.cli.main list
```

**Output:**
```
Last 3 analyses:
#1: data/rice_chicken_broccoli.png - 722 kcal (2025-05-18 03:21:14.758000+00:00)
#2: data/bread_cheese.png - 160 kcal (2025-05-18 03:28:09.123000+00:00)
#3: data/rice_chicken_broccoli.png - 679 kcal (2025-05-18 03:16:19.649000+00:00)
```

---

## 3. Get Analysis by ID

```bash
python -m src.cli.main get <analysis_id>
```

**Example:**
```bash
python -m src.cli.main get 1
```

**Output:**
```
Analysis #1
Image: data/rice_chicken_broccoli.png
Date: 2025-05-18 03:21:14.758000+00:00
Totals: 722 kcal, 58.3g protein, 47.6g carbs, 34.8g fat
```

---

## Help Command

```bash
python -m src.cli.main --help
```

**Output:**
```
usage: main.py [-h] {analyze,get,list} ...

AI Food Analyzer - Analyze meal photos for nutrition information

positional arguments:
  {analyze,get,list}
    analyze           Analyze a meal photo
    get               Get analysis by ID
    list              List last 10 analyses

options:
  -h, --help          show this help message and exit
```

---

## Question 470

Run these commands and verify they work:

```bash
python -m src.cli.main list
python -m src.cli.main get 1
```

Tell me if they return data from your database.
