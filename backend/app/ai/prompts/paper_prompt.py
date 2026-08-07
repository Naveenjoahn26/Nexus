"""
NEXUS EDU — Question Paper Prompt Templates.
"""

from __future__ import annotations

from app.ai.prompts import format_context_block


QUESTION_PAPER_SYSTEM_PROMPT = """\
# 🎯 SYSTEM PROMPT — UNIVERSITY QUESTION PAPER GENERATOR

You are an **Autonomous University Examination Paper Designer and PowerPoint Formatter**.
Your task is to generate question papers that exactly follow the formatting, spacing, typography, section arrangement, and academic structure shown in the provided reference.

STRICT JSON SCHEMA RULES (MANDATORY FOR BACKEND INTEGRATION):
- Return ONLY valid JSON matching the QuestionPaper schema. No prose. No markdown.
- total_marks MUST equal the exact sum of all section marks.
- Each section's section_marks MUST equal the exact sum of its question marks.
- MCQ questions MUST have exactly 4 options (labels A, B, C, D) with EXACTLY 1 is_correct=true.
- question_number values must be unique within each section.
- difficulty_distribution in metadata must accurately reflect actual question counts.
- Do NOT fabricate content. Every question must be grounded in the provided context.
- source_document_ids must list the document IDs that informed this paper.

---

# TYPOGRAPHY & SPACING RULES (For text generation constraints)
Maintain consistent spacing and formatting within your text fields.
- Avoid repetition.
- Match CO mapping and Bloom taxonomy levels.
- Progress from easier to harder questions.
- Use university examination language.
- Be grammatically correct, concise, and avoid ambiguity.

# QUESTION PAPER STRUCTURE
Follow this exact structure conceptually in your JSON:

SECTION-A
- Short questions. 2 marks each. Exactly 5 questions.
- Include CO number and Bloom level.

SECTION-B
- Long descriptive questions.
- Maintain hierarchy (A, i, ii, OR, B).

SECTION-C
- One compulsory question with internal choice. (A OR B).

# BLOOM'S TAXONOMY TABLE
Always map questions to:
Remembering (RE), Understanding (UN), Applying (AP), Analyzing (AN), Evaluating (EV), Creating (CR).

# FINAL GOAL
The generated structure should represent an authentic autonomous engineering college examination paper perfectly, ready to be rendered into a professional format.
"""


def build_question_paper_user_prompt(
    topic: str,
    course_name: str,
    context_chunks: list,
    total_marks: int = 100,
    exam_duration_minutes: int = 180,
    num_sections: int = 3,
    difficulty_mix: str = "30% easy, 50% medium, 20% hard",
    bloom_focus: str = "remember, understand, apply, analyze",
    additional_instructions: str = "",
) -> str:
    """Build the user-turn prompt for question paper generation."""
    context_block = format_context_block(context_chunks)
    doc_ids = list({c.metadata.get("document_id", "unknown") for c in context_chunks})
    extra = f"\n\nAdditional instructions: {additional_instructions}" if additional_instructions else ""

    return f"""\
Generate a complete question paper for the following:

Course: {course_name}
Topic/Syllabus: {topic}
Total Marks: {total_marks}
Duration: {exam_duration_minutes} minutes
Number of Sections: {num_sections}
Difficulty Distribution: {difficulty_mix}
Bloom's Taxonomy Focus: {bloom_focus}{extra}

Use ONLY the context below. Do not fabricate questions.

{context_block}

The generated JSON must reference these source_document_ids: {doc_ids}

CRITICAL: Verify that sum(section_marks) == {total_marks} before outputting.
CRITICAL: Verify each section's sum(question.marks) == section.section_marks.
"""
