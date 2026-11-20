from database import (
    save_products,
    save_interaction,
    get_recommendations_from_history,
    register_user,
    login_user,
    get_all_interactions,
    save_review,
    get_product_reviews
)
import streamlit as st
import pandas as pd
from recommendations import ProductRecommender

st.set_page_config(
    page_title="Smart Product Recommender",
    page_icon="🛍️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main {
    background-color: #f7f8fc;
}
.product-card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}
.stButton button {
    border-radius: 8px;
    background-color: #6046e8;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🛍️ Smart Product Store")
    st.subheader("Welcome! Login or Create an Account")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login"):

            if login_user(username, password):

                st.session_state.logged_in = True
                st.session_state.username = username

                st.success("Login successful!")
                st.rerun()

            else:
                st.error("Invalid username or password.")

    with tab2:

        new_username = st.text_input(
            "Create Username",
            key="register_username"
        )

        new_password = st.text_input(
            "Create Password",
            type="password",
            key="register_password"
        )

        if st.button("Register"):

            if not new_username.strip() or len(new_password) < 8:
                st.warning(
                    "Enter a username and password of at least 8 characters."
                )

            else:
                success, message = register_user(
                    new_username.strip(),
                    new_password
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.stop()
if st.sidebar.button("Logout"):

    st.session_state.logged_in = False
    st.session_state.username = ""

    st.rerun()
# Load data
@st.cache_resource
def load_recommender():
    return ProductRecommender("products.csv")

recommender = load_recommender()
products = recommender.products
save_products(products)
# Header
st.title("🛍️ Smart Product Store")
st.write("Discover products recommended using Machine Learning.")

st.divider()

# Sidebar
st.sidebar.title("Product Filters")

categories = ["All"] + sorted(
    products["category"].unique().tolist()
)

selected_category = st.sidebar.selectbox(
    "Select Category",
    categories
)

max_price = st.sidebar.slider(
    "Maximum Price",
    min_value=0,
    max_value=int(products["price"].max()),
    value=int(products["price"].max())
)

# Search
search = st.text_input(
    "🔍 Search products",
    placeholder="Search laptops, mobiles, headphones..."
)

# Filter products
filtered = products.copy()

if selected_category != "All":
    filtered = filtered[
        filtered["category"] == selected_category
    ]

filtered = filtered[
    pd.to_numeric(filtered["price"]) <= max_price
]

if search:
    filtered = filtered[
        filtered["name"].str.contains(
            search, case=False, na=False
        )
    ]

# Product listing
st.subheader("Explore Products")

if filtered.empty:
    st.warning("No products found.")
else:
    cols = st.columns(3)
    for i, (_, product) in enumerate(filtered.iterrows()):

        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(product["name"])
                st.write("Category:", product["category"])
                st.write("Price: ₹", product["price"])
                st.write("⭐", product["rating"])

                
if st.button(
    "Get Similar Products",
    key=f"recommend_{product['product_id']}"
):
    st.session_state.selected_product = product["name"]

    save_interaction(
        "user_001",
        product["name"],
        "view"
    )


# Recommendations
if "selected_product" in st.session_state:

    st.divider()

    st.subheader(
        f"✨ Recommended for: {st.session_state.selected_product}"
    )

    recommendations = recommender.recommend(
        st.session_state.selected_product,
        top_n=5
    )

    cols = st.columns(3)

    for i, (_, product) in enumerate(
        recommendations.iterrows()
    ):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(product["name"])
                st.write("Category:", product["category"])
                st.write("Price: ₹", product["price"])
                st.write("⭐", product["rating"])
                st.progress(
                    min(
                        float(product["similarity_score"]) / 100,
                        1.0
                    )
                )
                st.caption(
                    f"Similarity: {product['similarity_score']}%"
                )

st.divider()

st.subheader("🕒 Your Recently Viewed Products")

user_id = st.session_state.username
history = get_recommendations_from_history(user_id)

if history:

    for item in history:
        st.write("👁️", item)

else:
    st.info("You haven't viewed any products yet.")

# Collaborative Filtering Section

st.divider()

st.subheader("👥 Recommended By Similar Users")

all_interactions = get_all_interactions()

collaborative_results = recommender.recommend_collaborative(
    st.session_state.username,
    all_interactions,
    top_n=5
)

if not collaborative_results.empty:

    cols = st.columns(3)

    for i, (_, product) in enumerate(
        collaborative_results.iterrows()
    ):

        with cols[i % 3]:

            with st.container(border=True):

                st.subheader(product["name"])

                st.write("Category:", product["category"])

                st.write("Price: ₹", product["price"])

                st.write("⭐", product["rating"])

else:

    st.info(
        "Not enough similar user activity yet. "
        "Ask other test users to explore products."
    )
st.divider()
st.subheader("⭐ Rate and Review This Product")

rating = st.selectbox(
    "Select your rating",
    [1, 2, 3, 4, 5]
)

review_text = st.text_area("Write your review")

if st.button("Submit Review"):
    if review_text.strip():
        save_review(
            st.session_state.username,
            selected_product["name"],
            rating,
            review_text
        )
        st.success("Review submitted successfully!")
    else:
        st.warning("Please write a review.")

st.subheader("Customer Reviews")

reviews = get_product_reviews(selected_product["name"])

if reviews:
    for review in reviews:
        st.write("⭐" * review["rating"])
        st.write(review["review"])
        st.caption("By: " + review["user_id"])
        st.divider()
else:
    st.info("No reviews yet. Be the first to review!")