import logging
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from openai.types.chat import ChatCompletion
from app.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis on content examples"""
    content_type: str
    style_patterns: Dict[str, Any]
    structure_patterns: Dict[str, Any]
    tone_analysis: Dict[str, Any]
    format_requirements: Dict[str, Any]
    confidence_score: float
    analysis_metadata: Dict[str, Any]

class PatternExtractionError(Exception):
    """Raised when pattern extraction fails"""
    pass

class PatternExtractionService:
    """Service for extracting content patterns from examples and generating structured prompts"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
        
        # Analysis prompts for different aspects
        self.STYLE_ANALYSIS_PROMPT = """
        Analyze the writing style of these {content_type} examples. Extract:
        1. Tone (formal/casual, warm/professional, etc.)
        2. Voice (first person, second person, collective "we")
        3. Language complexity (simple/advanced vocabulary)
        4. Sentence structure preferences
        5. Common phrases or expressions used
        
        Examples:
        {examples}
        
        Return analysis as JSON with confidence score (0-1).
        """
        
        self.STRUCTURE_ANALYSIS_PROMPT = """
        Analyze the structural patterns of these {content_type} examples. Extract:
        1. Common sections/headings used
        2. Information organization flow
        3. Length patterns (word count, paragraph count)
        4. Opening and closing patterns
        5. Use of lists, quotes, references
        
        Examples:
        {examples}
        
        Return analysis as JSON with confidence score (0-1).
        """
        
        self.TEMPLATE_GENERATION_PROMPT = """
        Based on this pattern analysis, create a structured prompt template that will generate {content_type} content matching this organization's unique style.

        Pattern Analysis:
        Style: {style_patterns}
        Structure: {structure_patterns}
        Tone: {tone_analysis}
        Format: {format_requirements}

        Create a comprehensive prompt template that:
        1. Captures their unique voice and tone
        2. Follows their structural preferences
        3. Matches their complexity level
        4. Uses their preferred formatting
        5. Can be applied to any sermon content

        The template should be detailed enough that when combined with sermon content, it produces content that feels like this organization wrote it.

        Return as JSON with:
        {{
            "structured_prompt": "The complete prompt template",
            "key_style_elements": ["list", "of", "elements"],
            "confidence_score": 0.95
        }}
        """


    async def extract_patterns(
        self, 
        examples: List[str], 
        content_type_name: str,
        description: Optional[str] = None
    ) -> PatternAnalysisResult:
        """
        Extract patterns from content examples and generate structured prompt
        
        Args:
            examples: List of 1-5 content examples
            content_type_name: User-defined content type name (e.g., "small group guide")
            description: Optional description of content type
            
        Returns:
            PatternAnalysisResult with extracted patterns and confidence score
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting pattern extraction for '{content_type_name}' with {len(examples)} examples")
            
            # Validate inputs
            self._validate_examples(examples, content_type_name)
            
            # Stage 1: Analyze different aspects in parallel
            style_analysis = await self._analyze_style_patterns(examples, content_type_name)
            structure_analysis = await self._analyze_structure_patterns(examples, content_type_name)
            
            # Stage 2: Combine analyses
            combined_analysis = self._combine_analyses(style_analysis, structure_analysis)
            
            # Stage 3: Calculate overall confidence
            confidence_score = self._calculate_confidence_score(combined_analysis)
            
            # Stage 4: Create structured result
            result = PatternAnalysisResult(
                content_type=content_type_name,
                style_patterns=combined_analysis["style"],
                structure_patterns=combined_analysis["structure"],
                tone_analysis=combined_analysis["tone"],
                format_requirements=combined_analysis["format"],
                confidence_score=confidence_score,
                analysis_metadata={
                    "example_count": len(examples),
                    "processing_time_seconds": time.time() - start_time,
                    "description": description,
                    "analysis_timestamp": time.time()
                }
            )
            
            processing_time = time.time() - start_time
            self.logger.info(
                f"Pattern extraction completed for {content_type_name}: "
                f"confidence={confidence_score:.3f}, time={processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pattern extraction failed for {content_type_name}: {str(e)}", exc_info=True)
            raise PatternExtractionError(f"Failed to extract patterns: {str(e)}") from e

    async def generate_structured_prompt(self, analysis: PatternAnalysisResult) -> str:
        """
        Generate a structured prompt template from pattern analysis
        
        Args:
            analysis: Pattern analysis result
            
        Returns:
            Structured prompt template string
        """
        try:
            self.logger.info(f"Generating structured prompt for {analysis.content_type}")
            
            # Use the template generation prompt
            prompt = self.TEMPLATE_GENERATION_PROMPT.format(
                content_type=analysis.content_type,
                style_patterns=json.dumps(analysis.style_patterns, indent=2),
                structure_patterns=json.dumps(analysis.structure_patterns, indent=2),
                tone_analysis=json.dumps(analysis.tone_analysis, indent=2),
                format_requirements=json.dumps(analysis.format_requirements, indent=2)
            )
            
            response: ChatCompletion = self.client.chat.completions.create(
                model=getattr(settings, 'PATTERN_EXTRACTION_MODEL', 'gpt-4o'),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert at creating AI prompt templates that capture "
                            "organizational voice, style, and formatting preferences. Create "
                            "precise, detailed prompts that will reliably reproduce the "
                            "organization's unique content style."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent templates
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            structured_prompt = result.get("structured_prompt", "")
            
            if not structured_prompt:
                raise PatternExtractionError("Failed to generate structured prompt")
            
            self.logger.info(f"Generated structured prompt for {analysis.content_type} ({len(structured_prompt)} chars)")
            return structured_prompt
            
        except Exception as e:
            self.logger.error(f"Failed to generate structured prompt: {str(e)}", exc_info=True)
            raise PatternExtractionError(f"Failed to generate prompt template: {str(e)}") from e

    async def _analyze_style_patterns(self, examples: List[str], content_type: str) -> Dict[str, Any]:
        """Analyze writing style patterns"""
        try:
            examples_text = "\n\n---\n\n".join(examples)
            
            response: ChatCompletion = self.client.chat.completions.create(
                model=getattr(settings, 'PATTERN_EXTRACTION_MODEL', 'gpt-4o'),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert writing analyst. Analyze content patterns precisely."
                    },
                    {
                        "role": "user",
                        "content": self.STYLE_ANALYSIS_PROMPT.format(
                            content_type=content_type,
                            examples=examples_text
                        )
                    }
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"Style analysis failed: {str(e)}")
            raise PatternExtractionError(f"Style analysis failed: {str(e)}") from e

    async def _analyze_structure_patterns(self, examples: List[str], content_type: str) -> Dict[str, Any]:
        """Analyze structural patterns"""
        try:
            examples_text = "\n\n---\n\n".join(examples)
            
            response: ChatCompletion = self.client.chat.completions.create(
                model=getattr(settings, 'PATTERN_EXTRACTION_MODEL', 'gpt-4o'),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content structure analyst. Identify organizational patterns."
                    },
                    {
                        "role": "user",
                        "content": self.STRUCTURE_ANALYSIS_PROMPT.format(
                            content_type=content_type,
                            examples=examples_text
                        )
                    }
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"Structure analysis failed: {str(e)}")
            raise PatternExtractionError(f"Structure analysis failed: {str(e)}") from e

    def _validate_examples(self, examples: List[str], content_type: str) -> None:
        """Validate example inputs"""
        if not examples:
            raise PatternExtractionError("At least one example is required")
        
        if len(examples) > 5:
            raise PatternExtractionError("Maximum 5 examples allowed")
        
        if not content_type or len(content_type.strip()) < 2:
            raise PatternExtractionError("Valid content type name is required")
        
        # Check example quality
        for i, example in enumerate(examples):
            if not example or len(example.strip()) < 50:
                raise PatternExtractionError(f"Example {i+1} is too short (minimum 50 characters)")
            
            if len(example) > 10000:
                raise PatternExtractionError(f"Example {i+1} is too long (maximum 10,000 characters)")

    def _combine_analyses(self, style_analysis: Dict, structure_analysis: Dict) -> Dict[str, Any]:
        """Combine style and structure analyses"""
        return {
            "style": style_analysis.get("style_patterns", {}),
            "structure": structure_analysis.get("structure_patterns", {}),
            "tone": style_analysis.get("tone_analysis", {}),
            "format": structure_analysis.get("format_requirements", {})
        }

    def _calculate_confidence_score(self, combined_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score for pattern extraction"""
        try:
            scores = []
            
            # Check each analysis component
            for component_name, component_data in combined_analysis.items():
                if isinstance(component_data, dict):
                    # Look for confidence scores in the component
                    component_confidence = component_data.get("confidence_score", 0.5)
                    scores.append(float(component_confidence))
                    
                    # Boost confidence for detailed analysis
                    detail_count = len([k for k, v in component_data.items() 
                                      if v and k != "confidence_score"])
                    if detail_count >= 3:
                        scores.append(0.1)  # Bonus for detailed analysis
            
            if not scores:
                return 0.5  # Default moderate confidence
            
            # Average the scores with a minimum threshold
            avg_score = sum(scores) / len(scores)
            
            # Ensure score is within valid range
            confidence = max(0.0, min(1.0, avg_score))
            
            return round(confidence, 3)
            
        except Exception as e:
            self.logger.warning(f"Confidence calculation failed: {str(e)}")
            return 0.5  # Default to moderate confidence

# Create singleton instance
pattern_extraction_service = PatternExtractionService()