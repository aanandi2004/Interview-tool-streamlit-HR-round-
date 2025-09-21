'''from openai import OpenAI
import openai
import streamlit as st

st.set_page_config(page_title='Stream lit',page_icon =' 💬')
st.title('Chatbot')

openai.api_key = st.secrets["OPENAI_API_KEY"]
openai.api_base = st.secrets["OPENAI_BASE_URL"] 

client = openai


if "openai_model" not in st.session_state:
    st.session_state['openai_model'] = "openai/chatgpt-4o-latest"

if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt := st.chat_input("your answer : "):
    st.session_state.messages.append({'role': "user",'content': prompt})
    with st.chat_message("user"):
        st.markdown(prompt)


    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model = st.session_state["openai_model"],
            messages=[
                {'role': m['role'],'content': m['content']}
                for m in st.session_state.messages
            ],
            stream = True,
        
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({'role': "assistant",'content': response})
'''
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

# OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


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
            "Choose Level",
            options=["junior", "mid-level", "senior"],
            index=["junior", "mid-level", "senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a Position",
            ["data scientist", "data engineer", "ml engineer", "bi analyst", "financial analyst"],
            index=0
        )
        st.session_state["company"] = st.selectbox(
            "Choose a Company",
            ["amazon", "meta", "udemy", "365", "nestle", "linkedin", "spotify"],
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
You are an HR executive that interviews an interviewee called {st.session_state['name']}
with the experience {st.session_state['experience']} and skills {st.session_state['skills']}.
You should interview them for the position {st.session_state['level']} {st.session_state['position']}
at the company {st.session_state['company']}.
"""
            }
        ]

    # Display chat history
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input (only while under 5 turns)
    if st.session_state.user_msg_count < 5:
        if prompt := st.chat_input("Your message:", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # OpenAI API call
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=500,
                messages=st.session_state.messages
            )

            assistant_reply = response.choices[0].message.content
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)

            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            st.session_state.user_msg_count += 1

    # End chat after 5 turns
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

    # Keep only last 10 messages to avoid token overload
    trimmed_history = st.session_state.messages[-10:]
    conversation_history = "\n".join(
        [f"Role: {msg['role']}, Content: {msg['content']}" for msg in trimmed_history]
    )

    try:
        feedback_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful tool that provides feedback on an interviewee's performance.
Before the feedback give a score of 1 to 10.
Follow this format:
Overall Score: //Your score
Feedback: //Here you put your feedback
Give only the feedback do not ask any additional questions.
"""
                },
                {
                    "role": "user",
                    "content": f"""This is the interview you need to evaluate. 
The Interview is as follows:

{conversation_history}
"""
                }
            ]
        )

        st.write(feedback_completion.choices[0].message.content)

    except Exception as e:
        st.error(f"⚠️ Error while fetching feedback: {e}")
    if st.button("restart interview",type ='primary'):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
