
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ProductRecommender:

    def __init__(self, csv_file):
        self.products = pd.read_csv(csv_file)

        # Handle missing values
        self.products = self.products.fillna("")

        # Combine product features
        self.products["features"] = (
            self.products["name"].astype(str) + " " +
            self.products["category"].astype(str) + " " +
            self.products["description"].astype(str)
        )

        # Convert text into numerical vectors
        self.vectorizer = TfidfVectorizer(
            stop_words="english"
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.products["features"]
        )

        # Calculate cosine similarity
        self.similarity_matrix = cosine_similarity(
            self.tfidf_matrix
        )

    def recommend(self, product_name, top_n=5):

        matches = self.products[
            self.products["name"].str.lower()
            == product_name.lower()
        ]

        if matches.empty:
            return pd.DataFrame()

        index = matches.index[0]

        scores = list(
            enumerate(self.similarity_matrix[index])
        )

        scores = sorted(
            scores,
            key=lambda x: x[1],
            reverse=True
        )

        # Remove selected product itself
        scores = [
            item for item in scores
            if item[0] != index
        ]

        top_products = scores[:top_n]

        indices = [item[0] for item in top_products]

        result = self.products.iloc[indices].copy()

        result["similarity_score"] = [
            round(float(item[1]) * 100, 2)
            for item in top_products
        ]

        return result

    def recommend_for_history(self, viewed_products, top_n=5):

        if not viewed_products:
            return pd.DataFrame()

        # Find indices of previously viewed products
        indices = self.products[
            self.products["name"].isin(viewed_products)
        ].index.tolist()

        if not indices:
            return pd.DataFrame()

        # Calculate average similarity across viewed products
        scores = self.similarity_matrix[indices].mean(axis=0)

        # Exclude products already viewed
        results = []

        for i, score in enumerate(scores):
            product_name = self.products.iloc[i]["name"]

            if product_name not in viewed_products:
                results.append((i, float(score)))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)

        top_results = results[:top_n]

        recommended_indices = [
            item[0] for item in top_results
        ]

        recommendations = self.products.iloc[
            recommended_indices
        ].copy()

        recommendations["similarity_score"] = [
            round(score * 100, 2)
            for _, score in top_results
        ]

        return recommendations

    def recommend_collaborative(
        self, user_id, interactions, top_n=5
    ):

        if not interactions:
            return pd.DataFrame()

        # Convert interactions into a DataFrame
        data = pd.DataFrame(interactions)

        if data.empty:
            return pd.DataFrame()

        # Create user-product interaction matrix
        user_product = pd.crosstab(
            data["user_id"],
            data["product_name"]
        )

        # Check whether current user exists
        if user_id not in user_product.index:
            return pd.DataFrame()

        # Calculate similarity between users
        user_similarity = cosine_similarity(user_product)

        similarity_df = pd.DataFrame(
            user_similarity,
            index=user_product.index,
            columns=user_product.index
        )

        # Find users similar to current user
        similar_users = similarity_df[user_id].drop(
            user_id
        ).sort_values(ascending=False)

        # Calculate recommendation scores
        scores = {}

        for other_user, similarity in similar_users.items():

            if similarity <= 0:
                continue

            for product in user_product.columns:

                # Don't recommend already viewed products
                if user_product.loc[user_id, product] > 0:
                    continue

                if user_product.loc[other_user, product] > 0:

                    scores[product] = (
                        scores.get(product, 0) + similarity
                    )

        if not scores:
            return pd.DataFrame()

        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        result = self.products[
            self.products["name"].isin(
                [product for product, score in ranked]
            )
        ].copy()

        score_map = dict(ranked)

        result["collaborative_score"] = result["name"].map(
            score_map
        )

        result = result.sort_values(
            "collaborative_score",
            ascending=False
        )

        return result
