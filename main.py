import streamlit as st
from login import login_page
from scanner import main_page

if __name__ == "__main__":
    st.set_page_config(page_title="Barcode/QR")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'next_page' not in st.session_state:
        st.session_state.next_page = False

    if not st.session_state.logged_in:
        login_page()
    else:
        main_page()
