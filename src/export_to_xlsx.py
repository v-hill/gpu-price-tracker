"""
Main script for running the scraper.
"""
import pandas as pd
from sqlalchemy import create_engine
from configuration import DATABASE_NAME

# SQLAlchemy connectable
cnx = create_engine(f"sqlite:///{DATABASE_NAME}").connect()

df_log = pd.read_sql_table("log", cnx)  # Log table
df_gpu = pd.read_sql_table("gpu", cnx)  # GPU table
df_sale = pd.read_sql_table("sale", cnx)  # Sale table

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter("gpu.xlsx", engine="xlsxwriter")

# Write each dataframe to a different worksheet.
df_log.to_excel(writer, sheet_name="Log", index=False)
df_gpu.to_excel(writer, sheet_name="GPU", index=False)
df_sale.to_excel(writer, sheet_name="Sales", index=False)

# Close the Pandas Excel writer and output the Excel file.
writer.save()
