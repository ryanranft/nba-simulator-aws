"""
Tests for 0.0012: RAG + LLM Integration

Tests query understanding, RAG retrieval, prompt building, and LLM integration.

Run with:
    pytest tests/phases/phase_0/test_0_0012.py -v
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from scripts.ml.query_understanding import QueryUnderstanding
from scripts.ml.prompt_builder import PromptBuilder
from scripts.ml.llm_integration import LLMIntegration


class TestQueryUnderstanding:
    """Test query parsing and understanding"""

    def test_classify_intent_comparison(self):
        """Test comparison intent classification"""
        qp = QueryUnderstanding()
        query = "Compare LeBron James and Michael Jordan"
        analysis = qp.analyze_query(query)
        assert analysis["intent"] == "comparison"

    def test_classify_intent_statistics(self):
        """Test statistics intent classification"""
        qp = QueryUnderstanding()
        query = "What are LeBron James's career stats?"
        analysis = qp.analyze_query(query)
        assert analysis["intent"] == "statistics"

    def test_extract_season(self):
        """Test season extraction"""
        qp = QueryUnderstanding()
        query = "Who won MVP in the 2022 season?"
        analysis = qp.analyze_query(query)
        assert 2022 in analysis["entities"]["seasons"]


class TestPromptBuilder:
    """Test prompt construction"""

    def test_build_prompt_basic(self):
        """Test basic prompt building"""
        builder = PromptBuilder(model="gpt-4")
        contexts = [
            {
                "source": "player",
                "metadata": {"name": "LeBron James"},
                "content": "Test",
                "similarity": 0.95,
            }
        ]
        query_analysis = {
            "intent": "general",
            "query_type": "general_query",
            "entities": {},
            "temporal": {},
        }
        prompt = builder.build_prompt("Who is LeBron James?", contexts, query_analysis)
        assert "LeBron James" in prompt

    def test_cost_estimation(self):
        """Test cost calculation"""
        builder = PromptBuilder(model="gpt-4")
        prompt = "Test prompt"
        cost = builder.estimate_cost(prompt, response_tokens=500)
        assert cost["total_cost"] > 0


class TestLLMIntegration:
    """Test LLM API integration"""

    @patch("openai.ChatCompletion.create")
    def test_generate_response(self, mock_create):
        """Test response generation"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_create.return_value = mock_response
        llm = LLMIntegration(model="gpt-3.5-turbo")
        response = llm._generate_standard("Test prompt", "Test system")
        assert response == "Test response"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
