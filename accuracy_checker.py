import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Scraping Accuracy Checker",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Scraping Accuracy Checker")

st.write("""
Upload your scraped CSV file. Then manually mark whether each scraped field is correct or incorrect.
This version works with your current columns: date, title, article.
""")

uploaded_file = st.file_uploader(
    "Upload your scraped CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Scraped Data Preview")
    st.dataframe(df.head())

    # Your actual CSV columns
    required_fields = ["date", "title", "article"]

    available_fields = [col for col in required_fields if col in df.columns]

    if not available_fields:
        st.error("Required columns were not found. Your CSV should have date, title, and article columns.")
    else:
        st.subheader("Completeness Rate")

        total_required_fields = len(df) * len(available_fields)
        non_empty_fields = df[available_fields].notna().sum().sum()

        completeness_rate = (non_empty_fields / total_required_fields) * 100

        st.metric("Completeness Rate", f"{completeness_rate:.2f}%")

        st.write("Non-empty fields:", int(non_empty_fields))
        st.write("Total required fields:", int(total_required_fields))

        st.subheader("Manual Accuracy Checking")

        sample_size = st.number_input(
            "How many rows do you want to check manually?",
            min_value=1,
            max_value=len(df),
            value=min(10, len(df))
        )

        sample_df = df.head(sample_size).copy()

        # Add manual correctness columns
        sample_df["date_correct"] = True
        sample_df["title_correct"] = True
        sample_df["article_correct"] = True

        st.info("""
Check the original newspaper website manually.
Keep the box checked if the field is correct.
Uncheck it if the field is wrong.
""")

        edited_df = st.data_editor(
            sample_df,
            use_container_width=True,
            num_rows="fixed"
        )

        if st.button("Calculate Accuracy"):
            correct_columns = [
                "date_correct",
                "title_correct",
                "article_correct"
            ]

            total_checked_fields = len(edited_df) * len(correct_columns)

            correct_fields = edited_df[correct_columns].sum().sum()

            field_accuracy = (correct_fields / total_checked_fields) * 100

            edited_df["fully_correct_record"] = edited_df[correct_columns].all(axis=1)

            total_records = len(edited_df)
            fully_correct_records = edited_df["fully_correct_record"].sum()

            record_accuracy = (fully_correct_records / total_records) * 100

            st.subheader("Accuracy Result")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Field-level Accuracy", f"{field_accuracy:.2f}%")

            with col2:
                st.metric("Record-level Accuracy", f"{record_accuracy:.2f}%")

            with col3:
                st.metric("Checked Records", total_records)

            st.write("Correct fields:", int(correct_fields))
            st.write("Total checked fields:", int(total_checked_fields))
            st.write("Fully correct records:", int(fully_correct_records))
            st.write("Total checked records:", int(total_records))

            st.subheader("Field-wise Accuracy")

            field_accuracy_data = []

            for col in correct_columns:
                checked = len(edited_df)
                correct = edited_df[col].sum()
                accuracy = (correct / checked) * 100

                field_accuracy_data.append({
                    "Field": col.replace("_correct", ""),
                    "Correct": int(correct),
                    "Checked": int(checked),
                    "Accuracy (%)": round(accuracy, 2)
                })

            field_accuracy_df = pd.DataFrame(field_accuracy_data)

            st.dataframe(field_accuracy_df)

            csv_result = field_accuracy_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Accuracy Report CSV",
                data=csv_result,
                file_name="scraping_accuracy_report.csv",
                mime="text/csv"
            )