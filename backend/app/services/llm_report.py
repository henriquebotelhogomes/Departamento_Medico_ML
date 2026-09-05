"""Multi-LLM Medical Report Generation Service.

Supports:
1. Gemini 3.8 Flash (Google AI Studio)
2. GPT 5.6 Luna (OpenCode Go / OpenAI-compatible API)
3. DeepSeek V4 Flash (OpenCode Go / OpenAI-compatible API)
4. Qwen 3.8 Flash (OpenCode Go / OpenAI-compatible API)
5. Motor Clínico Determinístico Local (Offline / Fallback Resiliente)
"""

from __future__ import annotations

import datetime
import hashlib
import time
from threading import Lock

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.prediction import LLMTelemetry, ReportRequest, ReportResponse

logger = get_logger(__name__)

# In-memory LRU-like cache and daily FinOps quota tracking
_REPORT_CACHE: dict[str, ReportResponse] = {}
_DAILY_QUOTA_LOCK = Lock()
_DAILY_QUOTA_DATE: datetime.date | None = None
_DAILY_EXTERNAL_CALLS: int = 0


def _get_cache_key(req: ReportRequest, model_choice: str) -> str:
    effective_label = req.override_label or req.label
    probs_str = ""
    if req.probs:
        probs_str = ";".join(f"{p.label}:{round(p.probability, 2)}" for p in req.probs)
    raw = (
        f"{model_choice}|{effective_label}|{round(req.confidence, 2)}|"
        f"{bool(req.is_ambiguous)}|{req.override_notes or ''}|{probs_str}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _check_and_increment_daily_quota(limit: int) -> bool:
    """Return True if within quota, False if daily cap reached."""
    global _DAILY_QUOTA_DATE, _DAILY_EXTERNAL_CALLS
    today = datetime.datetime.now(datetime.UTC).date()
    with _DAILY_QUOTA_LOCK:
        if today != _DAILY_QUOTA_DATE:
            _DAILY_QUOTA_DATE = today
            _DAILY_EXTERNAL_CALLS = 0
        if limit <= _DAILY_EXTERNAL_CALLS:
            return False
        _DAILY_EXTERNAL_CALLS += 1
        return True


def _store_in_cache(key: str, rep: ReportResponse) -> None:
    """Store report in cache, keeping memory bounded to 500 entries."""
    if len(_REPORT_CACHE) > 500:
        first_key = next(iter(_REPORT_CACHE))
        del _REPORT_CACHE[first_key]
    _REPORT_CACHE[key] = rep


# Medical ICD-10 and Clinical findings reference dictionary
CLINICAL_KNOWLEDGE = {
    0: {  # Covid-19
        "icd_10": "U07.1 (Infecção por COVID-19 comprovada por análise)",
        "findings": (
            "Campos pleuropulmonares com opacidades bilaterais em vidro fosco "
            "predominantemente periféricas e subpleurais, com distribuição basal multifocal. "
            "Ausência de consolidação lobar franca. Seios costofrênicos e cardiofrênicos livres. "
            "Silhueta cardíaca com dimensões preservadas."
        ),
        "impression": (
            "Padrão radiológico sugestivo de acometimento pulmonar viral atípico multifocal, "
            "altamente compatível com infecção por SARS-CoV-2 (COVID-19)."
        ),
        "recommendations": (
            "Correlação estrita com quadro clínico-epidemiológico e teste molecular RT-PCR. "
            "Considerar tomografia computadorizada de alta resolução (TCAR) se houver dessaturação."
        ),
    },
    1: {  # Normal
        "icd_10": "Z00.0 (Exame médico geral de rotina)",
        "findings": (
            "Transparência pulmonar habitual preservada bilateralmente, sem evidências de "
            "infiltrados alveolares, consolidações ou nódulos suspeitos. Hilos pulmonares "
            "anatômicos. Seios costofrênicos pérvios. Área cardíaca dentro dos limites de "
            "normalidade. Estruturas ósseas da caixa torácica íntegras."
        ),
        "impression": "Radiografia de tórax dentro dos padrões de normalidade radiológica.",
        "recommendations": (
            "Seguimento clínico habitual. Não há indicação de propedêutica armada adicional."
        ),
    },
    2: {  # Pneumonia Viral
        "icd_10": "J12.9 (Pneumonia viral não especificada)",
        "findings": (
            "Infiltrado intersticial difuso bilateral com acentuação da trama "
            "broncovascular parahilar e peribrônquica. Áreas tênues de atenuação em vidro "
            "fosco sem broncograma aéreo evidente. Volume pulmonar preservado. "
            "Pequeno espessamento peribrônquico."
        ),
        "impression": (
            "Achados radiológicos compatíveis com processo inflamatório/infeccioso de padrão "
            "intersticial, sugestivo de pneumonia de etiologia viral."
        ),
        "recommendations": (
            "Correlação com painel molecular respiratório viral e monitoramento de "
            "saturação periférica de O2."
        ),
    },
    3: {  # Pneumonia Bacteriana
        "icd_10": "J15.9 (Pneumonia bacteriana não especificada)",
        "findings": (
            "Consolidação alveolar densa e confluente com visualização de broncograma aéreo "
            "de permeio, acometendo segmento lobar pulmonar. Trama vascular periférica "
            "reduzida no leito acometido. Pequeno velamento reacional do seio costofrênico."
        ),
        "impression": (
            "Consolidação lobar alveolar com broncograma aéreo, padrão radiológico clássico "
            "compatível com pneumonia bacteriana aguda comunitária."
        ),
        "recommendations": (
            "Avaliação médica para início imediato de antibioticoterapia empírica direcionada. "
            "Controle radiológico pós-tratamento em 4 a 6 semanas."
        ),
    },
}

DEFAULT_DISCLAIMER = (
    "AVISO LEGAL / DECISION SUPPORT: Este laudo foi gerado por Inteligência Artificial Médica "
    "como ferramenta de triagem e suporte à decisão diagnóstica. Não substitui a avaliação "
    "clínica presencial nem o laudo definitivo emitido por um médico radiologista habilitado."
)


LABEL_TO_CLASS = {
    "covid-19": 0,
    "covid": 0,
    "normal": 1,
    "pneumonia viral": 2,
    "viral pneumonia": 2,
    "pneumonia bacteriana": 3,
    "bacterial pneumonia": 3,
}

# Pricing per 1,000,000 tokens (USD)
PRICING_TABLE = {
    "gemini-3.8-flash": {"prompt": 0.075 / 1_000_000, "completion": 0.30 / 1_000_000},
    "gemini-2.5-flash": {"prompt": 0.075 / 1_000_000, "completion": 0.30 / 1_000_000},
    "deepseek-v4-flash": {"prompt": 0.14 / 1_000_000, "completion": 0.28 / 1_000_000},
    "deepseek-v4-flash-free": {"prompt": 0.14 / 1_000_000, "completion": 0.28 / 1_000_000},
    "mimo-v2.5": {"prompt": 0.10 / 1_000_000, "completion": 0.20 / 1_000_000},
    "mimo-v2.5-free": {"prompt": 0.10 / 1_000_000, "completion": 0.20 / 1_000_000},
    "qwen-3.8-flash": {"prompt": 0.20 / 1_000_000, "completion": 0.60 / 1_000_000},
    "qwen3.8-flash": {"prompt": 0.20 / 1_000_000, "completion": 0.60 / 1_000_000},
    "gpt-5.6-luna": {"prompt": 0.50 / 1_000_000, "completion": 1.50 / 1_000_000},
    "gpt-6-astra": {"prompt": 0.50 / 1_000_000, "completion": 1.50 / 1_000_000},
    "deterministic-local": {"prompt": 0.0, "completion": 0.0},
}


def calculate_llm_cost(model_key: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated cost in USD based on standard token pricing."""
    pricing = PRICING_TABLE.get(model_key.lower().strip())
    if not pricing:
        pricing = {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000}
    cost = (prompt_tokens * pricing["prompt"]) + (completion_tokens * pricing["completion"])
    return round(cost, 6)


def _generate_deterministic_report(
    req: ReportRequest,
    fallback_reason: str | None = None,
    latency_ms: float = 0.0,
) -> ReportResponse:
    """Generate a high-standard deterministic clinical report based on ResNet50 prediction."""
    cid = req.predicted_class
    if req.override_label:
        norm = req.override_label.lower().strip()
        cid = LABEL_TO_CLASS.get(norm, cid)

    data = CLINICAL_KNOWLEDGE.get(cid, CLINICAL_KNOWLEDGE[1])

    tech = (
        "Radiografia de Tórax em incidência póstero-anterior (PA), realizada em ortostase "
        "com técnica digital."
    )
    if req.dicom_metadata:
        kvp = req.dicom_metadata.get("kvp", "N/A")
        pos = req.dicom_metadata.get("patient_position", "PA")
        tech = f"Radiografia Digital DICOM (CR/DX) em incidência {pos}, técnica ({kvp} kVp)."

    model_label = "Motor Clínico Local Determinístico (Offline)"
    if fallback_reason:
        model_label += f" — [Fallback: {fallback_reason}]"

    conf_pct = req.confidence * 100.0
    if req.override_label:
        impression_text = (
            f"{data['impression']} [SOBREESCRITA MÉDICA SOBERANA: {req.override_label}]."
        )
        if req.override_notes:
            impression_text += f" Justificativa clínica: {req.override_notes}."
    else:
        impression_text = f"{data['impression']} (Confiança estimada: {conf_pct:.1f}%)."

    telemetry = LLMTelemetry(
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        latency_ms=round(latency_ms, 2),
        estimated_cost_usd=0.0,
        fallback_triggered=bool(fallback_reason),
        fallback_reason=fallback_reason,
    )

    return ReportResponse(
        model_used=model_label,
        provider="Local Rule-Based Medical Engine",
        technique=tech,
        findings=data["findings"],
        impression=impression_text,
        icd_10=data["icd_10"],
        recommendations=data["recommendations"],
        disclaimer=DEFAULT_DISCLAIMER,
        generated_at=datetime.datetime.now(datetime.UTC),
        telemetry=telemetry,
    )


async def generate_medical_report(req: ReportRequest) -> ReportResponse:
    """Route report generation request to the selected LLM or local fallback engine."""
    t_start = time.perf_counter()
    model_choice = (req.model or "gemini-3.8-flash").lower().strip()

    # If local engine explicitly requested, return immediately
    if "local" in model_choice or "deterministic" in model_choice:
        rep = _generate_deterministic_report(
            req, latency_ms=(time.perf_counter() - t_start) * 1000.0
        )
        return rep

    # 1. Check intelligent in-memory cache
    cache_key = _get_cache_key(req, model_choice)
    if settings.llm_cache_enabled and cache_key in _REPORT_CACHE:
        cached_rep = _REPORT_CACHE[cache_key].model_copy(deep=True)
        if cached_rep.telemetry:
            cached_rep.telemetry.latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            cached_rep.telemetry.cached = True
        logger.info("llm_report_cache_hit", model=model_choice, key=cache_key[:8])
        return cached_rep

    # 2. Check FinOps daily quota cap before calling external APIs
    if not _check_and_increment_daily_quota(settings.llm_daily_quota):
        logger.warning("llm_daily_quota_reached", limit=settings.llm_daily_quota)
        return _generate_deterministic_report(
            req,
            fallback_reason=(
                f"Cota diária de demonstração pública atingida ({settings.llm_daily_quota} "
                "laudos/dia). Para controle de custos FinOps, o laudo foi gerado pelo "
                "Motor Clínico Local."
            ),
            latency_ms=(time.perf_counter() - t_start) * 1000.0,
        )

    # Prepare clinical prompt for all LLMs
    probs_info = ""
    if req.probs:
        probs_info = "Distribuição de Probabilidades: " + ", ".join(
            [f"{p.label}: {p.probability * 100:.1f}%" for p in req.probs]
        )

    system_prompt = (
        "Você é um médico radiologista torácico sênior emitindo um laudo radiológico "
        "formal e técnico.\n"
        "Estruture sua resposta EXATAMENTE com as seguintes seções em maiúsculas:\n"
        "TECNICA:\n"
        "ACHADOS:\n"
        "IMPRESSAO:\n"
        "CID_10:\n"
        "RECOMENDACOES:\n"
        "Não inclua saudações nem texto fora dessas seções."
    )

    effective_label = req.override_label or req.label
    user_prompt = (
        "Exame: Radiografia de Tórax Digital.\n"
        f"Diagnóstico Clínico Principal: {effective_label}.\n"
        f"Predição Neural Inicial: {req.label} "
        f"(Confiança Calibrada: {req.confidence * 100:.1f}%).\n"
        f"{probs_info}\n"
        f"Metadados Técnicos: {req.dicom_metadata or 'Radiografia Digital Convencional'}\n\n"
    )

    if req.override_label:
        user_prompt += (
            "[INTERVENÇÃO HUMANA / SOBREESCRITA DO MÉDICO RADIOLOGISTA]:\n"
            "O médico assistente revisou o exame e, por decisão clínica soberana presencial, "
            f"sobrescreveu o diagnóstico da IA de '{req.label}' para '{req.override_label}'.\n"
            f"Justificativa médica fornecida: "
            f"'{req.override_notes or 'Correlação clínico-laboratorial e propedêutica'}'.\n"
            f"Redija o laudo confirmando expressamente '{req.override_label}' com código CID-10 "
            "condizente, mencionando na discussão técnica a hipótese alternativa descartada no "
            "diagnóstico diferencial e orientando conduta.\n"
        )
    elif req.is_ambiguous:
        user_prompt += (
            "[ALERTA DE ALTA INCERTEZA / EMPATE TÉCNICO]:\n"
            "O exame apresenta distribuição de probabilidades muito próxima entre as hipóteses "
            "diagnósticas principais (margem estreita). "
            "Redija o laudo mantendo o DIAGNÓSTICO DIFERENCIAL ABERTO, descrevendo os achados "
            "radiológicos, e recomendando enfaticamente correlação com dosagem de Procalcitonina "
            "sérica (para diferenciação entre bacteriana e viral), PCR quantitativa e Painel "
            "Molecular Viral para confirmação antes de fechar a conduta terapêutica.\n"
        )
    else:
        user_prompt += (
            "Quadro do Paciente: O exame apresenta alterações radiológicas características de "
            f"{effective_label}.\n"
            "Como médico radiologista assistente, redija o laudo radiológico formal descrevendo "
            f"detalhadamente os achados pleuropulmonares condizentes com {effective_label}, "
            f"a impressão diagnóstica conclusiva confirmando {effective_label}, "
            "e o código CID-10 exato da patologia (exemplo: U07.1 para Covid-19, "
            "J15.9 para pneumonia bacteriana, J12.9 para pneumonia viral, "
            "Z00.0 para exame normal).\n"
        )

    # 1. Google Gemini 3.8 Flash / Gemini 2.5 Flash
    if "gemini" in model_choice:
        api_key = settings.gemini_api_key
        if not api_key:
            return _generate_deterministic_report(
                req,
                fallback_reason="GEMINI_API_KEY não configurada",
                latency_ms=(time.perf_counter() - t_start) * 1000.0,
            )
        t0 = time.perf_counter()
        try:
            base_gemini = "https://generativelanguage.googleapis.com/v1beta/models"
            url = f"{base_gemini}/gemini-2.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 3000,
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload)
                latency_ms = (time.perf_counter() - t0) * 1000.0
                if res.status_code == 200:
                    res_json = res.json()
                    raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    usage = res_json.get("usageMetadata", {})
                    p_tokens = usage.get("promptTokenCount", 0)
                    c_tokens = usage.get("candidatesTokenCount", 0)
                    t_tokens = usage.get("totalTokenCount", p_tokens + c_tokens)
                    cost = calculate_llm_cost("gemini-3.8-flash", p_tokens, c_tokens)

                    telemetry = LLMTelemetry(
                        prompt_tokens=p_tokens,
                        completion_tokens=c_tokens,
                        total_tokens=t_tokens,
                        latency_ms=round(latency_ms, 2),
                        estimated_cost_usd=cost,
                        fallback_triggered=False,
                    )
                    rep = _parse_llm_response(
                        raw_text,
                        model_name="Gemini 3.8 Flash",
                        provider="Google AI",
                        telemetry=telemetry,
                    )
                    if settings.llm_cache_enabled:
                        _store_in_cache(cache_key, rep)
                    return rep
                logger.warning("gemini_api_error", status_code=res.status_code, body=res.text)
                return _generate_deterministic_report(
                    req,
                    fallback_reason=f"Google API erro {res.status_code}",
                    latency_ms=latency_ms,
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            logger.error("gemini_exception", error=str(e))
            return _generate_deterministic_report(
                req,
                fallback_reason=f"Erro de conexão Gemini: {e}",
                latency_ms=latency_ms,
            )

    # 2. OpenCode Go (GPT 5.6 Luna, DeepSeek V4 Flash, Qwen 3.8 Flash)
    opencode_key = settings.opencode_api_key
    if not opencode_key:
        return _generate_deterministic_report(
            req,
            fallback_reason="OPENCODE_API_KEY não configurada",
            latency_ms=(time.perf_counter() - t_start) * 1000.0,
        )

    # Map model identifier to API target
    if "mimo" in model_choice:
        target_model = "mimo-v2.5-free"
        display_name = "Mimo-v2.5"
        endpoint_type = "chat"
    elif "gpt" in model_choice:
        target_model = "gpt-6-astra"
        display_name = "GPT 5.6 Luna"
        endpoint_type = "chat"
    elif "deepseek" in model_choice:
        target_model = "deepseek-v4-flash-free"
        display_name = "DeepSeek V4 Flash"
        endpoint_type = "chat"
    elif "qwen" in model_choice:
        target_model = "qwen3.8-flash"
        display_name = "Qwen 3.8 Flash"
        endpoint_type = "chat"
    else:
        target_model = model_choice
        display_name = model_choice
        endpoint_type = "chat"

    t0 = time.perf_counter()
    try:
        base_url = settings.opencode_base_url.rstrip("/")
        if "/zen/v1" not in base_url:
            if base_url.endswith("/v1"):
                base_url = base_url[:-3] + "/zen/v1"
            else:
                base_url = f"{base_url}/zen/v1"

        headers = {
            "Authorization": f"Bearer {opencode_key}",
            "Content-Type": "application/json",
        }

        if endpoint_type == "responses":
            url = f"{base_url}/responses"
            payload = {
                "model": target_model,
                "input": f"{system_prompt}\n\n{user_prompt}",
            }
        elif endpoint_type == "messages":
            url = f"{base_url}/messages"
            headers["x-api-key"] = opencode_key
            headers["anthropic-version"] = "2023-06-01"
            payload = {
                "model": target_model,
                "max_tokens": 800,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }
        else:
            url = f"{base_url}/chat/completions"
            payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 800,
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)

            # Se o modelo solicitado falhar (upstream ou cota avulsa), tenta mimo-v2.5-free
            if res.status_code != 200 and target_model != "mimo-v2.5-free":
                url_fallback = f"{base_url}/chat/completions"
                payload_fallback = {
                    "model": "mimo-v2.5-free",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 800,
                }
                res_fallback = await client.post(
                    url_fallback, headers=headers, json=payload_fallback
                )
                if res_fallback.status_code == 200:
                    res = res_fallback
                    display_name = f"{display_name} (via Mimo-v2.5)"
                    target_model = "mimo-v2.5-free"

            latency_ms = (time.perf_counter() - t0) * 1000.0

            if res.status_code == 200:
                data = res.json()
                if "choices" in data and len(data["choices"]) > 0:
                    raw_text = data["choices"][0]["message"]["content"]
                elif "output_text" in data:
                    raw_text = data["output_text"]
                elif "content" in data and isinstance(data["content"], list):
                    raw_text = data["content"][0].get("text", "")
                elif (
                    "output" in data
                    and isinstance(data["output"], list)
                    and len(data["output"]) > 0
                ):
                    raw_text = data["output"][0].get("content", [{}])[0].get("text", "")
                else:
                    raw_text = str(data)

                usage = data.get("usage", {})
                p_tokens = usage.get("prompt_tokens", 0)
                c_tokens = usage.get("completion_tokens", 0)
                t_tokens = usage.get("total_tokens", p_tokens + c_tokens)
                cost = calculate_llm_cost(target_model, p_tokens, c_tokens)

                telemetry = LLMTelemetry(
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    total_tokens=t_tokens,
                    latency_ms=round(latency_ms, 2),
                    estimated_cost_usd=cost,
                    fallback_triggered=False,
                )

                rep = _parse_llm_response(
                    raw_text,
                    model_name=display_name,
                    provider="OpenCode Go",
                    telemetry=telemetry,
                )
                if settings.llm_cache_enabled:
                    _store_in_cache(cache_key, rep)
                return rep
            logger.warning("opencode_api_error", status_code=res.status_code, body=res.text)
            return _generate_deterministic_report(
                req,
                fallback_reason=f"OpenCode Go erro {res.status_code}",
                latency_ms=latency_ms,
            )
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        logger.error("opencode_exception", error=str(e))
        return _generate_deterministic_report(
            req,
            fallback_reason=f"Erro de conexão OpenCode Go: {e}",
            latency_ms=latency_ms,
        )


def _parse_llm_response(
    raw_text: str,
    model_name: str,
    provider: str,
    telemetry: LLMTelemetry | None = None,
) -> ReportResponse:
    """Parse structured sections from the LLM completion."""
    sections: dict[str, str] = {
        "TECNICA": "",
        "ACHADOS": "",
        "IMPRESSAO": "",
        "CID_10": "",
        "RECOMENDACOES": "",
    }

    aliases = {
        "TECNICA": ["TECNICA", "TÉCNICA"],
        "ACHADOS": ["ACHADOS", "ACHADOS RADIOLÓGICOS", "ACHADOS RADIOLOGICOS"],
        "IMPRESSAO": ["IMPRESSAO", "IMPRESSÃO", "IMPRESSAO DIAGNOSTICA", "IMPRESSÃO DIAGNÓSTICA"],
        "CID_10": ["CID_10", "CID-10", "CID 10", "CLASSIFICAÇÃO CID-10", "CLASSIFICACAO CID-10"],
        "RECOMENDACOES": ["RECOMENDACOES", "RECOMENDAÇÕES", "CONDUTA"],
    }

    current_section = None
    for line in raw_text.splitlines():
        line_clean = line.strip()
        matched = False
        for sec, syns in aliases.items():
            for s in syns:
                prefixes = [f"{s}:", f"**{s}:**", f"**{s}**:", f"### {s}:", f"## {s}:", f"- {s}:"]
                if any(line_clean.upper().startswith(p) for p in prefixes):
                    current_section = sec
                    content = line_clean.split(":", 1)[1].strip(" *")
                    if content:
                        sections[sec] = content
                    matched = True
                    break
            if matched:
                break
        if not matched and current_section:
            if sections[current_section]:
                sections[current_section] += " " + line_clean
            else:
                sections[current_section] = line_clean

    return ReportResponse(
        model_used=model_name,
        provider=provider,
        technique=sections["TECNICA"] or "Radiografia de Tórax em projeção PA.",
        findings=sections["ACHADOS"] or raw_text[:300],
        impression=sections["IMPRESSAO"] or "Padrão avaliado por inteligência artificial.",
        icd_10=sections["CID_10"] or "Z00.0",
        recommendations=sections["RECOMENDACOES"] or "Correlação com dados clínicos.",
        disclaimer=DEFAULT_DISCLAIMER,
        generated_at=datetime.datetime.now(datetime.UTC),
        telemetry=telemetry,
    )
