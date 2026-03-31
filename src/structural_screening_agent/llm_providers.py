import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from structural_screening_agent.bilingual import same_line
from structural_screening_agent.localization import Language, format_decision_localized
from structural_screening_agent.models import BuildingIntake, DecisionStatus, ScreeningResult


DEFAULT_MODELS = {
    "openai": "gpt-4.1-mini",
    "minimax": "MiniMax-M2.5",
    "gemini": "gemini-2.5-flash",
    "mock": "demo-mock",
}


def _decision_label(status: DecisionStatus) -> str:
    return format_decision_localized(status, "bilingual")


def _build_system_instruction(language: Language) -> str:
    if language == "zh":
        return (
            "你是面向项目决策者的结构筛查助手。不要改写既有决策结论。"
            "请用简洁、专业的中文解释当前规则引擎结论。"
        )
    return (
        "You are an engineering screening assistant for project decision makers. "
        "Do not change the decision status. "
        "Explain the existing rule-backed result clearly in concise professional English."
    )


def _build_user_prompt(
    intake: BuildingIntake, result: ScreeningResult, follow_up_questions: List[str], language: Language
) -> str:
    risk_text = "; ".join(item.title_en for item in result.risks) or "No major risks identified"
    missing_data = "; ".join(item.title_en for item in result.missing_data) or "No missing critical data"
    actions = "; ".join(item.title_en for item in result.recommended_actions) or "No specific action"
    questions = "; ".join(follow_up_questions) or "No follow-up questions"
    return (
        f"Project type: {intake.project_type}\n"
        f"Building type: {intake.building_type}\n"
        f"Structural system: {intake.structural_system}\n"
        f"Decision: {_decision_label(result.status)}\n"
        f"Confidence: {result.confidence}\n"
        f"Top risks: {risk_text}\n"
        f"Missing data: {missing_data}\n"
        f"Recommended actions: {actions}\n"
        f"Follow-up questions: {questions}\n"
        + (
            "Write one short executive summary in Chinese."
            if language == "zh"
            else "Write one short executive summary in English."
        )
    )


@dataclass
class BaseProvider:
    provider_name: str
    model_name: str
    mode: str

    def generate_summary(
        self, intake: BuildingIntake, result: ScreeningResult, follow_up_questions: List[str], language: Language
    ) -> str:
        raise NotImplementedError


@dataclass
class MockProvider(BaseProvider):
    def generate_summary(
        self, intake: BuildingIntake, result: ScreeningResult, follow_up_questions: List[str], language: Language
    ) -> str:
        headline = format_decision_localized(result.status, language)
        top_risk = result.risks[0] if result.risks else None
        action = result.recommended_actions[0] if result.recommended_actions else None
        pieces = [("结论" if language == "zh" else "Decision") + f": {headline}"]
        if top_risk is not None:
            pieces.append(
                ("关键风险" if language == "zh" else "Top Risk")
                + f": {(top_risk.title_zh if language == 'zh' else top_risk.title_en)}"
            )
        if action is not None:
            pieces.append(
                ("建议动作" if language == "zh" else "Recommended Action")
                + f": {(action.title_zh if language == 'zh' else action.title_en)}"
            )
        return " ".join(pieces)


@dataclass
class OpenAIProvider(BaseProvider):
    api_key: str
    base_url: str = ""

    def generate_summary(
        self, intake: BuildingIntake, result: ScreeningResult, follow_up_questions: List[str], language: Language
    ) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url or None)
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": _build_system_instruction(language)},
                {
                    "role": "user",
                    "content": _build_user_prompt(intake, result, follow_up_questions, language),
                },
            ],
        )
        return response.choices[0].message.content or ""


@dataclass
class GeminiProvider(BaseProvider):
    api_key: str

    def generate_summary(
        self, intake: BuildingIntake, result: ScreeningResult, follow_up_questions: List[str], language: Language
    ) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model_name,
            contents=_build_user_prompt(intake, result, follow_up_questions, language),
            config=types.GenerateContentConfig(
                system_instruction=_build_system_instruction(language),
                temperature=0.2,
            ),
        )
        return response.text or ""


def _resolve_model(provider_name: str) -> str:
    provider_specific_key = f"{provider_name.upper()}_MODEL"
    return os.getenv(provider_specific_key) or os.getenv("LLM_MODEL") or DEFAULT_MODELS[provider_name]


def _load_env_file(dotenv_path: Optional[Path] = None) -> None:
    candidate = dotenv_path or Path.cwd() / ".env"
    load_dotenv(candidate, override=False)


def resolve_provider(dotenv_path: Optional[Path] = None) -> BaseProvider:
    _load_env_file(dotenv_path)
    provider_name = (os.getenv("LLM_PROVIDER") or "mock").strip().lower()

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if api_key:
            return OpenAIProvider(
                provider_name="openai",
                model_name=_resolve_model("openai"),
                mode="live",
                api_key=api_key,
            )
        provider_name = "mock"
    elif provider_name == "minimax":
        api_key = os.getenv("MINIMAX_API_KEY", "").strip()
        if api_key:
            return OpenAIProvider(
                provider_name="minimax",
                model_name=_resolve_model("minimax"),
                mode="live",
                api_key=api_key,
                base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"),
            )
        provider_name = "mock"
    elif provider_name == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key:
            return GeminiProvider(
                provider_name="gemini",
                model_name=_resolve_model("gemini"),
                mode="live",
                api_key=api_key,
            )
        provider_name = "mock"

    return MockProvider(
        provider_name="mock",
        model_name=_resolve_model("mock"),
        mode="fallback",
    )
