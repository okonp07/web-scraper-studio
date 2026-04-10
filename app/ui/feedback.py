"""Feedback page content."""

from __future__ import annotations

import streamlit as st

from app.models import FeedbackCategory, FeedbackSubmission
from app.services.feedback_service import FeedbackService


def render_feedback(feedback_service: FeedbackService) -> None:
    """Render the feedback page and handle form submission."""

    st.markdown(
        """
        <section class="hero-panel about-hero">
          <div class="hero-content">
            <p class="eyebrow">Feedback</p>
            <h1 class="about-title">Help Improve Web Scraper Studio</h1>
            <p class="about-subtitle">
              Share bugs, feature ideas, usability notes, and suggestions that can
              make the product more useful for real-world research and document workflows.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    form_col, info_col = st.columns([1.3, 0.9], gap="large")

    with form_col:
        st.markdown("### Send feedback")
        with st.form("feedback_form", clear_on_submit=True):
            identity_col, role_col = st.columns(2, gap="medium")
            with identity_col:
                name = st.text_input(
                    "Name",
                    placeholder="Your name",
                    help="Optional. Add your name if you would like your feedback to be attributable.",
                )
                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    help="Optional. Add an email if you want the team to follow up with you.",
                )
            with role_col:
                role = st.text_input(
                    "Role or Organization",
                    placeholder="Researcher, student, analyst, product team...",
                    help="Optional. This helps us understand the kind of workflow your feedback comes from.",
                )
                category = st.selectbox(
                    "Feedback type",
                    options=list(FeedbackCategory),
                    index=0,
                    format_func=lambda item: item.value.replace("_", " ").title(),
                    help="Choose the kind of feedback you are sharing so it can be reviewed in the right context.",
                )

            rating = st.slider(
                "Experience rating",
                min_value=1,
                max_value=5,
                value=4,
                help="Rate your current experience with the app. 1 means very poor, 5 means excellent.",
            )
            message = st.text_area(
                "Feedback",
                placeholder="Tell us what happened, what you expected, what felt unclear, or what would make the app better.",
                height=180,
                help="Describe the issue, improvement, or observation in enough detail that another developer can act on it.",
            )
            improvement_ideas = st.text_area(
                "Improvement ideas",
                placeholder="Optional: share feature ideas, workflow suggestions, or examples of what would help your use case.",
                height=120,
                help="Optional. Add suggestions for features, quality improvements, export enhancements, or workflow ideas.",
            )
            allow_follow_up = st.checkbox(
                "You may contact me about this feedback",
                value=False,
                help="Enable this only if you are happy to be contacted about your submission.",
            )
            submitted = st.form_submit_button("Submit feedback", type="primary", use_container_width=True)

        if submitted:
            try:
                submission = FeedbackSubmission(
                    name=name,
                    email=email,
                    role=role,
                    category=category,
                    rating=rating,
                    message=message,
                    improvement_ideas=improvement_ideas,
                    allow_follow_up=allow_follow_up,
                    page_context="feedback",
                )
                feedback_service.save(submission)
                st.success(
                    "Thank you for the feedback. Your submission was recorded successfully."
                )
            except Exception as exc:
                st.error(f"Could not submit feedback: {exc}")

    with info_col:
        st.markdown(
            f"""
            <div class="about-card">
              <h2>What Good Feedback Looks Like</h2>
              <p>
                The most helpful submissions explain what you were trying to do,
                what happened instead, and what outcome would have made the app
                more useful. That gives developers something concrete to improve.
              </p>
              <p>
                Strong examples include export formatting issues, missing crawl
                controls, websites that fail to scrape cleanly, unclear interface
                behavior, and ideas for making the outputs more publication-ready.
              </p>
            </div>
            <div class="about-card">
              <h2>Where Submissions Go</h2>
              <p>
                This form currently stores submissions in a local JSONL file at
                <code>{feedback_service.storage_path}</code>.
              </p>
              <p>
                For durable production collection on ephemeral hosts, another
                developer can connect this page to a backend such as Supabase,
                Google Sheets, a database, or an email workflow without changing
                the rest of the app experience.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
