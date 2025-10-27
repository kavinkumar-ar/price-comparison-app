# scraper.py
"""
Mock product data provider and price comparison.
Replace or extend functions here to call real APIs later.
"""
import random

def get_mock_product_data(product_name):
    descriptions = {
        "Phone": "A high-performance smartphone with advanced camera capabilities and long battery life.",
        "Laptop": "Lightweight laptop ideal for work and study with a powerful processor.",
        "Tablet": "Portable tablet with vivid display and long battery life.",
        "Camera": "Versatile digital camera capable of high-resolution photos and 4K video.",
        "Headphones": "Wireless noise-cancelling headphones for immersive audio.",
        "Watch": "Smartwatch with fitness tracking and notifications.",
        "Shoe": "Comfortable athletic shoes for daily wear and running.",
        "Bag": "Durable backpack with multiple compartments for travel and work.",
        "Television": "4K Smart TV with HDR and streaming support.",
        "Speaker": "Portable Bluetooth speaker with strong bass and long battery."
    }

    # Mock stores with shipping, rating, reviews
    def mk_store(name):
        price = random.randint(2000, 80000)
        return {
            "name": name,
            "price": f"₹{price:,}",
            "price_raw": price,
            "shipping": "Free Delivery" if random.random() > 0.3 else f"₹{random.randint(30,200)} delivery",
            "rating": f"{random.uniform(3.5, 5):.1f}★",
            "reviews": f"{random.randint(10, 15000)} reviews",
            "link": "#"  # later point to real product URL
        }

    stores = [mk_store("Amazon"), mk_store("Flipkart"), mk_store("eBay")]

    # find lowest
    lowest = min(stores, key=lambda s: s["price_raw"])

    return {
        "name": product_name,
        "description": descriptions.get(product_name, "Reliable product with good reviews."),
        "specs": [
            "Warranty: 1 year",
            "Color options available",
            "High build quality"
        ],
        "stores": stores,
        "lowest": {
            "store": lowest["name"],
            "price": lowest["price"],
            "link": lowest["link"]
        }
    }
