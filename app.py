import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import datetime

from streamlit_lottie import st_lottie
import requests
from pandas.api.types import CategoricalDtype

EMPTY_SPACE = "##"
DATA_PATH = "data/push-ups.csv"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


sub_heading = f"""I set a challenge of doing **10k push-ups** as my new year's resolution for 2021. 
This works out to roughly 30 a day

I used the [Streaks app](https://streaksapp.com/) to remind me to do them daily. 
One of the nice things about the app is that you can set how many times a day you want to do a task.
This made it easy for me to do and track more push-ups in blocks of 30

I kept track of my progress in a spreadhseet. Below is some analysis on the numbers
"""


def load_lottie(url: str) -> dict:
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    drop_cols = [c for c in df.columns if c.startswith("Unnamed:")]
    df = df.drop(columns=drop_cols)

    # filter rows for just days of the month
    df = df.iloc[:31]
    df.index = range(1, 32)
    df = df.rename(columns=dict(zip(df.columns, MONTHS)))
    return df


def as_time_series(df: pd.DataFrame) -> pd.Series:
    """convert day x month dataframe into 1d time series"""

    def to_datetime(day_month: tuple, year: int = 2021) -> datetime:
        day, month = day_month
        return pd.to_datetime(f"{day}/{month}/{year}", format="%d/%B/%Y")

    stacked = df.stack()
    stacked.index = pd.Series(stacked.index.tolist()).apply(to_datetime)
    return stacked.sort_index()  # ensure series is sorted in calendar order


def main():
    # load data
    df = load_data(DATA_PATH).dropna(how="all", axis=1)
    ts = as_time_series(df)
    
    # header - title and intro
    url = "https://assets10.lottiefiles.com/packages/lf20_zm1z76.json"
    lottie_logo = load_lottie(url)
    st_lottie(lottie_logo, height=250)

    st.title("New Year's Resolution 2021")
    st.subheader("by Micah Paul")
    st.markdown(sub_heading)
    st.markdown(EMPTY_SPACE)
    st.subheader(f"Total push-ups this year: {df.sum().sum():.0f}")
    st.write("---")
    
    # body - charts and insights
    pushups_per_month = df.sum()
    fig = px.bar(
        pushups_per_month,
        title="push-ups per month".title(),
        labels={"index": "Month", "value": "Total"},
    )
    fig.add_hline(
        y=pushups_per_month.mean(), 
        line_width=1, 
        line_dash="dash", 
        annotation_text="Mean", 
        line=dict(color="red")
        )
    st.plotly_chart(fig)
    desc = f"""On average I did {pushups_per_month.mean(): .0f} push-ups per month. 
    **My best month was {pushups_per_month.idxmax()} with {pushups_per_month.max(): .0f} total push-ups**. 
    On the other end, in {pushups_per_month.idxmin()} I did just {pushups_per_month.min(): .0f} push-ups.
    Thats a difference of {pushups_per_month.max() - pushups_per_month.min(): .0f} push-ups, actually more than my average"""
    st.write(desc)
    
    pushuper_per_month_day = df.sum(axis=1)
    fig = px.bar(
        pushuper_per_month_day,
        title="push-ups per day of the month".title(),
        labels={"index": "Date", "value": "Total"},
    )
    fig.add_hline(
        y=pushuper_per_month_day.mean(), 
        line_width=1, 
        line_dash="dash", 
        annotation_text="Mean", 
        line=dict(color="red")
        )
    st.plotly_chart(fig)
    desc = f"""Understandably the 31st has the lowest number of total push-ups because there are 5 months missing this date. 
    The rest of the dates are roughly similar and hover around the mean of {pushuper_per_month_day.mean(): .0f} push-ups.
    **On {ts.idxmax().strftime("%A, %dth of %B")} I did the most push-ups in a single day, {ts.max(): .0f}** 🎉. 
    This was definatley an outlier and is the primary reason why this particular date is so high
    """
    desc += f"""\nlooking at the numbers by day of the week, there isnt much difference day to day. 
    {ts.idxmax().strftime("%A")} has the highest total, likely bolstered by my highest day of the year."""
    st.write(desc)
    
    
    progress = ts.to_frame().rename(columns={0: "Actual"})
    progress["Expected"] = 30.0
    progress = progress.cumsum()
    fig = px.line(
        progress,
        title="cumulative progress".title(),
        labels={"value": "Cumulative sum", "index": "Month"}
    )
    fig.add_hline(y=10000, line_width=1, line_dash="dash", annotation_text="Goal", line=dict(color="green"), annotation_position="bottom right")
    st.plotly_chart(fig)

    csum = ts.cumsum()
    goal_date = csum[csum > 10000].idxmin().strftime('%B %-dth')
    desc = f"""
    **I reached my goal of 10k push-ups on {goal_date}** 🎉\n
    Well ahead of schedule! You can see a small step increase at the end of Feburary when I did the most push-ups in a single day.
    But the biggest uptick happens from June to July when I did a higher number of daily push-ups than normal
    
    To reach my goal by the end of the year, I needed to do {10000 / 365: .2f} push-ups a day on average, but on average I did {ts.dropna().mean(): .2f}
    
    After reaching my goal I reduced my daily push-ups down to 30 for the first half of the next month (because doing 90 push-ups a day for a month straight is tough)
    You can also see that after i hit my goal, there is more variation in the speed of my progress. 
    I alternated mostly between 30 or 60 push-ups throughout the month based on how my body was feeling
    """
    st.write(desc)
    
    ts = as_time_series(df).to_frame().rename(columns={0: "pushups"})

    after_goal_mask = ts.index > "2021-08-06"
    ts["after_goal"] = False
    ts.loc[after_goal_mask, "after_goal"] = True
    
    fig = px.violin(ts, y="pushups", x="after_goal", color="after_goal", labels={"after_goal": "After Goal", "pushups": "Push-ups"})
    st.plotly_chart(fig)
    st.write("---")
    
    # footer - raw data
    st.header("raw data".title())
    
    df.columns = [c[0] for c in df.columns]
    
    fig, ax = plt.subplots(figsize=(12,12))
    ax = sns.heatmap(df, ax=ax, cbar=False, annot=True, cmap="Blues", fmt='g', linewidth=1, linecolor="black")
    plt.tick_params(axis='both', which='major', labeltop=True, labelbottom=False, bottom=False, left=False)
    for _, spine in ax.spines.items():
        spine.set_visible(True)
        
    plt.tick_params(axis='both', which='major', labeltop=True, labelbottom=False, bottom=False, left=False)
    plt.yticks(rotation = 0)
    st.pyplot(fig)
    


if __name__ == "__main__":
    main()