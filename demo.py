import streamlit as st
import pandas as pd

df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'Age': [25, 30, 35, 28],
    'City': ['New York', 'London', 'Tokyo', 'Paris']
})

st.title("Simple Clickable Rows")

if 'selected_row' not in st.session_state:
    st.session_state.selected_row = None

# Display dataframe with select buttons
for i, row in df.iterrows():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"**{row['Name']}** - {row['Age']} - {row['City']}")
    with col2:
        if st.button("Select", key=f"btn_{i}"):
            st.session_state.selected_row = row

# Input fields
if st.session_state.selected_row is not None:
    st.text_input("Name", value=st.session_state.selected_row['Name'])
    st.text_input("Age", value=str(st.session_state.selected_row['Age']))
    st.text_input("City", value=st.session_state.selected_row['City'])