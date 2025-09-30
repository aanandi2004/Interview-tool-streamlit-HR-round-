import streamlit as st
from openai import OpenAI

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="HR Interview Assistant", page_icon="💼", layout="wide")
st.title("💬 AI-Powered HR Interview Tool")

# ----------------------------
# Load OpenRouter API secrets from Streamlit
# ----------------------------
api_key = st.secrets["OPENROUTER_API_KEY"]
base_url = st.secrets["OPENROUTER_BASE_URL"]

# ✅ Initialize OpenAI client with OpenRouter
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# ----------------------------
# Session State Initialization
# ----------------------------
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_msg_count" not in st.session_state:
    st.session_state.user_msg_count = 0
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []


# ----------------------------
# Helper Functions
# ----------------------------
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True


# ----------------------------
# Step 1: Personal Info & Job Setup
# ----------------------------
if not st.session_state.setup_complete:
    st.subheader("Personal Information", divider="rainbow")
    
    # Initialize session state variables
    for key in ["name", "experience", "skills"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    st.session_state["name"] = st.text_input(
        "Name", value=st.session_state["name"], max_chars=40, placeholder="Enter your name"
    )
    st.session_state["experience"] = st.text_area(
        "Experience", value=st.session_state["experience"], max_chars=200, placeholder="Your experience"
    )
    st.session_state["skills"] = st.text_area(
        "Skills", value=st.session_state["skills"], max_chars=200, placeholder="Your skills"
    )

    st.subheader("Company and Position", divider="rainbow")
    
    # Initialize defaults
    if "level" not in st.session_state:
        st.session_state["level"] = "junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "data scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "amazon"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose Level", options=["junior", "mid-level", "senior"],
            index=["junior", "mid-level", "senior"].index(st.session_state["level"])
        )
    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a Position",
            ["data scientist", "data engineer", "ml engineer", "bi analyst", "financial analyst"]
        )
        st.session_state["company"] = st.selectbox(
            "Choose a Company",
            ["amazon", "meta", "udemy", "365", "nestle", "linkedin", "spotify"]
        )

    st.write(f"Your Information: {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}")

    if st.button("Start Interview", on_click=complete_setup):
        st.success("Setup complete. Starting interview...")


# ----------------------------
# Step 2: Interview / Chat
# ----------------------------
if st.session_state.setup_complete and not st.session_state.chat_complete:
    st.info("Start by introducing yourself.")

    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": f"""
You are an HR executive that interviews an interviewee called {st.session_state['name']}.
Experience: {st.session_state['experience']}.
Skills: {st.session_state['skills']}.
Interview for position: {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}.
"""
            }
        ]

    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # User input (max 5 turns)
    if st.session_state.user_msg_count < 5:
        if user_input := st.chat_input("Your message:"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            try:
                response = client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=st.session_state.messages,
                    max_tokens=500
                )
                assistant_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                with st.chat_message("assistant"):
                    st.markdown(assistant_reply)
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")

            st.session_state.user_msg_count += 1

    if st.session_state.user_msg_count >= 5:
        st.session_state.chat_complete = True
        st.success("Interview complete. Click below to see feedback.")
        if st.button("Get Feedback", on_click=show_feedback):
            st.session_state.feedback_shown = True


# ----------------------------
# Step 3: Feedback
# ----------------------------
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    # Use last 10 messages to avoid token overload
    trimmed_history = st.session_state.messages[-10:]
    conversation_history = "\n".join([f"{m['role']}: {m['content']}" for m in trimmed_history])

    try:
        feedback_completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You are a helpful tool that provides feedback on an interviewee's performance.
Give a score (1-10) and feedback.
Format:
Overall Score: //
Feedback: //
Do not ask questions.
"""
                },
                {"role": "user", "content": f"Evaluate this interview:\n{conversation_history}"}
            ],
            max_tokens=500
        )
        st.write(feedback_completion.choices[0].message.content)
    except Exception as e:
        st.error(f"⚠️ Error while fetching feedback: {e}")
