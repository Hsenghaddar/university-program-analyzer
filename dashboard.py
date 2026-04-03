import streamlit as st
import pandas as pd
import plotly.express as px
import os
st.set_page_config(page_title="EU University Program Analyzer", layout="wide")

@st.cache_data
def load_data(file_name):
    if not os.path.exists(file_name):
        st.error(f"{file_name} not found in project folder.")
        st.stop()

    df = pd.read_csv(file_name)

    if "program_duration" in df.columns:
        df.rename(columns={"program_duration": "program_duration_year"}, inplace=True)

    df["tuition_fee_usd_total"] = pd.to_numeric(df["tuition_fee_usd_total"], errors="coerce")
    df["program_duration_year"] = pd.to_numeric(df["program_duration_year"], errors="coerce")

    df = df.dropna(subset=["tuition_fee_usd_total"])

    return df

st.sidebar.title("📊 Dataset Selection")

dataset_option = st.sidebar.selectbox(
    "Choose Dataset",
    [
        "study_eu_programs_cleaned.csv",
        "study_eu_programs_with_ranking.csv",
        "study_eu_programs.csv",
    ],
)

df = load_data(dataset_option)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Filters")

if not df.empty:
    min_fee = int(df["tuition_fee_usd_total"].min(skipna=True))
    max_fee = int(df["tuition_fee_usd_total"].max(skipna=True))
else:
    min_fee, max_fee = 0, 0

fee_range = st.sidebar.slider(
    "Tuition Fee Range (USD)",
    min_fee,
    max_fee,
    (min_fee, max_fee),
)

degree_filter = st.sidebar.multiselect(
    "Degree Type",
    options=df["degree"].dropna().unique(),
    default=df["degree"].dropna().unique(),
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=df["university_location"].dropna().unique(),
    default=df["university_location"].dropna().unique(),
)

keyword = st.sidebar.text_input("Keyword in Program Title").strip().lower()
filtered_df = df[
    (df["tuition_fee_usd_total"].between(fee_range[0], fee_range[1]))
    & (df["degree"].isin(degree_filter))
    & (df["university_location"].isin(country_filter))
]

if keyword:
    filtered_df = filtered_df[
        filtered_df["program_name"].str.lower().str.contains(keyword)
        | filtered_df["university_name"].str.lower().str.contains(keyword)
    ]

st.title("🎓 European University Program Analyzer")
st.markdown("Explore tuition, rankings, and trends across EU programs.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Programs", len(filtered_df))
col2.metric("Avg Tuition (USD)", round(filtered_df["tuition_fee_usd_total"].mean(), 2) if not filtered_df.empty else 0)
col3.metric("Avg Duration (Years)", round(filtered_df["program_duration_year"].mean(), 2) if not filtered_df.empty else 0)
col4.metric("Countries", filtered_df["university_location"].nunique() if not filtered_df.empty else 0)

st.markdown("---")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["💰 Tuition Analysis", "🏆 Ranking Analysis", "🌍 Geographic Insights", "📊 Correlation", "🔍 Program Explorer", "🏫 University Spotlight"]
)

with tab1:
    if not filtered_df.empty:
        st.subheader("Tuition Distribution")
        fig1 = px.histogram(filtered_df, x="tuition_fee_usd_total", nbins=30, title="Distribution of Tuition Fees")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Average Tuition by Degree")
        degree_avg = filtered_df.groupby("degree")["tuition_fee_usd_total"].mean().reset_index()
        fig2 = px.bar(degree_avg, x="degree", y="tuition_fee_usd_total", title="Average Tuition per Degree")
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    if "global_ranking" in filtered_df.columns and not filtered_df.empty:
        st.subheader("Ranking Distribution")

        def ranking_group(rank):
            if pd.isna(rank):
                return "N/A"
            if rank <= 100:
                return "Top 100"
            elif rank <= 300:
                return "Top 300"
            elif rank <= 600:
                return "Top 600"
            else:
                return "600+"

        filtered_df["ranking_group"] = filtered_df["global_ranking"].apply(ranking_group)
        ranking_counts = filtered_df["ranking_group"].value_counts().reset_index()
        ranking_counts.columns = ["ranking_group", "count"]

        fig3 = px.bar(ranking_counts, x="ranking_group", y="count", title="Programs by Ranking Tier")
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Tuition vs Ranking")
        fig4 = px.scatter(
            filtered_df,
            x="global_ranking",
            y="tuition_fee_usd_total",
            hover_data=["university_name", "program_name"],
            title="Does Better Ranking Mean Higher Tuition?",
        )
        st.plotly_chart(fig4, use_container_width=True)

with tab3:
    if not filtered_df.empty:
        st.subheader("Programs per Country")
        country_counts = filtered_df["university_location"].value_counts().reset_index()
        country_counts.columns = ["country", "count"]
        fig5 = px.bar(country_counts, x="country", y="count", title="Number of Programs by Country")
        st.plotly_chart(fig5, use_container_width=True)

    st.info("🌍 Map view requires latitude/longitude data. Add geocoded coordinates if available.")

with tab4:
    if not filtered_df.empty:
        st.subheader("Correlation Matrix")
        numeric_df = filtered_df[["tuition_fee_usd_total", "program_duration_year"]].copy()
        if "global_ranking" in filtered_df.columns:
            numeric_df["global_ranking"] = pd.to_numeric(filtered_df["global_ranking"], errors="coerce")

        fig6 = px.imshow(numeric_df.corr(), text_auto=True, title="Correlation Between Numeric Variables")
        st.plotly_chart(fig6, use_container_width=True)

        st.subheader("Tuition vs Duration")
        fig7 = px.scatter(
            filtered_df,
            x="program_duration_year",
            y="tuition_fee_usd_total",
            hover_data=["university_name", "program_name"],
            title="Tuition vs Duration",
        )
        st.plotly_chart(fig7, use_container_width=True)
with tab5:
    st.subheader("Search Programs")
    search_text = st.text_input("Search by Program or University Name")
    if search_text:
        result_df = filtered_df[
            filtered_df["program_name"].str.contains(search_text, case=False)
            | filtered_df["university_name"].str.contains(search_text, case=False)
        ]
    else:
        result_df = filtered_df

    st.dataframe(result_df.head(50))

    if not filtered_df.empty:
        st.download_button(
            label="💾 Download Filtered Data",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="filtered_programs.csv",
            mime="text/csv"
        )

    with st.expander("📂 See Full Filtered Dataset"):
        st.dataframe(filtered_df)

    if not filtered_df.empty:
        st.subheader("🔗 Top Program Links")
        top_programs = filtered_df.sort_values("tuition_fee_usd_total").head(10)
        for _, row in top_programs.iterrows():
            st.write(f"[{row['program_name']} - {row['university_name']}]({row['url']})")
with tab6:
    if not filtered_df.empty:
        st.subheader("University Spotlight")
        uni_choice = st.selectbox("Select a University", filtered_df["university_name"].unique())
        spotlight_df = filtered_df[filtered_df["university_name"] == uni_choice]
        st.dataframe(spotlight_df)
