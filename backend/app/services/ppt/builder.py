"""
NEXUS EDU — Presentation Builder.

Injects structured AI presentation data into a reusable PowerPoint template.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pptx import Presentation as PPTXPresentation
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN

from app.schemas.presentation import Presentation, Slide, ContentBlock


class PresentationBuilder:
    """
    Builds a `.pptx` file from a structured Presentation schema.
    Uses a base template to preserve branding, fonts, and layout.
    """

    def __init__(self, template_path: str = "app/storage/template.pptx") -> None:
        """Initialize with a base template. Falls back to a blank template if not found."""
        self.template_path = template_path
        if not os.path.exists(self.template_path):
            # Create a blank Presentation if template doesn't exist yet
            self.prs = PPTXPresentation()
        else:
            self.prs = PPTXPresentation(self.template_path)

    def _add_title_slide(self, title: str, subtitle: str | None, author: str | None) -> None:
        """Add a main title slide."""
        # 0 is usually the title slide layout in most templates
        title_slide_layout = self.prs.slide_layouts[0]
        slide = self.prs.slides.add_slide(title_slide_layout)
        
        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = title
            
        # Set subtitle
        if len(slide.placeholders) > 1:
            subtitle_text = subtitle or ""
            if author:
                subtitle_text += f"\n\nBy: {author}"
            slide.placeholders[1].text = subtitle_text.strip()

    def _add_content_slide(self, slide_data: Slide) -> None:
        """Add a standard content slide and inject blocks."""
        # 1 is usually the 'Title and Content' layout
        # 3 is usually 'Two Content'
        # 5 is usually 'Title Only'
        # We try to pick layout based on layout_hint
        
        layout_idx = 1
        if slide_data.layout_hint == "two_column":
            layout_idx = 3 if len(self.prs.slide_layouts) > 3 else 1
        elif slide_data.layout_hint == "title_only" or slide_data.slide_type == "image_placeholder":
            layout_idx = 5 if len(self.prs.slide_layouts) > 5 else 1
        
        # Fallback if template has fewer layouts
        if layout_idx >= len(self.prs.slide_layouts):
            layout_idx = 0
            
        slide_layout = self.prs.slide_layouts[layout_idx]
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Set Title
        if slide.shapes.title:
            slide.shapes.title.text = slide_data.title
            
        # Add Speaker Notes
        if slide_data.speaker_notes and slide.has_notes_slide:
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.text = slide_data.speaker_notes

        # Process Content Blocks
        if slide_data.content_blocks and len(slide.placeholders) > 1:
            content_placeholder = slide.placeholders[1]
            tf = content_placeholder.text_frame
            tf.clear()
            
            for block in slide_data.content_blocks:
                if block.heading:
                    p = tf.add_paragraph()
                    p.text = block.heading
                    p.font.bold = True
                    p.space_after = Pt(10)

                if block.block_type == "bullet_points" and block.bullets:
                    for bullet in block.bullets:
                        p = tf.add_paragraph()
                        p.text = bullet
                        p.level = 1
                elif block.block_type == "paragraph" and block.paragraph:
                    p = tf.add_paragraph()
                    p.text = block.paragraph
                    p.level = 0
                elif block.block_type in ("quote", "key_concept") and block.quote_text:
                    p = tf.add_paragraph()
                    p.text = f"\" {block.quote_text} \""
                    p.font.italic = True
                    p.alignment = PP_ALIGN.CENTER
                    p.level = 0
                elif block.block_type == "code_snippet" and block.code:
                    p = tf.add_paragraph()
                    p.text = block.code
                    p.font.name = "Courier New"
                    p.level = 0
                elif block.block_type == "table" and block.table_data:
                    # Python-pptx doesn't easily convert a text placeholder to a table.
                    # We would add a table shape here if doing it properly, 
                    # but for basic injection we can just format it as text for now
                    # if the placeholder is purely text-based.
                    # A robust implementation would remove the placeholder and add a table shape.
                    p = tf.add_paragraph()
                    p.text = " | ".join(block.table_data.headers)
                    p.font.bold = True
                    for row in block.table_data.rows:
                        rp = tf.add_paragraph()
                        rp.text = " | ".join(row)

    def build(self, presentation_data: Presentation, output_path: str) -> str:
        """
        Build the PPTX and save it to the output path.
        Returns the absolute path to the saved file.
        """
        self._add_title_slide(
            title=presentation_data.title,
            subtitle=presentation_data.subtitle,
            author=presentation_data.author,
        )
        
        for slide in presentation_data.slides:
            self._add_content_slide(slide)
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.prs.save(output_path)
        return output_path
