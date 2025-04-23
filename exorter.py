class Exporter:
    def __init__(self, df, format):
        self.df = df
        self.format = format

    def export_file(self):
        if self.format == "csv":
            return self.df.to_csv(index=False).encode('utf-8')
        elif self.format == "excel":
            from io import BytesIO
            buffer = BytesIO()
            self.df.to_excel(buffer, index=False)
            return buffer.getvalue()
        elif self.format == "json":
            return self.df.to_json(orient="records", indent=2).encode('utf-8')
        elif self.format == "parquet":
            from io import BytesIO
            buffer = BytesIO()
            self.df.to_parquet(buffer, index=False)
            return buffer.getvalue()
        else:
            raise ValueError("Unsupported export format")