
import streamlit as st
import pandas as pd
import joblib
from pathlib import Path
from database import signup, login

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Credit Card Fraud Detection",
    page_icon="💳",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "fraud_count" not in st.session_state:
    st.session_state.fraud_count = 0

if "legitimate_count" not in st.session_state:
    st.session_state.legitimate_count = 0

# ---------------- PROFESSIONAL UI ----------------
st.markdown("""
<style>
.stApp {
    background-color: #F4F7FC;
}
[data-testid="stSidebar"] {
    background-color: #101C36;
}
[data-testid="stSidebar"] * {
    color: #FFFFFF;
}
h1, h2, h3 {
    color: #14213D !important;
    font-weight: 800;
}
p, label {
    color: #203354;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E1E8F0;
    padding: 16px;
    border-radius: 12px;
}
div.stButton > button,
div[data-testid="stFormSubmitButton"] button {
    background-color: #2457E6;
    color: white;
    border-radius: 9px;
    border: none;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD ML MODEL ----------------
MODEL_PATH = Path(__file__).parent / "credit_card_fraud_model.joblib"

model = None
model_error = None

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    model_error = str(e)

# ---------------- HEADER ----------------
st.title("💳 Smart Credit Card Fraud Detection")
st.caption("Machine Learning Based Transaction Risk Analysis")

# ==================================================
# LOGIN / SIGNUP
# ==================================================
if st.session_state.user is None:

    st.info("Please log in or create an account to continue.")

    login_tab, signup_tab = st.tabs(["🔐 Login", "📝 Create Account"])

    with login_tab:
        st.subheader("Welcome Back")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button(
                "Login", use_container_width=True
            )

        if login_submit:
            if not email.strip() or not password:
                st.warning("Please enter your email and password.")
            else:
                try:
                    user = login(email.strip(), password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with signup_tab:
        st.subheader("Create Your Account")

        with st.form("signup_form"):
            name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input(
                "Create Password", type="password"
            )
            confirm_password = st.text_input(
                "Confirm Password", type="password"
            )
            signup_submit = st.form_submit_button(
                "Sign Up", use_container_width=True
            )

        if signup_submit:
            if not name.strip() or not new_email.strip():
                st.warning("Please fill in your name and email.")
            elif not new_password:
                st.warning("Please enter a password.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    success, message = signup(
                        name.strip(), new_email.strip(), new_password
                    )
                    if success:
                        st.success(message + " You can now log in.")
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Signup failed: {e}")

# ==================================================
# AUTHENTICATED APPLICATION
# ==================================================
else:
    user = st.session_state.user

    # ---------------- SIDEBAR NAVIGATION ----------------
    with st.sidebar:
        st.title("💳 Smart Fraud")
        st.caption("Transaction Security")
        st.divider()

        page = st.radio(
            "NAVIGATION",
            [
                "🏠 Dashboard",
                "🛡️ Fraud Detection",
                "👤 My Profile"
            ],
            key="main_navigation"
        )

        st.divider()
        st.caption("Machine Learning Powered")
        st.caption(f"Signed in as {user['full_name']}")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # ---------------- DASHBOARD ----------------
    if page == "🏠 Dashboard":
        st.header("Dashboard")
        st.write(f"Welcome back, **{user['full_name']}**!")

        if model is not None:
            st.success("Machine learning model loaded.")
        else:
            st.error("The ML model could not be loaded.")
            st.code(model_error or "Unknown model error")
            st.info(
                "Ensure credit_card_fraud_model.joblib "
                "is in the same folder as app.py."
            )

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Transactions Checked",
            st.session_state.fraud_count
            + st.session_state.legitimate_count
        )
        c2.metric("Flagged as Fraud", st.session_state.fraud_count)
        c3.metric(
            "Classified Legitimate",
            st.session_state.legitimate_count
        )

        st.subheader("Quick Navigation")
        st.write("Use **Fraud Detection** in the sidebar to:")
        st.markdown(
            "- Analyze a single transaction\n"
            "- Analyze multiple transactions from a CSV file\n"
            "- View predictions and download results"
        )

        st.warning(
            "Educational demo only. Predictions are not proof of fraud "
            "and must not be used alone for real financial decisions."
        )

    # ---------------- FRAUD DETECTION ----------------
    elif page == "🛡️ Fraud Detection":
        st.header("Fraud Detection")

        if model is None:
            st.error("Model loading failed.")
            st.code(model_error or "Unknown model error")
            st.stop()

        st.success("Machine learning model is ready.")

        if hasattr(model, "feature_names_in_"):
            feature_names = list(model.feature_names_in_)
        else:
            feature_names = (
                ["Time"]
                + [f"V{i}" for i in range(1, 29)]
                + ["Amount"]
            )

        single_tab, batch_tab = st.tabs(
            ["Single Transaction", "Multiple Transactions (CSV)"]
        )

        # -------- SINGLE TRANSACTION --------
        with single_tab:
            st.subheader("Check a Single Transaction")
            st.info(
                "Enter sample model features. Do not enter actual card "
                "numbers, CVVs, PINs, passwords, or bank credentials."
            )

            with st.form("single_transaction_form"):
                values = {}
                col1, col2 = st.columns(2)

                for i, feature in enumerate(feature_names):
                    with (col1 if i % 2 == 0 else col2):
                        default = 100.0 if feature.lower() == "amount" else 0.0
                        values[feature] = st.number_input(
                            feature,
                            value=default,
                            format="%.6f",
                            key=f"single_{feature}"
                        )

                submitted = st.form_submit_button(
                    "🔍 Detect Fraud", use_container_width=True
                )

            if submitted:
                try:
                    input_df = pd.DataFrame(
                        [[values[f] for f in feature_names]],
                        columns=feature_names
                    )
                    prediction = int(model.predict(input_df)[0])

                    if prediction == 1:
                        st.error("⚠️ FRAUD: The model flagged this transaction.")
                        st.session_state.fraud_count += 1
                    else:
                        st.success(
                            "✅ LEGITIMATE: The model did not flag this transaction."
                        )
                        st.session_state.legitimate_count += 1

                    if hasattr(model, "predict_proba"):
                        probabilities = model.predict_proba(input_df)[0]
                        scores = {
                            str(label): round(float(prob), 4)
                            for label, prob in zip(model.classes_, probabilities)
                        }
                        st.subheader("Model Probability Scores")
                        st.json(scores)

                    st.caption(
                        "This is a model prediction, not a guarantee "
                        "that a transaction is safe or fraudulent."
                    )

                except Exception as e:
                    st.error(f"Prediction failed: {e}")

        # -------- BATCH CSV TRANSACTIONS --------
        with batch_tab:
            st.subheader("Analyze Multiple Transactions")
            st.write(
                "Upload a CSV containing all required model feature columns."
            )
            st.caption("Required columns: " + ", ".join(feature_names))

            uploaded_file = st.file_uploader(
                "Choose a CSV file",
                type=["csv"],
                key="batch_csv"
            )

            if uploaded_file is not None:
                try:
                    data = pd.read_csv(uploaded_file)
                    st.write("CSV Preview")
                    st.dataframe(data.head(10), use_container_width=True)

                    missing = [
                        f for f in feature_names if f not in data.columns
                    ]

                    if missing:
                        st.error(
                            "Missing required columns: " + ", ".join(missing)
                        )
                    elif data.empty:
                        st.warning("The CSV contains no transactions.")
                    else:
                        if st.button(
                            "🔍 Analyze All Transactions",
                            use_container_width=True
                        ):
                            features = data[feature_names].copy()

                            for feature in feature_names:
                                features[feature] = pd.to_numeric(
                                    features[feature], errors="coerce"
                                )

                            if features.isnull().any().any():
                                st.error(
                                    "Some required values are empty or "
                                    "non-numeric. Please fix the CSV."
                                )
                            else:
                                predictions = model.predict(features)
                                results = data.copy()
                                results["Fraud_Prediction"] = [
                                    "Fraud" if int(p) == 1 else "Legitimate"
                                    for p in predictions
                                ]

                                st.subheader("Detection Results")
                                st.dataframe(
                                    results, use_container_width=True
                                )

                                fraud_count = sum(
                                    int(p) == 1 for p in predictions
                                )
                                legitimate_count = (
                                    len(predictions) - fraud_count
                                )

                                a, b, c = st.columns(3)
                                a.metric("Analyzed", len(results))
                                b.metric("Flagged as Fraud", fraud_count)
                                c.metric(
                                    "Classified Legitimate", legitimate_count
                                )

                                csv_data = results.to_csv(
                                    index=False
                                ).encode("utf-8")

                                st.download_button(
                                    "⬇️ Download Results CSV",
                                    data=csv_data,
                                    file_name="fraud_detection_results.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )

                except Exception as e:
                    st.error(f"Could not process CSV: {e}")

    # ---------------- MY PROFILE ----------------
    elif page == "👤 My Profile":
        st.header("My Profile")
        st.write("### Account Information")

        st.text_input(
            "Full Name",
            value=user["full_name"],
            disabled=True
        )
        st.text_input(
            "Email",
            value=user["email"],
            disabled=True
        )

        st.info(
            "This is a demonstration application. "
            "Never enter real bank credentials, PINs, or CVVs."
        )

# ---------------- FOOTER ----------------
st.divider()
st.caption(
    "Smart Credit Card Fraud Detection • Academic ML Project • Demo only"
)
