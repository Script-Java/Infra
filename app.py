import streamlit as st
from analyzer import DataAnalyzer
from renderer import Renderer
from sql_editory import SQLEditor

st.set_page_config(page_title="AI Data Analyzer", layout="wide")

st.title("⚡ AI-Powered Data Analyzer ⚡")
st.markdown("Upload a CSV file and get AI-generated insights and dashboard summaries.")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

with st.sidebar:
    st.image("infera.png", width=300)
    api_key = st.text_input('Openai Key')
    csv_file = st.file_uploader('Upload a CSV file 🏆', type=['csv'])
    st.subheader("⚙️ Settings")
    preview_count = st.slider("Number of previews", min_value=10, max_value=100, value=20)

# added tabs to better layout everything
tab1, tab2, tab3, tab4, tab5= st.tabs(['🔢 Preview', '🐍 Statistics', '🤖 Summary', '💬 Ask Questions', '💻 Query'])

if csv_file:
    analyzer = DataAnalyzer(api_key, csv_file)
    # added these tables next to each other
    with tab1:
        st.subheader('🔍 Data Preview')
        st.dataframe(analyzer.data_preview(preview_count))
    with tab2:
        st.subheader("📊 Statistical Summary")
        st.dataframe(analyzer.data_describe())
    with tab3:
        st.subheader("🤖 AI Summary")
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
        editor = SQLEditor(csv_file)
        editor.data_preview(preview_count)
        editor.create_connection()
        editor.create_code_editor()


else:
    st.info("Please upload a CSV file")