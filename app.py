import streamlit as st
from analyzer import DataAnalyzer
from renderer import Renderer
from sql_editory import SQLEditor
from exporter import Exporter
import pandas as pd
import sqlite3

st.set_page_config(page_title="AI Data Analyzer", layout="wide")

st.title("⚡ AI-Powered Data Analyzer ⚡")
st.markdown("Upload a CSV file and get AI-generated insights and dashboard summaries.")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Options for data cleaning
null = ''
dup = ''
index = ''

with st.sidebar:
    st.image("infera.png", width=300)
    api_key = st.text_input('Openai Key')
    csv_file = st.file_uploader('Upload a dataset 🏆', type=['csv','xlsx','json','parquet','db','sqlite','txt'])
    st.subheader("⚙️ Settings")
    preview_count = st.slider("Number of previews", min_value=10, max_value=100, value=20)
    null_option = st.checkbox("Remove Null")
    if null_option:
        null = True
    dup_option = st.checkbox("Remove Duplicates")
    if dup_option:
        dup = True
    index_option = st.checkbox("Reset Index")
    if index_option:
        index = True

# data loader
def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file)
    elif file.name.endswith('.json'):
        return pd.read_json(file)
    elif file.name.endswith('.parquet'):
        return pd.read_parquet(file)
    elif file.name.endswith('.db') or file.name.endswith('.sqlite'):
        conn = sqlite3.connect(file.name)
        return pd.read_sql_query("SELECT * FROM your_table", conn)
    elif file.name.endswith('.txt'):
        return pd.read_csv(file, delimiter="\t")  # or prompt for custom delimiter
    else:
        raise ValueError("Unsupported file format.")

# added tabs to better layout everything
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(['🔢 Preview', '🐍 Statistics', '🤖 AI Dashboard', '💬 Ask Questions', '🧑‍💻 SQL', '⬇️ Export'])

if csv_file:
    try:
        analyzer = DataAnalyzer(api_key, csv_file, null, dup, index)
        csv_file.seek(0)
        editor = SQLEditor(csv_file)

        with tab1:
            st.subheader('🔍 Data Preview')
            st.dataframe(analyzer.data_preview(preview_count))
            st.subheader('📄 Data Report')
            analyzer.data_report_builder()

        with tab2:
            st.subheader("📊 Statistical Summary")
            st.dataframe(analyzer.data_describe())

        with tab3:
            st.subheader("🤖 AI Dashboard Generator")
            if st.button('Generate AI Insights'):
                with st.spinner('Generating AI Insights...'):
                    summary = analyzer.ai_summary()
                    st.write(summary)
                    st.subheader("🌐 AI Dashboard")
                    chart_config = analyzer.ai_json()
                    renderer = Renderer(chart_config, analyzer.df)
                    renderer.render_charts()

        with tab4:
            if st.button("🧹 Clear Chat"):
                st.session_state.chat_history = []

            user_input = st.chat_input("Ask something about the data...")

            for role, message in st.session_state.chat_history:
                with st.chat_message(role):
                    st.markdown(message)

            if user_input:
                with st.spinner('Thinking...'):
                    analyzer.data_chat(user_input)

        with tab5:
            editor.table_info()
            editor.create_connection()
            editor.create_code_editor()

        with tab6:
            st.subheader("⬇️ Export Data")
            export_format = st.selectbox("Choose Export Format", ["csv", "excel", "json", "parquet"])
            if st.button("Export File"):
                exporter = Exporter(analyzer.df, export_format)
                exported_data = exporter.export_file()
                st.download_button(
                    label=f"Download as {export_format.upper()}",
                    data=exported_data,
                    file_name=f"exported_data.{export_format}",
                    mime="application/octet-stream"
                )

    except Exception as e:
        st.error(f"❌ An error occurred while processing the CSV file: {e}")
else:
    st.info("Please upload a CSV file")
