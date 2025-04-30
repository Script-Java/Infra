from openai import OpenAI
import pandas as pd
import streamlit as st
import json
import re
import sqlite3

class DataAnalyzer:
    def __init__(self, key, data, null=False, dup=False, index=False):
        self.null = null
        self.dup = dup
        self.index = index
        self.data = data
        self.key = key
        self.client = OpenAI(api_key=self.key)
        self.df = self.load_data(drop_na=null, drop_dup=dup, reset_index=index)
        self.prompt_manager = self.PromptManager(self)

    def data_report_builder(self):
        df = self.load_data(drop_na=self.null, drop_dup=self.dup, reset_index=self.index, reset_data=True)
        total_null = df.isna().sum()
        total_duplicated = df.duplicated().sum()
        data_len = len(df)
        st.markdown(f"**Total Rows:** {data_len}")
        st.markdown(f"**Total Duplicate Rows:** {total_duplicated}")
        null_report = pd.DataFrame({
            "Column": total_null.index,
            "Missing Values": total_null.values,
            "% Missing": (total_null.values / data_len * 100).round(2)
        })
        st.dataframe(null_report[null_report["Missing Values"] > 0])

    def load_data(self, drop_na=True, drop_dup=True, reset_index=True, reset_data=False):
        if reset_data:
            self.data.seek(0)

        if self.data.name.endswith('.csv'):
            self.df = pd.read_csv(self.data)
        elif self.data.name.endswith('.xlsx'):
            self.df = pd.read_excel(self.data)
        elif self.data.name.endswith('.json'):
            self.df = pd.read_json(self.data)
        elif self.data.name.endswith('.parquet'):
            self.df = pd.read_parquet(self.data)
        elif self.data.name.endswith('.db') or self.data.name.endswith('.sqlite'):
            conn = sqlite3.connect(self.data.name)
            self.df = pd.read_sql_query("SELECT * FROM your_table", conn)
        elif self.data.name.endswith('.txt'):
            self.df = pd.read_csv(self.data, delimiter="\t")
        else:
            st.error("Unsupported file format.")

        if drop_na:
            self.df.dropna(inplace=True)
        if drop_dup:
            self.df.drop_duplicates(inplace=True)
        if reset_index:
            self.df.reset_index(drop=True, inplace=True)

        return self.df

    def ai_summary(self):
        prompt = self.prompt_manager.data_summary_prompt()
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI data analyst."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content

    def ai_json(self):
        prompt = self.prompt_manager.data_json_prompt()
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You're an expert data visualization assistant"},
                {"role": "user", "content": prompt}
            ],
        )
        content = response.choices[0].message.content

        try:
            json_block = re.search(r"\[\s*{.*}\s*\]", content, re.DOTALL).group(0)
            return json.loads(json_block)
        except json.JSONDecodeError as e:
            st.error("❌ Failed to parse AI JSON response.")
            st.code(content, language="json")
            st.exception(e)
            return []

    def data_chat(self, user_query):
        if user_query:
            with st.chat_message("user"):
                st.markdown(user_query)

            st.session_state.chat_history.append(("user", user_query))
            prompt = self.prompt_manager.data_chat_prompt(user_query)

            message_history = [
                {"role": role, "content": content} for role, content in st.session_state.chat_history
            ]
            message_history.insert(0, {"role": "system", "content": "You are a smart and friendly data assistant."})
            message_history.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=message_history,
            )
            ai_response = response.choices[0].message.content.strip()

            with st.chat_message("assistant"):
                st.markdown(ai_response)

            st.session_state.chat_history.append(("assistant", ai_response))
        else:
            st.error("Please enter a question to ask the assistant.")

    def data_describe(self):
        return self.df.describe().round(2)

    def data_preview(self, n=20):
        return self.df.head(n)

    class PromptManager:
        def __init__(self, parent):
            self.parent = parent

        def data_summary_prompt(self):
            return f"""
        You're a professional data analyst. Based on the sample below, provide a **brief, one-paragraph summary** describing what this dataset is about.

        DATA SAMPLE:
        {self.parent.df.head(100).to_string(index=False)}

        Your response should:
        - Be 3–4 sentences max
        - Describe the purpose and type of data
        - Mention any major categories or patterns
        - Avoid listing all columns or repeating raw data

        Make it readable, natural, and clear to a non-technical audience.
        """.strip()

        def data_json_prompt(self):
            columns_list = self.parent.df.columns.tolist()
            column_info = "\n".join([f"- {col}" for col in columns_list])

            return f"""
        You are a data visualization assistant. Your job is to generate 1–3 chart ideas **in JSON format** using the dataset below.

        🔒 Important rules (follow strictly):
        - Use ONLY the column names listed under "AVAILABLE COLUMNS"
        - Every chart must include both a valid "x" and "y" column (NO blanks)
        - Do NOT invent column names or use abstract labels like "category" or "amount"
        - All chart suggestions should be clear, distinct, and based on the actual data

        📌 Output format:
        [
          {{
            "title": "Your chart title",
            "chart_type": "bar",
            "x": "COLUMN_NAME",
            "y": "COLUMN_NAME",
            "description": "What this chart shows"
          }}
        ]

        AVAILABLE COLUMNS:
        {column_info}

        DATA SAMPLE:
        {self.parent.df.head(5).to_string(index=False)}

        STATS:
        {self.parent.df.describe().to_string()}
        """.strip()

        def data_chat_prompt(self, user_query):
            sample_data = self.parent.df.head(10).to_csv(index=False)
            columns = self.parent.df.columns.tolist()
            return f"""
                You are a professional data analyst.
                
                Here is a sample of the dataset (in CSV format):
                {sample_data}
                
                Columns:
                {columns}
                
                The user asked: "{user_query}"
                
                Answer clearly in plain English. Use the dataset to find patterns, trends, comparisons, or summaries. Provide specific numbers if possible. Do not write or mention Python code.
                """.strip()
