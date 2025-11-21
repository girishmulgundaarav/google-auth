import streamlit as st

# Page setup
st.set_page_config(
    page_title="Secure App",
    page_icon="🔒",
    layout="centered"
)

def login_screen():
    st.title("🔒 Private App")
    st.write("Access is restricted. Please log in with your Google account to continue.")

    # Use columns to center the button
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("Log in with Google", on_click=st.login)

    # Helpful info
    with st.expander("Why do I need to log in?"):
        st.info("Logging in ensures secure access and personalized features.")

def welcome_screen():
    st.success(f"👋 Welcome, {st.user.name}!")
    st.write("You are now securely logged in. Explore your app below:")

    # Example dashboard layout
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "⚙️ Settings", "👤 Profile"])

    with tab1:
        st.metric("Active Sessions", 12)
        st.metric("Tasks Completed", 34)

    with tab2:
        st.write("Settings go here...")
        st.checkbox("Enable notifications")
        st.slider("Volume", 0, 100, 50)

    with tab3:
        st.write("Profile details")
        st.write(f"Name: {st.user.name}")
        st.button("Log out", on_click=st.logout)

# Main flow
if not st.user.is_logged_in:
    login_screen()
else:
    welcome_screen()