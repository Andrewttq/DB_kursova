"""Статистика набору RAW_recipes.csv для розділу 2 звіту.

Запуск з кореня репозиторію:
    uv run --with pandas python scripts/dataset_stats.py data/RAW_recipes.csv
"""

import ast
import sys
from collections import Counter

import pandas as pd

CUISINES = [
    "american",
    "italian",
    "mexican",
    "asian",
    "european",
    "french",
    "greek",
    "indian",
    "chinese",
    "thai",
    "japanese",
    "spanish",
    "german",
    "middle-eastern",
    "african",
    "caribbean",
    "korean",
    "vietnamese",
    "british",
    "irish",
    "canadian",
    "australian",
    "russian",
    "polish",
    "scandinavian",
    "turkish",
    "moroccan",
    "brazilian",
    "cajun",
    "southwestern-united-states",
]

path = sys.argv[1] if len(sys.argv) > 1 else "data/RAW_recipes.csv"
df = pd.read_csv(path)


def parse(col):
    return df[col].dropna().map(ast.literal_eval)


print("=== Загальне")
print("рядків:", len(df))
print("стовпці:", ", ".join(df.columns))
print("унікальних id:", df["id"].nunique(), "| дублікатів id:", df["id"].duplicated().sum())
print("унікальних авторів (contributor_id):", df["contributor_id"].nunique())
dates = pd.to_datetime(df["submitted"], errors="coerce")
print(
    "дати submitted:",
    dates.min().date(),
    "..",
    dates.max().date(),
    "| некоректних:",
    dates.isna().sum(),
)

print("\n=== Пропуски по стовпцях")
for col, n in df.isna().sum().items():
    if n:
        print(f"{col}: {n}")
print(
    "порожніх description (NaN або пусто):", (df["description"].fillna("").str.strip() == "").sum()
)
print("порожніх name:", (df["name"].fillna("").str.strip() == "").sum())

print("\n=== Час приготування (minutes)")
m = df["minutes"]
print("медіана:", m.median(), "| середнє:", round(m.mean(), 1), "| макс:", m.max())
print("дорівнює 0:", (m == 0).sum(), "| більше доби (>1440):", (m > 1440).sum())

print("\n=== Інгредієнти та кроки")
for col in ["n_ingredients", "n_steps"]:
    s = df[col]
    print(
        f"{col}: мін {s.min()} | медіана {s.median()} | "
        f"середнє {round(s.mean(), 1)} | макс {s.max()}"
    )
print("n_steps = 0:", (df["n_steps"] == 0).sum())
ingr = Counter(i for lst in parse("ingredients") for i in lst)
print("унікальних назв інгредієнтів:", len(ingr))
print("топ-10 інгредієнтів:", ", ".join(f"{k} ({v})" for k, v in ingr.most_common(10)))

print("\n=== Калорійність (nutrition[0])")
cal = parse("nutrition").map(lambda x: x[0])
print("медіана:", cal.median(), "| макс:", cal.max(), "| дорівнює 0:", (cal == 0).sum())

print("\n=== Кухні з тегів")
tags = parse("tags")
has_cuisine = tags.map(lambda t: any(c in t for c in CUISINES))
print("рецептів з тегом кухні:", has_cuisine.sum(), "| без тегу кухні:", (~has_cuisine).sum())
cnt = Counter(c for t in tags for c in CUISINES if c in t)
print("топ-10 кухонь:", ", ".join(f"{k} ({v})" for k, v in cnt.most_common(10)))
print("унікальних тегів усього:", len(Counter(x for t in tags for x in t)))

print("\n=== Рецептів на автора")
per = df["contributor_id"].value_counts()
print("медіана:", per.median(), "| макс:", per.max(), "| авторів з 1 рецептом:", (per == 1).sum())
