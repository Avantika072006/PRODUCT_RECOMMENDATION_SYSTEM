
from recommendations import ProductRecommender

# Initialize recommendation system
recommender = ProductRecommender("products.csv")

# Select a product
product = "HP Laptop"

# Get recommendations
results = recommender.recommend(product, top_n=5)

print("\nRecommended Products:")
print(results[[
    "name",
    "category",
    "price",
    "rating",
    "similarity_score"
]])
