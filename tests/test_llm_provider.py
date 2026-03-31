from structural_screening_agent.decision_agent import build_bilingual_explanation
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.llm_providers import OpenAIProvider, resolve_provider
from structural_screening_agent.rule_engine import evaluate_screening


def test_missing_provider_configuration_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    provider = resolve_provider()

    assert provider.provider_name == "mock"
    assert provider.mode == "fallback"


def test_minimax_provider_uses_official_openai_sdk_compatibility(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "MiniMax-M1")

    provider = resolve_provider()

    assert provider.provider_name == "minimax"
    assert provider.mode == "live"
    assert provider.model_name == "MiniMax-M1"


def test_explanation_includes_provider_metadata_when_mocked(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    intake = main_demo_case()
    result = evaluate_screening(intake)
    explanation = build_bilingual_explanation(intake, result)

    assert explanation.provider == "mock"
    assert explanation.mode == "fallback"
    assert "有条件推进" in explanation.summary


def test_provider_can_be_loaded_from_dotenv_file(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_PROVIDER=minimax\nMINIMAX_API_KEY=test-key\nMINIMAX_MODEL=MiniMax-M2.5\n")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_MODEL", raising=False)

    provider = resolve_provider(dotenv_path=env_file)

    assert provider.provider_name == "minimax"
    assert provider.model_name == "MiniMax-M2.5"


def test_live_provider_error_falls_back_to_mock_explanation(monkeypatch) -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)

    def fake_generate_summary(*args, **kwargs) -> str:
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(OpenAIProvider, "generate_summary", fake_generate_summary)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    explanation = build_bilingual_explanation(intake, result)

    assert explanation.provider == "mock"
    assert explanation.mode == "fallback"
    assert explanation.requested_provider == "openai"
    assert explanation.fallback_reason == "provider unavailable"
