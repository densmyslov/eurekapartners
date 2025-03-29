import streamlit as st
import pandas as pd
from PIL import Image
import base64
from io import BytesIO

# Load the image
image = Image.open("assets/eureka_logo.jpeg")

# Convert to base64
buffered = BytesIO()
image.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()

# Display logo + title
st.set_page_config(page_title="Eureka Partners Client Dashboard", layout="wide")
st.markdown(f"""
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{img_b64}" width="40" style="margin-right: 10px;">
        <h1 style="margin: 0;">Eureka Partners Client Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# Simulated values
current_balance = 20
token_price = 5.00
monthly_performance = [2, 5, 3, 7, 6, 9]




auth_col, balance_col, price_col = st.columns(3)

with auth_col:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        st.success("Logged in (placeholder)")

with balance_col:
    st.markdown("<h2 style='text-align: center'>Token Balance</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center'>{current_balance}</h3>", unsafe_allow_html=True)

with price_col:
    st.markdown("<h2 style='text-align: left'>Token Purchase</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: left'>Token Price: ${token_price:.2f}</h3>", unsafe_allow_html=True)
    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    token_to_buy = st.radio(
        "Buy tokens", [1, 3, 5, 10],
        horizontal=True,
        label_visibility="visible"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Center the button as well
    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    if st.button("Buy with Stripe"):
        st.info(f"Redirecting to Stripe for {token_to_buy} token(s)...")
    st.markdown("</div>", unsafe_allow_html=True)


# Credit Submission
st.header("📝 Forms")
st.markdown("**[Credit Submission Form (external link)](https://your-jotform-link.com)**")

if st.button("Submit Bank Introduction Form"):
    st.success("Token deducted. Email draft generated!")

# Upload Documents
st.header("📂 Upload Required Documents")
docs = ["EIN", "Articles", "ID", "Questionnaire"]
uploaded = {doc: st.file_uploader(f"Upload {doc}", type=["pdf", "jpg", "png"]) for doc in docs}

# Final Package Download
st.header("📥 Final Package")
if st.button("Download Final Combined PDF"):
    st.download_button("📄 Download PDF", b"Dummy PDF content", file_name="final_package.pdf")

# Request Token Back
st.header("⬅️ Token Return")
denial_letter = st.file_uploader("Upload Denial Letter", type=["pdf"])
if st.button("Request Token Back"):
    st.info("Token return requested!")

# Progress Tracker
st.header("📶 Client Progress")
steps = ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"]
progress = [0.2, 0.4, 0.6, 0.3, 0.8]
for s, p in zip(steps, progress):
    st.write(s)
    st.progress(p)

# Referral Tracker
st.header("👥 Referral Tracker")
st.metric("Clients Referred", 6)
st.metric("Fees Earned", "$1,250")
st.bar_chart(pd.DataFrame({
    "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "Referrals": monthly_performance
}).set_index("Month"))

# Calendly Links
st.header("📅 Calendly")
st.markdown("**[Schedule Onboarding Call](https://calendly.com/your-link)**")
