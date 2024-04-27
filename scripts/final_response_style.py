import streamlit as st


key_points = [
    "No argument is complete because there's always room for more premises.",
    "A premise requires another premises to justify its truth.",
    "What happens when we reach a premise that can't be justified by another premise? Is it still valid?",
]

advices = [
    "Consider researching philosophical theories about the nature of premises and arguments, such as foundationalism and infinitism, to deepen your understanding of the topic.",
    "Try engaging in a philosophical discussion with others, presenting your belief that no argument is complete because there's always room for more premises. This could provide you with different perspectives.",
    "Reflect on the implications of your belief. If every premise requires another premise for justification, what does this mean for our ability to reach a definitive conclusion in an argument?",
]

readings = [
    {
        "title": "Infinite Regress Argument",
        "link": "https://plato.stanford.edu/entries/infinite-regress/",
        "snippet": "An infinite regress argument is an argument that makes the case that a particular...",
    },
    {
        "title": "Foundationalism",
        "link": "https://plato.stanford.edu/entries/foundational/",
        "snippet": "Foundationalism is a view about the structure of justification or knowledge."
    },
    {
        "title": "Infinitism",
        "link": "https://plato.stanford.edu/entries/infinitism/",
        "snippet": "Infinitism is a view in epistemology about the structure of knowledge and justification."
    },
]

tab1, tab2, tab3 = st.tabs(["Summary", "Suggestions", "Articles"])

with tab1:
    st.markdown("### 🔑 Key Points from Conversation")

    for point in key_points:
        with st.container(border=True):
            st.markdown(point)

with tab2:
    st.markdown("### 🧠 Ways to Explore Beliefs Further")

    for advice in advices:
        with st.container(border=True):
            st.markdown(advice)

with tab3:
    st.markdown("### 📚 Interesting Online Articles")

    for reading in readings:
        with st.container(border=True):
            st.markdown(f"**[{reading['title']}]({reading['link']})**")
            st.markdown(reading["snippet"])
