"""
NEXUS EDU — Paper Analysis Schema.

Defines the strict Pydantic output schema for AI-generated academic paper analysis.
This is the most structurally complex schema — it enforces extraction of research
claims, evidence, methodology, and critical evaluation into machine-readable form.

Key anti-hallucination mechanisms:
  - Finding.directly_quoted: flags whether a claim is paraphrased or quoted,
    making citation verification possible.
  - CriticalEvaluation.*_score: bounded integers (1–10) prevent vague ordinal claims.
  - AnalysisMetadata.confidence_score: float (0–1) reflecting RAG chunk coverage,
    exposing low-confidence analyses to the UI rather than hiding uncertainty.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, field_validator

from app.ai.llm.models import StrictBaseModel


# ── Methodology ───────────────────────────────────────────────────────────────


class MethodologyBlock(StrictBaseModel):
    """Structured description of the research methodology used in the paper."""

    methodology_type: Annotated[
        Literal[
            "quantitative",
            "qualitative",
            "mixed",
            "theoretical",
            "experimental",
            "survey",
            "case_study",
            "review",
        ],
        Field(description="The primary research methodology classification."),
    ]
    description: Annotated[
        str,
        Field(
            min_length=50,
            max_length=1000,
            description=(
                "A detailed description of how the research was conducted. "
                "Include data collection, processing, and analysis approach."
            ),
        ),
    ]
    datasets_used: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=10,
            description="Named datasets used in the research. Omit if none.",
        ),
    ]
    evaluation_metrics: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=15,
            description="Metrics used to evaluate results (e.g. 'F1-score', 'BLEU', 'accuracy').",
        ),
    ]
    tools_and_frameworks: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=15,
            description="Tools, libraries, or frameworks mentioned (e.g. 'PyTorch', 'SPSS').",
        ),
    ]


# ── Finding ───────────────────────────────────────────────────────────────────


class Finding(StrictBaseModel):
    """A single key finding or result from the paper, with evidence and significance."""

    finding_number: Annotated[
        int,
        Field(ge=1, description="1-indexed finding number for ordering."),
    ]
    claim: Annotated[
        str,
        Field(
            min_length=20,
            max_length=600,
            description="The specific claim or result reported by the authors.",
        ),
    ]
    evidence: Annotated[
        str,
        Field(
            min_length=20,
            max_length=600,
            description=(
                "The supporting evidence from the paper (e.g. a statistic, table result, "
                "or experimental observation) that substantiates this claim."
            ),
        ),
    ]
    significance: Annotated[
        Literal["high", "medium", "low"],
        Field(
            description=(
                "The assessed significance of this finding relative to the paper's contribution."
            )
        ),
    ]
    directly_quoted: Annotated[
        bool,
        Field(
            description=(
                "True if the claim text is a direct quotation from the paper. "
                "False if it is a paraphrase. This enables citation verification."
            )
        ),
    ]


# ── Related Work ──────────────────────────────────────────────────────────────


class RelatedWork(StrictBaseModel):
    """A related paper referenced by the analyzed work."""

    title: Annotated[
        str,
        Field(min_length=5, max_length=300, description="Title of the related work."),
    ]
    authors: Annotated[
        list[str] | None,
        Field(default=None, description="Author names of the related work."),
    ]
    relationship: Annotated[
        Literal["builds_upon", "contradicts", "extends", "compares", "uses"],
        Field(
            description=(
                "How the analyzed paper relates to this work: "
                "'builds_upon' = directly extends it; "
                "'contradicts' = disputes its claims; "
                "'extends' = broadens its scope; "
                "'compares' = benchmarks against it; "
                "'uses' = adopts its methodology or tool."
            )
        ),
    ]
    summary: Annotated[
        str,
        Field(
            min_length=20,
            max_length=300,
            description="A brief description of the related work and its relevance.",
        ),
    ]


# ── Critical Evaluation ───────────────────────────────────────────────────────


class CriticalEvaluation(StrictBaseModel):
    """
    A structured critical evaluation of the paper's quality and contribution.

    All scores are integers bounded 1–10 to prevent vague ordinal claims
    (e.g. 'good', 'excellent') that vary between LLM runs.
    """

    overall_quality: Annotated[
        Literal["excellent", "good", "fair", "poor"],
        Field(description="Overall assessed quality of the paper."),
    ]
    novelty_score: Annotated[
        int,
        Field(
            ge=1,
            le=10,
            description="How novel or original the contribution is (1 = incremental, 10 = breakthrough).",
        ),
    ]
    methodological_rigor: Annotated[
        int,
        Field(
            ge=1,
            le=10,
            description="Quality of the research methodology (1 = flawed, 10 = rigorous).",
        ),
    ]
    reproducibility_score: Annotated[
        int,
        Field(
            ge=1,
            le=10,
            description=(
                "How reproducible the results are based on the reported methods "
                "(1 = impossible to reproduce, 10 = fully reproducible)."
            ),
        ),
    ]
    strengths: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=5,
            description="Specific strengths of the paper. Min 1, max 5 items.",
        ),
    ]
    weaknesses: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=5,
            description="Specific weaknesses or limitations of the paper. Min 1, max 5 items.",
        ),
    ]
    recommendation: Annotated[
        Literal["highly_recommend", "recommend", "neutral", "not_recommend"],
        Field(description="Whether to recommend this paper for reading or citation."),
    ]


# ── Metadata ─────────────────────────────────────────────────────────────────


class AnalysisMetadata(StrictBaseModel):
    """Generation and source provenance metadata for the paper analysis."""

    @field_validator("generated_at", mode="before")
    @classmethod
    def parse_generated_at(cls, v: object) -> object:
        """Accept ISO 8601 strings from the LLM and convert to datetime."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    generated_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(timezone.utc),
            description="UTC timestamp when this analysis was generated.",
        ),
    ]
    source_document_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="IDs of the RAG-retrieved source document chunks used for this analysis.",
        ),
    ]
    analysis_depth: Annotated[
        Literal["surface", "standard", "deep"],
        Field(
            description=(
                "Depth of analysis performed: "
                "'surface' = abstract + intro only; "
                "'standard' = full paper; "
                "'deep' = full paper + related works."
            )
        ),
    ]
    confidence_score: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description=(
                "Confidence score (0–1) reflecting how much of the paper content was covered "
                "by the retrieved RAG chunks. Low scores indicate the analysis may be incomplete."
            ),
        ),
    ]


