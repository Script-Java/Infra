import plotly.express as px
import streamlit as st

class Renderer:
    def __init__(self, charts, df):
        self.charts = charts
        self.df = df

    def render_charts(self):
        for chart in self.charts:
            chart_type = chart.get('chart_type')
            x = chart.get('x')
            y = chart.get('y')
            title = chart.get('title')
            description = chart.get('description')
            print("X: ", x)
            print("Y: ", y)

            # Handle list of Y columns
            if isinstance(y, list):
                y_valid = [col for col in y if col in self.df.columns]
                if not y_valid:
                    st.warning(f"Skipping chart: {title} (no valid Y columns)")
                    continue
            else:
                if x not in self.df.columns or y not in self.df.columns:
                    st.warning(f"Skipping chart: {title} (invalid X or Y)")
                    continue
                y_valid = [y]

            fig = None
            if chart_type == 'bar':
                fig = px.bar(self.df, x=x, y=y_valid, title=title)
            elif chart_type == 'line':
                fig = px.line(self.df, x=x, y=y_valid, title=title)
            elif chart_type == 'scatter' and len(y_valid) == 1:
                fig = px.scatter(self.df, x=x, y=y_valid[0], title=title)
            elif chart_type == 'histogram' and len(y_valid) == 1:
                fig = px.histogram(self.df, x=y_valid[0], title=title)

            if fig:
                st.plotly_chart(fig, use_container_width=True)
                st.caption(description)
                st.balloons()

