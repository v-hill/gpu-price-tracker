"""Find the best price indicator from the available attributes.

Run this script using `python manage.py forecasting_best_indicator`
"""

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from visualisation.models import Sale


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

    def get_input_df(self):
        current_month = 2
        current_year = 2023
        sale_attributes = get_model_attributes(Sale)
        qs = Sale.objects.filter(
            date__month=current_month, date__year=current_year
        )
        df = pd.DataFrame(list(qs.values(*sale_attributes)))
        df["date"] = df["date"].dt.date
        return df

    def handle(self, *args, **kwargs):
        df = self.get_input_df()
        print(df.shape)

        # Split into features and target
        data = df.drop(
            columns=[
                "total_price",
                "title",
                "outlier",
                "date",
            ]
        )

        all_cols_to_try = [
            "gpu__g3d_mark_median",
            "gpu__architecture__year",
            "gpu__launch_date",
            "gpu__launch_price",
            "gpu__memory_size",
            "gpu__model",
            "gpu__passmark_samples",
            "gpu__short_model",
            "gpu__architecture__series",
            "gpu__architecture__architecture",
        ]
        all_mapes = {}
        for keep_col in all_cols_to_try:
            x_test, y_test, y_pred = self.evaluate_dataset(df, data, keep_col)

            # Concatenate actual and predicted values into a dataframe
            results = pd.DataFrame({"Actual": y_test, "Predicted": y_pred})
            results = pd.concat([x_test, results], axis=1)

            # Calculate and print MAPE
            results["mape"] = (
                results["Actual"] - results["Predicted"]
            ).abs() / results["Actual"]
            all_mapes[keep_col] = results["mape"].mean()
        all_mapes = {
            k: v
            for k, v in sorted(all_mapes.items(), key=lambda item: item[1])
        }
        for k, v in all_mapes.items():
            print(f"{k} : {v:0.4f}")

    def evaluate_dataset(self, df, attrs, keep_col):
        attrs, y = self.get_training_dataset(df, attrs, keep_col)

        # One-hot encode categorical columns
        cat_cols = [
            col for col in attrs.columns if attrs[col].dtype == "object"
        ]
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
        x_encoded = pd.DataFrame(encoder.fit_transform(attrs[cat_cols]))
        x_encoded.columns = encoder.get_feature_names_out(cat_cols)
        attrs = attrs.drop(columns=cat_cols)
        attrs = pd.concat([attrs, x_encoded], axis=1)

        # Identify boolean columns
        bool_cols = [
            col for col in attrs.columns if attrs[col].dtype == "bool"
        ]

        # Convert boolean columns to integers
        for col in bool_cols:
            attrs[col] = attrs[col].astype(int)

        # Split into training and testing sets
        x_train, x_test, y_train, y_test = train_test_split(
            attrs, y, test_size=0.2, random_state=42
        )

        # Train the model
        model = RandomForestRegressor(
            n_estimators=8, criterion="absolute_error"
        )
        model.fit(x_train, y_train)

        # Evaluate the model on the testing set
        y_pred = model.predict(x_test)
        return x_test, y_test, y_pred

    def get_training_dataset(self, df, data, keep_col):
        all_potential_drops = [
            "founders",
            "gpu__architecture__architecture",
            "gpu__architecture__series",
            "gpu__architecture__year",
            "gpu__g3d_mark_median",
            "gpu__launch_date",
            "gpu__launch_price",
            "gpu__memory_size_restrict",
            "gpu__memory_size",
            "gpu__model",
            "gpu__passmark_samples",
            "gpu__short_model",
            "gpu__super_restrict",
            "gpu__super",
            "gpu__tdp",
            "gpu__ti_restrict",
            "gpu__ti",
        ]
        drop_cols = [c for c in all_potential_drops if c != keep_col]
        data = data.drop(columns=drop_cols)
        target = df["total_price"]
        return data, target
