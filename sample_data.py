"""Sample datasets used by the AgGridJS demos."""

from __future__ import annotations

from random import Random


SALES_ROWS = [
    {"make": "Toyota", "model": "Celica", "price": 35000},
    {"make": "Ford", "model": "Mondeo", "price": 32000},
    {"make": "Porsche", "model": "Boxster", "price": 72000},
    {"make": "BMW", "model": "330e", "price": 45000},
    {"make": "Tesla", "model": "Model 3", "price": 48000},
]


INVENTORY_ROWS = [
    {"category": "Laptops", "product": "Model A", "region": "NA", "units": 42, "revenue": 84000, "stock": 12, "backorder": False},
    {"category": "Laptops", "product": "Model B", "region": "EU", "units": 30, "revenue": 54000, "stock": 6, "backorder": True},
    {"category": "Laptops", "product": "Model C", "region": "APAC", "units": 51, "revenue": 91800, "stock": 15, "backorder": False},
    {"category": "Monitors", "product": "UltraSharp", "region": "NA", "units": 58, "revenue": 31900, "stock": 18, "backorder": False},
    {"category": "Monitors", "product": "VisionPro", "region": "APAC", "units": 22, "revenue": 17600, "stock": 4, "backorder": True},
    {"category": "Accessories", "product": "Dock", "region": "NA", "units": 80, "revenue": 9600, "stock": 35, "backorder": False},
    {"category": "Accessories", "product": "Dock", "region": "EU", "units": 65, "revenue": 7800, "stock": 17, "backorder": False},
    {"category": "Accessories", "product": "Keyboard", "region": "APAC", "units": 44, "revenue": 4400, "stock": 25, "backorder": False},
    {"category": "Accessories", "product": "Mouse", "region": "LATAM", "units": 36, "revenue": 3600, "stock": 15, "backorder": False},
]


ANALYTICS_ROWS = [
    {"month": "Jan", "desktops": 120, "laptops": 95, "tablets": 45},
    {"month": "Feb", "desktops": 98, "laptops": 88, "tablets": 38},
    {"month": "Mar", "desktops": 141, "laptops": 102, "tablets": 52},
    {"month": "Apr", "desktops": 160, "laptops": 119, "tablets": 60},
    {"month": "May", "desktops": 170, "laptops": 123, "tablets": 63},
    {"month": "Jun", "desktops": 180, "laptops": 137, "tablets": 70},
    {"month": "Jul", "desktops": 176, "laptops": 132, "tablets": 66},
    {"month": "Aug", "desktops": 182, "laptops": 141, "tablets": 72},
    {"month": "Sep", "desktops": 165, "laptops": 128, "tablets": 58},
    {"month": "Oct", "desktops": 158, "laptops": 120, "tablets": 54},
    {"month": "Nov", "desktops": 149, "laptops": 114, "tablets": 49},
    {"month": "Dec", "desktops": 172, "laptops": 135, "tablets": 67},
]


_REGIONS = ["NA", "EU", "APAC", "LATAM"]
_PRODUCTS = [
    {"product": "Notebook Air", "category": "Laptops", "price": 980},
    {"product": "Notebook Pro", "category": "Laptops", "price": 1450},
    {"product": "4K Display", "category": "Monitors", "price": 650},
    {"product": "Ergo Keyboard", "category": "Accessories", "price": 189},
    {"product": "Precision Mouse", "category": "Accessories", "price": 129},
]

_rng = Random(42)
SSRM_ROWS = []
order_counter = 1
for year in range(2020, 2024):
    for quarter in ("Q1", "Q2", "Q3", "Q4"):
        for region in _REGIONS:
            for product in _PRODUCTS:
                units = _rng.randint(20, 120)
                revenue = units * product["price"]
                SSRM_ROWS.append(
                    {
                        "order_id": f"{year}-{order_counter:05d}",
                        "region": region,
                        "product": product["product"],
                        "category": product["category"],
                        "quarter": f"{year} {quarter}",
                        "units": units,
                        "revenue": revenue,
                    }
                )
                order_counter += 1


__all__ = [
    "SALES_ROWS",
    "INVENTORY_ROWS",
    "ANALYTICS_ROWS",
    "SSRM_ROWS",
]

