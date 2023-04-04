"""Forecast the total price.

Run this script using `python manage.py forecasting_price_forecast`
"""
import datetime
import random
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz
from django.core.management.base import BaseCommand
from django.db import models
from scipy.stats import linregress, pearsonr, spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import (
    CountVectorizer,
    TfidfTransformer,
    TfidfVectorizer,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from visualisation.models import GraphicsCard, Sale


def preprocess_text_series(series):
    # Convert the strings to lowercase
    series = series.str.lower()

    # Remove non-alphanumeric characters
    series = series.apply(lambda x: re.sub(r"\W+", " ", x))

    return series


def get_model_attributes(model_class, prefix=""):
    attributes = []
    for field in model_class._meta.fields:
        if isinstance(field, models.ForeignKey):
            # If the attribute is a foreign key, recursively get its attributes
            related_model = field.remote_field.model
            related_prefix = f"{prefix}{field.name}__"
            related_attributes = get_model_attributes(
                related_model, prefix=related_prefix
            )
            attributes += related_attributes
        elif field.name != "id":
            # If the attribute is not a foreign key, add its path to the list of attributes
            attribute_path = f"{prefix}{field.name}"
            attributes.append(attribute_path)
    return attributes


def calculate_percentage_error(y_true, y_pred):
    error = abs(y_true - y_pred) / y_true
    return error * 100


class Command(BaseCommand):
    help = ""

    def get_input_df(self, model_name):
        sale_attributes = get_model_attributes(Sale)
        qs = Sale.objects.filter(
            date__gte=datetime.datetime(2022, 7, 1, 0, 0, 0, tzinfo=pytz.UTC),
            gpu__model=model_name,
        )
        df = pd.DataFrame(list(qs.values(*sale_attributes)))
        if df.empty:
            return pd.DataFrame()

        # Create a new column with the day of the week as an integer value
        df["day_of_week"] = df["date"].dt.weekday

        df["date"] = df["date"].dt.date
        print(f"Input df shape: {df.shape}")
        return df

    def handle(self, *args, **kwargs):

        all_results = []
        keep_cols = [
            "gpu__g3d_mark_median",
            "gpu__model",
            "gpu__launch_date",
            "gpu__architecture__series",
            "gpu__architecture__year",
            "title",
            "date",
            "day_of_week",
        ]
        keep_cols = [
            # "gpu__g3d_mark_median",
            "title",
            "date",
            "day_of_week",
        ]
        number_of_runs_per_model = 3

        model_names = list(
            GraphicsCard.objects.all().values_list("model", flat=True)
        )
        for model_name in model_names:
            for idx in range(number_of_runs_per_model):
                new_result = self.train_on_gpu_model(model_name, keep_cols)
                if "name" in new_result.keys():
                    new_result["run"] = idx
                    all_results.append(new_result)

        results = pd.DataFrame(all_results)
        results_short = results.groupby(by=["name"]).median().reset_index()
        results_short.to_csv("forecast.csv", index=False)
        print(results.shape)

    def train_on_gpu_model(self, model_name, keep_cols):
        print(model_name)
        df = self.get_input_df(model_name)
        if df.empty:
            return {}

        # Convert the date column to a datetime object
        df["date"] = pd.to_datetime(df["date"])

        # Calculate the linear regression parameters
        slope, intercept, _, _, _ = linregress(
            df["date"].apply(lambda x: x.timestamp()), df["total_price"]
        )

        # Subtract the linear trend from the price data
        df["total_price"] = df["total_price"] - (
            slope * df["date"].apply(lambda x: x.timestamp()) + intercept
        )

        x_test, y_test, y_pred = self.evaluate_dataset(df, keep_cols)

        # Concatenate actual and predicted values into a dataframe
        results = pd.DataFrame({"Actual": y_test, "Predicted Diff": y_pred})
        results = pd.concat([x_test, results], axis=1)

        # Add the linear component back to the price data
        results = self.add_linear_trend_back_in(
            slope, intercept, results, "Actual", "Actual"
        )
        results = self.add_linear_trend_back_in(
            slope, intercept, results, "Predicted", "Predicted Diff"
        )

        # Calculate MAPE
        results["percentage_error"] = (
            results["Actual"] - results["Predicted"]
        ).abs() / results["Actual"]
        mape = results["percentage_error"].mean()
        print(f"   MAPE: {mape:0.4f}")

        # Calculate RMSLE
        results["logarithmic_error"] = (
            np.log1p(results["Actual"]) - np.log1p(results["Predicted"])
        ) ** 2
        rmsle = np.sqrt(results["logarithmic_error"].mean())
        print(f"   RMSLE: {rmsle:0.4f}")

        # self.scatter_plot(results)

        # Calculate Pearson correlation coefficient
        pearson_cc, _ = pearsonr(results["Actual"], results["Predicted"])
        print(f"   Pearson correlation coefficient: {pearson_cc:0.4f}")

        # Calculate Spearman rank correlation coefficient
        spearman_rcc, _ = spearmanr(results["Actual"], results["Predicted"])
        print(f"   Spearman rank correlation coefficient: {spearman_rcc:0.4f}")
        new_result = {
            "name": model_name,
            "mape": mape,
            "rmsle": rmsle,
            "pearson": pearson_cc,
            "spearman": spearman_rcc,
            "records": len(df),
        }
        return new_result

    def add_linear_trend_back_in(self, slope, intercept, df, new_col, old_col):
        df[new_col] = (
            (slope * df["date"].apply(lambda x: x.timestamp()))
            + intercept
            + df[old_col]
        )
        return df

    def scatter_plot(self, results):
        plt.scatter(results["Actual"], results["Predicted"])

        # Add a line of constant price
        min_val = results["Predicted"].min()
        max_val = results["Predicted"].max()
        plt.plot([min_val, max_val], [min_val, max_val], color="red")

        # Add labels and a title
        plt.xlabel("Actual values")
        plt.ylabel("Predicted values")
        plt.title("Scatter plot of Predicted and Actual values")

        # Set the minimum x and y values to 0
        plt.xlim(0)
        plt.ylim(0)

        # Make the plot square with equal aspect ratio
        plt.axis("equal")

        # Show the plot
        plt.show()

    def evaluate_dataset(self, df, keep_cols):
        # Split into features and target
        data = df.drop(
            columns=[c for c in df.columns.to_list() if c not in keep_cols]
        )
        y = df["total_price"]
        x_attrs = data.copy()

        data = self.feature_extraction_title(data)
        # X = self.custom_feature_extraction(X, ["untested", "waterblock"])

        # Drop the 'name' column as it has been vectorized
        data.drop(columns=["title", "date"], inplace=True)

        # One-hot encode categorical columns
        cat_cols = []
        for col in data.columns:
            if data[col].dtype == "object":
                cat_cols.append(col)
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
        x_encoded = pd.DataFrame(encoder.fit_transform(data[cat_cols]))
        x_encoded.columns = encoder.get_feature_names_out(cat_cols)
        data = data.drop(columns=cat_cols)
        data = pd.concat([data, x_encoded], axis=1)

        # Identify boolean columns
        bool_cols = [col for col in data.columns if data[col].dtype == "bool"]

        # Convert boolean columns to integers
        for col in bool_cols:
            data[col] = data[col].astype(int)

        # Split into training and testing sets
        random_state = random.randint(0, 100)
        x_train, x_test, y_train, y_test = train_test_split(
            data,
            y,
            test_size=0.2,
            random_state=random_state,
        )
        _, x_attrs_test, _, _ = train_test_split(
            x_attrs,
            y,
            test_size=0.2,
            random_state=random_state,
        )

        # Train the model
        model = RandomForestRegressor(
            n_estimators=15, criterion="absolute_error"
        )
        model.fit(x_train, y_train)

        # Evaluate the model on the testing set
        y_pred = model.predict(x_test)
        return x_attrs_test, y_test, y_pred

    def feature_extraction_title(self, data, max_features=25):
        data["title"] = preprocess_text_series(data["title"])

        # Use TfidfVectorizer with the custom tokenizer
        vectorizer = TfidfVectorizer(
            stop_words="english", max_features=max_features
        )
        x_name = vectorizer.fit_transform(data["title"])

        print(vectorizer.get_feature_names_out())

        # Convert the sparse matrix to a DataFrame
        name_features = pd.DataFrame(
            x_name.toarray(), columns=vectorizer.get_feature_names_out()
        )

        # Concatenate the new DataFrame with the original DataFrame
        data = pd.concat([data, name_features], axis=1)
        return data

    def custom_feature_extraction(
        self, df, feature_names, column_name="title"
    ):
        # Use CountVectorizer with custom feature names
        vectorizer = CountVectorizer(
            vocabulary=feature_names, stop_words="english"
        )
        x_count = vectorizer.fit_transform(df[column_name])

        # Convert term-frequency matrix to tf-idf matrix
        transformer = TfidfTransformer()
        x_tfidf = transformer.fit_transform(x_count)

        # Convert the sparse matrix to a DataFrame
        feature_df = pd.DataFrame(
            x_tfidf.toarray(), columns=vectorizer.get_feature_names_out()
        )

        # Concatenate the new DataFrame with the original DataFrame
        df = pd.concat([df, feature_df], axis=1)
        return df
