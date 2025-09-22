import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

# ----------------------------
# Streamlit Page Config
# ----------------------------
st.set_page_config(page_title="Chatbot", page_icon="💬")
st.title("Chatbot")

# ----------------------------
# Initialize Session State
# ----------------------------
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_msg_count" not in st.session_state:
    st.session_state.user_msg_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

# ----------------------------
# OpenRouter / OpenAI client
# ----------------------------
client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"],
    base_url=st.secrets["OPENROUTER_BASE_URL"]  # ✅ correct
)


# ----------------------------
# Helper Functions
# ----------------------------
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# ----------------------------
# Step 1: Personal Information + Job Setup
# ----------------------------
if not st.session_state.setup_complete:
    st.subheader("Personal Information", divider="rainbow")

    # Initialize session state variables
    for key in ["name", "experience", "skills"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    # Input fields
    st.session_state["name"] = st.text_input(
        label="Name",
        value=st.session_state["name"],
        max_chars=40,
        placeholder="Enter your name"
    )
    st.session_state["experience"] = st.text_area(
        label="Experience",
        value=st.session_state["experience"],
        max_chars=200,
        placeholder="Your experience"
    )
    st.session_state["skills"] = st.text_area(
        label="Skills",
        value=st.session_state["skills"],
        max_chars=200,
        placeholder="Your skills"
    )

    st.write(f"Your Name: {st.session_state['name']}")
    st.write(f"Your Experience: {st.session_state['experience']}")
    st.write(f"Your Skills: {st.session_state['skills']}")

    st.subheader("Company and Position", divider="rainbow")

    # Defaults
    if "level" not in st.session_state:
        st.session_state["level"] = "junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "data scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "amazon"

    col1, col2 = st.columns(2)

    with col1:
        st.session_state["level"] = st.radio(
            "Choose Level",
            options=["junior", "mid-level", "senior"],
            index=["junior","mid-level","senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a Position",
            ["data scientist", "data engineer", "ml engineer", "bi analyst", "financial analyst"],
            index=0
        )
        st.session_state["company"] = st.selectbox(
            "Choose a Company",
            ["amazon","meta","udemy","365","nestle","linkedin","spotify"],
            index=0
        )

    st.write(
        f"Your Information: {st.session_state['level']} "
        f"{st.session_state['position']} at {st.session_state['company']}"
    )

    if st.button("Start Interview", on_click=complete_setup):
        st.success("Setup complete. Starting interview...")

# ----------------------------
# Step 2: Interview Session
# ----------------------------
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    st.info("Start by introducing yourself")

    # Initialize system prompt
    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": f"""
You are an HR executive interviewing {st.session_state['name']} 
with experience {st.session_state['experience']} and skills {st.session_state['skills']}. 
Interview for the position {st.session_state['level']} {st.session_state['position']} 
at {st.session_state['company']}.
"""
            }
        ]

    # Display chat history
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input (up to 5 messages)
    if st.session_state.user_msg_count < 5:
        if prompt := st.chat_input("Your message:", max_chars=1000):
            st.session_state.messages.append({"role":"user", "content":prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                max_tokens=500
            )

            assistant_reply = response.choices[0].message.content
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)

            st.session_state.messages.append({"role":"assistant", "content":assistant_reply})
            st.session_state.user_msg_count += 1

    # End chat after 5 messages
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

    # Trim history to last 10 messages to avoid token issues
    trimmed_history = st.session_state.messages[-10:]
    conversation_history = "\n".join(
        [f"Role: {m['role']}, Content: {m['content']}" for m in trimmed_history]
    )

    try:
        feedback_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a tool that provides feedback on an interviewee's performance.
Give a score 1-10 first, then detailed feedback.
Format:
Overall Score: //score
Feedback: //detailed feedback
Only provide feedback, no additional questions.
"""
                },
                {
                    "role": "user",
                    "content": f"The interview is:\n{conversation_history}"
                }
            ],
            max_tokens=500
        )
        st.write(feedback_completion.choices[0].message.content)

    except Exception as e:
        st.error(f"⚠️ Error while fetching feedback: {e}")

    # Restart Interview button
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
