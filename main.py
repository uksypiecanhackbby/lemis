import streamlit as st
import google.generativeai as genai
import json
import requests
import base64
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat()

st.set_page_config(
    page_title="Dr. Lucie",
    page_icon="👩‍⚕️",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "This is a medical chatbot integrated with Gemini AI."
    }
)

def format_address(address):
    parts = address.split(",")
    
    if len(parts) > 1:
        return ", ".join(parts[1:]).strip()
    return address

def initializeAI():
    with open('draft2.json', 'r') as file:
        data = json.load(file)

    data_str = json.dumps(data)
    initialPrompt = """
    Your name is Dr Lucie and you are a medical assistant chatbot in Saint Lucia. Your role is to be a helpful and compassionate chatbot responding to messages from the user about St Lucia medical services. Do not mention that the information was provided to you in previous messages.

    Your response should be in json format with 2 keys: a response key and a quit key. The value to the response key should be the response to the user's prompt and the value for the quit key should be the response if the user want to end the conversation. Here is an example of how I want your response to be to the prompt 'What is good morning in spanish?'. {'response': 'Good morning in spanish is buenos dias', 'quit': false}"""

    chat.send_message(initialPrompt)
    chat.send_message(data_str)

initializeAI()
st.title("Dr Lucie -St Lucia's Medical Assistant")
dr_avatar = "👩‍⚕️"
user_avatar="👨"

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
    return encoded_image

image_path = "grey_heart.png"
base64_image = get_base64_image(image_path)

st.markdown(
    f"""
    <style>
    .main {{
        position: relative;
        background-image: url('data:image/jpeg;base64,{base64_image}');
        background-size: cover 600px;
        background-position: center;
        background-repeat: no-repeat;
    }}
    .main::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.3); /* White overlay with 50% opacity */
        z-index: -1;
    }}

   .stTextInput, .stButton, .stMarkdown , .stChatMessage{{
        font-size: 54px;
    }}

    .block-container {{
        max-width: 800px;
        margin: auto; 
    }}

      div[data-testid="InputInstructions"] > span:nth-child(1) {{
    visibility: hidden;
}}

    </style>
    """,
    unsafe_allow_html=True
)



def get_location_info(location_name):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_name}&components=country:LC&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        
        # Check if results were returned
        if data['results']:
            location_info = data['results'][0]['formatted_address']
            lat = data['results'][0]['geometry']['location']['lat']
            lng = data['results'][0]['geometry']['location']['lng']
            maps_url = f"https://www.google.com/maps/?q={lat},{lng}"
            formatted_address = format_address(location_info)
            
            return f"Location found: {formatted_address}. [View on Google Maps]({maps_url})"
        else:
            return "Sorry, I couldn't find the location in Saint Lucia."
    else:
        return "There was an error retrieving the location."

    
if 'messages' not in st.session_state:
    st.session_state.messages = []

    initial_message = ("Hello! I'm Dr. Lucie, your medical assistant chatbot for St Lucia. "
                       "I can help you find pricing information for medical procedures, "
                       " and details about healthcare facilities in St Lucia. "
                       "How can I assist you today?")
    st.session_state.messages.append({"role": "assistant", "content": initial_message})


# Process input when the button is clicked or when the input field is submitted
def process_input():
    user_input = st.session_state.user_input

    if user_input:
        # Add user message to the conversation
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Check if the user input is a location-related query
        if "where" in user_input.lower() or "location" in user_input.lower() or "find" in user_input.lower():
            location_info = get_location_info(user_input)
            map = {"response": location_info, "quit": False}
        else:
            # Generate the response for non-location queries
            response = chat.send_message(user_input)
            reply = response.text

            # Extract the JSON response from the reply
            start = reply.find('{')
            end = reply.rfind('}') + 1
            map = json.loads(reply[start:end])
        quit_chat = map['quit']

        # Add assistant reply to the conversation
        st.session_state.messages.append({"role": "assistant", "content": map['response']})

        # Clear the input field after submission
        st.session_state.user_input = ""

        # If quit is true, end the conversation
        if quit_chat:
            st.write("Exiting the chat. Goodbye!")
            st.stop()

# Display chat history
for message in st.session_state.messages:
    if message['role'] == 'user':
        with st.chat_message(name="You", avatar=user_avatar):
            st.write(message['content'])
    else:
        # Use st.chat_message for chatbot messages
        with st.chat_message(name="assistant", avatar=dr_avatar):
            st.write(message['content'])

# Input field and button
user_input = st.text_input("Enter your message:", key='user_input', value="")
send_button = st.button("Send", on_click=process_input)
