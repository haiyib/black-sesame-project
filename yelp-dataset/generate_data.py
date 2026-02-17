#!/usr/bin/env python3
"""Generate data.js from all flavor CSV datasets."""

import csv
import json
from collections import Counter, defaultdict

OUTPUT = "../black-sesame-trends/data.js"

def read_csv(filename):
    with open(filename, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def process_flavor(filename, flavor_name):
    rows = read_csv(filename)

    # Yearly trends
    year_counts = Counter(r["year"] for r in rows if r["year"])
    years = sorted(year_counts.keys())
    year_trends = [{"year": y, "reviews": year_counts[y]} for y in years]

    # Top cities
    city_counts = Counter(f"{r['city']}, {r['state']}" for r in rows if r["city"] and r["state"])
    top_cities = [{"city": c, "reviews": n} for c, n in city_counts.most_common(10)]

    # Top states
    state_counts = Counter(r["state"] for r in rows if r["state"])
    top_states = [{"state": s, "reviews": n} for s, n in state_counts.most_common(10)]

    # Star distribution
    star_counts = Counter()
    for r in rows:
        try:
            star = int(float(r["stars_x"]))
            star_counts[star] += 1
        except (ValueError, KeyError):
            pass
    star_dist = [{"stars": s, "count": star_counts.get(s, 0)} for s in range(1, 6)]

    # Top categories
    cat_counts = Counter()
    for r in rows:
        if r.get("categories"):
            for cat in r["categories"].split(","):
                cat = cat.strip()
                if cat:
                    cat_counts[cat] += 1
    top_cats = [{"category": c, "count": n} for c, n in cat_counts.most_common(10)]

    # Top businesses by review count
    biz_reviews = defaultdict(lambda: {"reviews": 0, "total_stars": 0, "location": ""})
    for r in rows:
        name = r.get("name", "").strip()
        if not name:
            continue
        biz = biz_reviews[name]
        biz["reviews"] += 1
        try:
            biz["total_stars"] += float(r["stars_x"])
        except (ValueError, KeyError):
            pass
        biz["location"] = f"{r['city']}, {r['state']}"

    top_biz = sorted(biz_reviews.items(), key=lambda x: x[1]["reviews"], reverse=True)[:10]
    top_businesses = [{
        "name": name,
        "location": d["location"],
        "reviews": d["reviews"],
        "rating": round(d["total_stars"] / d["reviews"], 2) if d["reviews"] else 0
    } for name, d in top_biz]

    return {
        "totalReviews": len(rows),
        "yearTrends": year_trends,
        "topCities": top_cities,
        "topStates": top_states,
        "starDistribution": star_dist,
        "topCategories": top_cats,
        "topBusinesses": top_businesses,
    }

def process_comparison_summary():
    rows = read_csv("flavor_comparison_summary.csv")
    result = []
    for r in rows:
        result.append({
            "flavor": r["Flavor"],
            "totalMentions": int(r["Total Mentions"]),
            "uniqueBusinesses": int(r["Unique Businesses"]),
            "cities": int(r["Cities"]),
            "avgRating": float(r["Avg Review Rating"]),
        })
    return result

def process_2025_comparison():
    rows = read_csv("asian_flavors_comparison_2025.csv")
    result = []
    for r in rows:
        result.append({
            "flavor": r["flavor"],
            "city": r["city"],
            "businessCount": int(r["business_count"]),
        })
    return result

def process_2025_businesses():
    rows = read_csv("black_sesame_businesses_2025.csv")

    # By city
    city_counts = Counter(f"{r['city']}, {r['state']}" for r in rows if r["city"])
    top_cities = [{"city": c, "count": n} for c, n in city_counts.most_common(10)]

    # By state
    state_counts = Counter(r["state"] for r in rows if r["state"])
    top_states = [{"state": s, "count": n} for s, n in state_counts.most_common(10)]

    # Top rated (min 10 reviews)
    top_rated = []
    for r in rows:
        try:
            rating = float(r["rating"])
            review_count = int(r["review_count"])
        except (ValueError, KeyError):
            continue
        if review_count >= 10:
            top_rated.append({
                "name": r["name"],
                "city": f"{r['city']}, {r['state']}",
                "rating": rating,
                "reviewCount": review_count,
                "categories": r.get("categories", ""),
            })
    top_rated.sort(key=lambda x: (-x["rating"], -x["reviewCount"]))
    top_rated = top_rated[:10]

    return {
        "total": len(rows),
        "topCities": top_cities,
        "topStates": top_states,
        "topRated": top_rated,
    }

def main():
    print("Processing black sesame...")
    black_sesame = process_flavor("black_sesame_analysis.csv", "black_sesame")

    print("Processing matcha...")
    matcha = process_flavor("matcha_analysis.csv", "matcha")

    print("Processing ube...")
    ube = process_flavor("ube_analysis.csv", "ube")

    print("Processing comparison summary...")
    comparison = process_comparison_summary()

    print("Processing 2025 city comparison...")
    city_comparison_2025 = process_2025_comparison()

    print("Processing 2025 businesses...")
    businesses_2025 = process_2025_businesses()

    data = {
        "blackSesame": black_sesame,
        "matcha": matcha,
        "ube": ube,
        "flavorComparison": comparison,
        "cityComparison2025": city_comparison_2025,
        "blackSesame2025": businesses_2025,
    }

    js = "// Asian Flavors Data - Generated from Yelp Academic Dataset\n"
    js += f"const flavorData = {json.dumps(data, indent=2)};\n"

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"Written to {OUTPUT}")
    print(f"  Black Sesame: {black_sesame['totalReviews']} reviews")
    print(f"  Matcha: {matcha['totalReviews']} reviews")
    print(f"  Ube: {ube['totalReviews']} reviews")
    print(f"  2025 Businesses: {businesses_2025['total']}")

if __name__ == "__main__":
    main()
