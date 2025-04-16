import streamlit as st
import pandas as pd
from streamlit_ace import st_ace  # replaced code_editor with st_ace
import sqlite3

class SQLEditor:
    def __init__(self, uploaded_data):
        self.uploaded_data = uploaded_data
        try:
            self.df = pd.read_csv(self.uploaded_data)
            print("Uploaded: ", self.df)
            self.table_name = uploaded_data.name.split(".")[0]  # fix: use .name for file object
        except Exception as e:
            st.error(f"Failed to load CSV: {e}")

    def data_preview(self, n=100):
        if hasattr(self, "df"):
            st.write("Preview of uploaded data")
            st.dataframe(self.df.head(n))

    def create_connection(self):
        if hasattr(self, "df"):
            self.connection = sqlite3.connect(":memory:")
            self.cursor = self.connection.cursor()
            self.df.to_sql(self.table_name, self.connection, index=False, if_exists="replace")

    def create_code_editor(self):
        if not hasattr(self, "df"):
            return

        default_sql = f"SELECT * FROM {self.table_name} LIMIT 10;"

        sql_query = st_ace(
            value=default_sql,
            language="sql",
            theme="monokai",
            height=200,
            key="sql_editor"
        )

        if st.button("Run SQL") and sql_query:
            try:
                self.cursor.execute(sql_query)
                if sql_query.strip().lower().startswith("select"):
                    rows = self.cursor.fetchall()
                    columns = [desc[0] for desc in self.cursor.description]
                    result_df = pd.DataFrame(rows, columns=columns)
                    st.success("✅ Query ran successfully!")
                    st.dataframe(result_df)
                else:
                    self.connection.commit()
                    st.success("✅ Query executed (no output to display).")
            except Exception as e:
                st.error(f"❌ Error: {e}")
