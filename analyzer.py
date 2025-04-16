from openai import OpenAI
import pandas as pd
import streamlit as st
import json
import re

class DataAnalyzer:
    def __init__(self, key, data):
        self.data = data
        self.key = key
        self.client = OpenAI(api_key=self.key)
        self.df = self.load_clean_data()
        self.prompt_manager = self.PromptManager(self)

    def load_clean_data(self):
        df = pd.read_csv(self.data)
        df.dropna(inplace=True)
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def ai_summary(self):
        #prompt is pulled from the prompt manager
        prompt = self.prompt_manager.data_summary_prompt()

        response = self.client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI data analyst."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content

    def ai_json(self):
        # here we are generating another data but from a dynamic prompt
        prompt = self.prompt_manager.data_json_prompt()
        response = self.client.chat.completions.create(
            model = "gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You're an expert data visualization assistant"},
                {"role": "user", "content": prompt}
            ],
        )
        content = response.choices[0].message.content

        try:
            json_block = re.search(r"\[\s*{.*}\s*\]", content, re.DOTALL).group(0)
            print("JSON: ", json.loads(json_block))
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

    # This is where all the prompts will be managed and placed
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