# ── Root model ───────────────────────────────────────────────────────────────


class PaperAnalysis(StrictBaseModel):
    """
    Complete AI-generated academic paper analysis.

    All AI generation for paper analysis must return this exact schema.
    The directly_quoted flag on each Finding and the confidence_score on
    metadata make every output auditable and citation-verifiable.
    """

    paper_title: Annotated[
        str,
        Field(
            min_length=5,
            max_length=300,
            description="Full title of the paper being analyzed.",
        ),
    ]
    authors: Annotated[
        list[str],
        Field(
            min_length=1,
            description="Full list of paper authors.",
        ),
    ]
    publication_year: Annotated[
        int | None,
        Field(default=None, ge=1900, le=2030, description="Year of publication."),
    ]
    doi_or_url: Annotated[
        str | None,
        Field(default=None, max_length=500, description="DOI or URL of the paper."),
    ]
    abstract_summary: Annotated[
        str,
        Field(
            min_length=50,
            max_length=600,
            description="A neutral summary of the paper's abstract and core premise.",
        ),
    ]
    research_problem: Annotated[
        str,
        Field(
            min_length=30,
            max_length=500,
            description="The specific research problem or gap this paper addresses.",
        ),
    ]
    research_questions: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=5,
            description="The explicit or implied research questions the paper addresses. Max 5.",
        ),
    ]
    methodology: Annotated[
        MethodologyBlock,
        Field(description="Structured description of the research methodology."),
    ]
    key_findings: Annotated[
        list[Finding],
        Field(
            min_length=1,
            max_length=20,
            description="All key findings extracted from the paper. Min 1, max 20.",
        ),
    ]
    contributions: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=10,
            description="The paper's stated or implied contributions to the field. Max 10.",
        ),
    ]
    limitations: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=10,
            description="Limitations acknowledged by the authors or identified by analysis. Max 10.",
        ),
    ]
    future_work: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=5,
            description="Future research directions mentioned or implied. Omit if none. Max 5.",
        ),
    ]
    related_works: Annotated[
        list[RelatedWork] | None,
        Field(
            default=None,
            max_length=10,
            description="Key related works referenced by the paper. Max 10.",
        ),
    ]
    critical_evaluation: Annotated[
        CriticalEvaluation,
        Field(description="Structured critical evaluation of the paper's quality."),
    ]
    metadata: Annotated[
        AnalysisMetadata,
        Field(description="Generation provenance and confidence metadata."),
    ]
