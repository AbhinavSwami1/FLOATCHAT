from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("postgresql://postgres:1234@localhost:5432/floatchat")
df.to_sql("argo_data", engine, if_exists="replace", index=False)
