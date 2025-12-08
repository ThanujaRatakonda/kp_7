import streamlit as st
import requests

API_URL = "http://backend:5000"
POD_NAME = os.getenv("HOSTNAME", "unknown")

st.title("Users Management Application")

st.write(f"### POD: {POD_NAME}")
with st.form("user_form"):
    name = st.text_input("Enter Name")
    email = st.text_input("Enter Email")
    submitted = st.form_submit_button("Add User")
    if submitted:
        if name and email:
            requests.post(f"{API_URL}/add", json={"name": name, "email": email})
            st.success("User added!")
        else:
            st.error("Please enter both name and email")

st.subheader("All Users")
users = requests.get(f"{API_URL}/users").json()
for u in users:
    st.write(f"{u['name']} - {u['email']}")
