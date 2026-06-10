import streamlit as st
import json
import re
from google import genai

# Page Configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. State Management
if "user_text" not in st.session_state:
    st.session_state.user_text = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "explanation" not in st.session_state:
    st.session_state.explanation = ""
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "flashcard_reveal" not in st.session_state:
    st.session_state.flashcard_reveal = False

# Initialize Gemini Client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def ask_ai(prompt, is_json=False):
    config = {}
    if is_json:
        config["response_mime_type"] = "application/json"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        return response.text
    except Exception as e:
        st.error(f"Gemini API Error: {str(e)}")
        return None

# 2. Modern UI Styles & Typography Injections
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap');
    
    /* Global style overrides */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    /* App Title Gradient styling */
    .app-title-container {
        padding: 0.5rem 0;
        margin-bottom: 1.5rem;
    }
    .app-title {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.05em;
        margin: 0;
    }
    .app-subtitle {
        color: var(--text-color);
        opacity: 0.8;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Study Card styling */
    .study-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.1);
        padding: 28px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
        color: var(--text-color);
    }
    
    /* Gradient backgrounds for specific cards */
    .accent-card {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%);
        border-left: 5px solid #7c3aed;
    }
    
    /* Flashcard Widget Container */
    .flashcard-outer {
        margin: 20px auto;
        width: 100%;
        max-width: 550px;
    }
    .flashcard-inner {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        padding: 40px 30px;
        border-radius: 20px;
        min-height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 15px 35px rgba(79, 70, 229, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    .flashcard-inner.reveal {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        box-shadow: 0 15px 35px rgba(16, 185, 129, 0.3);
    }
    .flashcard-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .flashcard-text {
        font-size: 1.4rem;
        font-weight: 500;
        line-height: 1.6;
    }
    
    /* Navigation Sidebar styling */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.1);
        background-color: var(--secondary-background-color);
    }
    .sidebar-title {
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Custom buttons override */
    div.stButton > button {
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 15px;
        width: 100%;
        transition: all 0.2s ease-in-out;
    }
    
    /* Results formatting custom styling */
    .markdown-box {
        line-height: 1.7;
    }
    .markdown-box li {
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Navigation Menu
with st.sidebar:
    st.markdown('<div class="sidebar-title">📚 StudyGenius</div>', unsafe_allow_html=True)
    st.write("Your premium AI study companion.")
    st.divider()
    
    # Navigation option using radio button
    selected_page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard & Input",
            "📝 Smart Summarizer",
            "💡 Concept Explainer",
            "❓ Interactive Quiz",
            "🃏 Active Flashcards"
        ],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.write("### Study Status")
    # Quick indicator checks for active generations
    def status_badge(condition):
        return "✅ Ready" if condition else "❌ Not Generated"
        
    st.markdown(f"""
    * **Notes Entered:** {"✅ Yes" if st.session_state.user_text.strip() else "❌ No"}
    * **Summary:** {status_badge(st.session_state.summary)}
    * **Explanation:** {status_badge(st.session_state.explanation)}
    * **Interactive Quiz:** {status_badge(st.session_state.quiz)}
    * **Flashcards Deck:** {status_badge(st.session_state.flashcards)}
    """)
    
    if st.session_state.user_text.strip():
        if st.button("🧹 Clear All Data"):
            st.session_state.user_text = ""
            st.session_state.summary = ""
            st.session_state.explanation = ""
            st.session_state.quiz = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.flashcards = None
            st.session_state.flashcard_index = 0
            st.session_state.flashcard_reveal = False
            st.rerun()

# 4. Main Page Header
st.markdown('<div class="app-title-container"><h1 class="app-title">StudyGenius</h1></div>', unsafe_allow_html=True)

# Helper function to check if notes exist
def verify_notes_present():
    if not st.session_state.user_text.strip():
        st.warning("⚠️ No study notes or topic entered yet! Please go back to the **🏠 Dashboard & Input** page to provide content.")
        return False
    return True

# 5. Page Implementations
if selected_page == "🏠 Dashboard & Input":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📚 Enter Your Topic or Study Notes")
        st.write("Paste your textbook chapters, lecture notes, or just type a concept you want to learn.")
        
        # Track text input directly in session state
        user_input = st.text_area(
            "Study Input Area",
            value=st.session_state.user_text,
            height=300,
            placeholder="e.g. What is Operating System? Or paste detailed computer architecture notes here...",
            label_visibility="collapsed"
        )
        
        if user_input != st.session_state.user_text:
            st.session_state.user_text = user_input
            # Reset generated states if text changes
            st.session_state.summary = ""
            st.session_state.explanation = ""
            st.session_state.quiz = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.flashcards = None
            st.session_state.flashcard_index = 0
            st.session_state.flashcard_reveal = False
            
    with col2:
        st.markdown("""
        <div class="study-card accent-card">
            <h3>🚀 Welcome to StudyGenius</h3>
            <p>Paste notes in the text area, then select any study tool from the sidebar navigation:</p>
            <ul>
                <li><strong>Summarizer:</strong> Get bullet-point takeaways.</li>
                <li><strong>Explainer:</strong> Understand complex ideas simply.</li>
                <li><strong>Interactive Quiz:</strong> Test your knowledge!</li>
                <li><strong>Flashcards:</strong> Practice active recall.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.user_text.strip():
            st.success("📝 Notes saved! Choose a tool from the sidebar to start studying.")
        else:
            st.info("💡 Enter some text on the left to activate the study tools.")

elif selected_page == "📝 Smart Summarizer":
    if verify_notes_present():
        st.subheader("📝 Smart Summarizer")
        st.write("Get a clear, concise summary of your material, broken down into readable bullet points.")
        
        if not st.session_state.summary:
            if st.button("✨ Generate Summary", type="primary"):
                with st.spinner("Analyzing and summarizing notes..."):
                    result = ask_ai(f"Summarize this in clear, simple bullet points with bold keywords:\n{st.session_state.user_text}")
                    if result:
                        st.session_state.summary = result
                        st.rerun()
        else:
            st.markdown(f'<div class="study-card markdown-box">{st.session_state.summary}</div>', unsafe_allow_html=True)
            if st.button("🔄 Regenerate Summary"):
                st.session_state.summary = ""
                st.rerun()

elif selected_page == "💡 Concept Explainer":
    if verify_notes_present():
        st.subheader("💡 Concept Explainer")
        st.write("Understand complicated concepts explained in plain English, with real-world analogies.")
        
        if not st.session_state.explanation:
            if st.button("✨ Generate Simple Explanation", type="primary"):
                with st.spinner("Breaking down complex ideas..."):
                    prompt = (
                        f"Explain this topic in simple terms (as if explaining to a beginner/student), "
                        f"using real-world analogies. Use clear headings and keep it around 150-300 words:\n"
                        f"{st.session_state.user_text}"
                    )
                    result = ask_ai(prompt)
                    if result:
                        st.session_state.explanation = result
                        st.rerun()
        else:
            st.markdown(f'<div class="study-card markdown-box">{st.session_state.explanation}</div>', unsafe_allow_html=True)
            if st.button("🔄 Regenerate Explanation"):
                st.session_state.explanation = ""
                st.rerun()

elif selected_page == "❓ Interactive Quiz":
    if verify_notes_present():
        st.subheader("❓ Interactive Quiz")
        st.write("Challenge yourself with multiple-choice questions dynamically generated from your notes.")
        
        if st.session_state.quiz is None:
            if st.button("✨ Generate Quiz", type="primary"):
                with st.spinner("Generating 5 interactive multiple-choice questions..."):
                    prompt = f"""
                    Generate exactly 5 multiple-choice quiz questions based on this study content.
                    Return the response as a raw JSON array of objects.
                    Each object MUST have:
                    - "question": string
                    - "options": list of 4 strings
                    - "correct_index": integer (0, 1, 2, or 3)
                    - "explanation": string explaining the correct answer
                    
                    Do NOT wrap the output in markdown code blocks. Just output raw valid JSON.
                    Content:
                    {st.session_state.user_text}
                    """
                    result = ask_ai(prompt, is_json=True)
                    if result:
                        try:
                            # Clean up markdown code blocks if the model returned them anyway
                            cleaned_result = result.strip()
                            if cleaned_result.startswith("```"):
                                match = re.search(r"```(?:json)?\s*(.*?)```", cleaned_result, re.DOTALL)
                                if match:
                                    cleaned_result = match.group(1)
                            
                            quiz_data = json.loads(cleaned_result)
                            st.session_state.quiz = quiz_data
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_submitted = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing quiz JSON. Please try again. Details: {e}")
                            st.code(result)
        else:
            # Quiz is loaded!
            quiz = st.session_state.quiz
            
            # Form to prevent reruns on every radio button click
            with st.form("quiz_form"):
                for idx, item in enumerate(quiz):
                    st.markdown(f"**Question {idx + 1}:** {item['question']}")
                    
                    # Store selected answer index
                    default_sel = st.session_state.quiz_answers.get(idx, None)
                    # Use radio buttons for option selection
                    selected_val = st.radio(
                        f"Select option for question {idx + 1}",
                        item["options"],
                        index=item["options"].index(default_sel) if default_sel in item["options"] else None,
                        key=f"q_{idx}",
                        label_visibility="collapsed"
                    )
                    
                    if selected_val:
                        st.session_state.quiz_answers[idx] = selected_val
                    
                    st.write("") # Spacer
                
                # Render quiz control buttons
                submitted = st.form_submit_button("Submit Answers")
                if submitted:
                    st.session_state.quiz_submitted = True
                    st.rerun()
            
            # Post-submission analysis
            if st.session_state.quiz_submitted:
                st.divider()
                st.subheader("📊 Quiz Results")
                
                correct_count = 0
                for idx, item in enumerate(quiz):
                    correct_opt = item["options"][item["correct_index"]]
                    user_opt = st.session_state.quiz_answers.get(idx, None)
                    
                    st.markdown(f"**Question {idx + 1}:** {item['question']}")
                    st.write(f"Your answer: `{user_opt or 'Unanswered'}`")
                    
                    if user_opt == correct_opt:
                        correct_count += 1
                        st.success(f"✅ Correct! The answer is: **{correct_opt}**")
                    else:
                        st.error(f"❌ Incorrect. Correct answer: **{correct_opt}**")
                    
                    st.info(f"💡 *Explanation:* {item['explanation']}")
                    st.divider()
                
                # Scoreboard
                score_percentage = int((correct_count / len(quiz)) * 100)
                st.markdown(f"""
                <div class="study-card accent-card" style="text-align: center;">
                    <h3>Your Final Score: <strong>{correct_count} / {len(quiz)}</strong> ({score_percentage}%)</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Option to reset/regenerate
                col_reset1, col_reset2 = st.columns(2)
                with col_reset1:
                    if st.button("🔄 Retake This Quiz"):
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.rerun()
                with col_reset2:
                    if st.button("🆕 Generate A New Quiz"):
                        st.session_state.quiz = None
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.rerun()

elif selected_page == "🃏 Active Flashcards":
    if verify_notes_present():
        st.subheader("🃏 Active Flashcard Deck")
        st.write("Train your memory using interactive flip flashcards generated from your study material.")
        
        if st.session_state.flashcards is None:
            if st.button("✨ Generate Flashcards", type="primary"):
                with st.spinner("Creating active recall cards..."):
                    prompt = f"""
                    Generate exactly 5 flashcards based on this study content.
                    Return the response as a raw JSON array of objects.
                    Each object MUST have:
                    - "front": string (question or term)
                    - "back": string (answer or explanation)
                    
                    Do NOT wrap the output in markdown code blocks. Just output raw valid JSON.
                    Content:
                    {st.session_state.user_text}
                    """
                    result = ask_ai(prompt, is_json=True)
                    if result:
                        try:
                            # Clean up markdown code blocks if the model returned them anyway
                            cleaned_result = result.strip()
                            if cleaned_result.startswith("```"):
                                match = re.search(r"```(?:json)?\s*(.*?)```", cleaned_result, re.DOTALL)
                                if match:
                                    cleaned_result = match.group(1)
                                    
                            flashcards_data = json.loads(cleaned_result)
                            st.session_state.flashcards = flashcards_data
                            st.session_state.flashcard_index = 0
                            st.session_state.flashcard_reveal = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing flashcards JSON. Please try again. Details: {e}")
                            st.code(result)
        else:
            # Flashcards are loaded!
            cards = st.session_state.flashcards
            idx = st.session_state.flashcard_index
            reveal = st.session_state.flashcard_reveal
            
            # Progress indicators
            st.progress((idx + 1) / len(cards))
            st.write(f"Card {idx + 1} of {len(cards)}")
            
            # Card Display Box
            current_card = cards[idx]
            if not reveal:
                st.markdown(f"""
                <div class="flashcard-outer">
                    <div class="flashcard-inner">
                        <div class="flashcard-badge">Front</div>
                        <div class="flashcard-text">{current_card['front']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("👁️ Reveal Answer", type="primary"):
                    st.session_state.flashcard_reveal = True
                    st.rerun()
            else:
                st.markdown(f"""
                <div class="flashcard-outer">
                    <div class="flashcard-inner reveal">
                        <div class="flashcard-badge">Back</div>
                        <div class="flashcard-text">{current_card['back']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🙈 Hide Answer"):
                    st.session_state.flashcard_reveal = False
                    st.rerun()
            
            st.write("") # Spacer
            
            # Navigation buttons
            nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
            with nav_col1:
                # Disabled if first card
                if st.button("⬅️ Previous Card", disabled=(idx == 0)):
                    st.session_state.flashcard_index = idx - 1
                    st.session_state.flashcard_reveal = False
                    st.rerun()
            with nav_col2:
                # Re-generate option
                if st.button("🔄 Reset Deck"):
                    st.session_state.flashcards = None
                    st.session_state.flashcard_index = 0
                    st.session_state.flashcard_reveal = False
                    st.rerun()
            with nav_col3:
                # Disabled if last card
                if st.button("➡️ Next Card", disabled=(idx == len(cards) - 1)):
                    st.session_state.flashcard_index = idx + 1
                    st.session_state.flashcard_reveal = False
                    st.rerun()
