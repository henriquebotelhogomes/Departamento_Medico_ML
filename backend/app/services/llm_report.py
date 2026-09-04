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

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.prediction import ReportRequest, ReportResponse

logger = get_logger(__name__)

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


def _generate_deterministic_report(
    req: ReportRequest, fallback_reason: str | None = None
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
    )


async def generate_medical_report(req: ReportRequest) -> ReportResponse:
    """Route report generation request to the selected LLM or local fallback engine."""
    model_choice = (req.model or "gemini-3.8-flash").lower().strip()

    # If local engine explicitly requested, return immediately
    if "local" in model_choice or "deterministic" in model_choice:
        return _generate_deterministic_report(req)

    # Prepare clinical prompt for all LLMs
    probs_info = ""
    if req.probs:
        probs_info = "Distribuição de Probabilidades: " + ", ".join(
            [f"{p.label}: {p.probability * 100:.1f}%" for p in req.probs]
        )

    system_prompt = (
        "Você é um médico radiologista torácico sênior emitindo um laudo radiológico formal e técnico.\n"
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
        f"Exame: Radiografia de Tórax Digital.\n"
        f"Diagnóstico Clínico Principal: {effective_label}.\n"
        f"Predição Neural Inicial: {req.label} (Confiança Calibrada: {req.confidence * 100:.1f}%).\n"
        f"{probs_info}\n"
        f"Metadados Técnicos: {req.dicom_metadata or 'Radiografia Digital Convencional'}\n\n"
    )

    if req.override_label:
        user_prompt += (
            f"[INTERVENÇÃO HUMANA / SOBREESCRITA DO MÉDICO RADIOLOGISTA]:\n"
            f"O médico assistente revisou o exame e, por decisão clínica soberana presencial, "
            f"sobrescreveu o diagnóstico da IA de '{req.label}' para '{req.override_label}'.\n"
            f"Justificativa médica fornecida: '{req.override_notes or 'Correlação clínico-laboratorial e propedêutica'}'.\n"
            f"Redija o laudo confirmando expressamente '{req.override_label}' com código CID-10 condizente, "
            f"mencionando na discussão técnica a hipótese alternativa descartada no diagnóstico diferencial e orientando conduta.\n"
        )
    elif req.is_ambiguous:
        user_prompt += (
            f"[ALERTA DE ALTA INCERTEZA / EMPATE TÉCNICO]:\n"
            f"O exame apresenta distribuição de probabilidades muito próxima entre as hipóteses diagnósticas principais (margem estreita). "
            f"Redija o laudo mantendo o DIAGNÓSTICO DIFERENCIAL ABERTO, descrevendo os achados radiológicos, "
            f"e recomendando enfaticamente correlação com dosagem de Procalcitonina sérica (para diferenciação entre bacteriana e viral), "
            f"PCR quantitativa e Painel Molecular Viral para confirmação antes de fechar a conduta terapêutica.\n"
        )
    else:
        user_prompt += (
            f"Quadro do Paciente: O exame apresenta alterações radiológicas características de {effective_label}.\n"
            f"Como médico radiologista assistente, redija o laudo radiológico formal descrevendo detalhadamente os "
            f"achados pleuropulmonares condizentes com {effective_label}, a impressão diagnóstica conclusiva confirmando {effective_label}, "
            f"e o código CID-10 exato da patologia (exemplo: U07.1 para Covid-19, J15.9 para pneumonia bacteriana, "
            f"J12.9 para pneumonia viral, Z00.0 para exame normal).\n"
        )

    # 1. Google Gemini 3.8 Flash / Gemini 2.5 Flash
    if "gemini" in model_choice:
        api_key = settings.gemini_api_key
        if not api_key:
            return _generate_deterministic_report(
                req, fallback_reason="GEMINI_API_KEY não configurada"
            )
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
                if res.status_code == 200:
                    raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return _parse_llm_response(
                        raw_text, model_name="Gemini 3.8 Flash", provider="Google AI"
                    )
                logger.warning("gemini_api_error", status_code=res.status_code, body=res.text)
                return _generate_deterministic_report(
                    req, fallback_reason=f"Google API erro {res.status_code}"
                )
        except Exception as e:
            logger.error("gemini_exception", error=str(e))
            return _generate_deterministic_report(
                req, fallback_reason=f"Erro de conexão Gemini: {e}"
            )

    # 2. OpenCode Go (GPT 5.6 Luna, DeepSeek V4 Flash, Qwen 3.8 Flash)
    opencode_key = settings.opencode_api_key
    if not opencode_key:
        return _generate_deterministic_report(
            req, fallback_reason="OPENCODE_API_KEY não configurada"
        )

    # Map model identifier to API target
    if "gpt" in model_choice:
        target_model = "gpt-5.6-luna"
        display_name = "GPT 5.6 Luna"
        endpoint_type = "responses"
    elif "deepseek" in model_choice:
        target_model = "deepseek-v4-flash"
        display_name = "DeepSeek V4 Flash"
        endpoint_type = "chat"
    elif "qwen" in model_choice:
        target_model = "qwen3.7-plus" if "plus" in model_choice else "qwen3.7-max"
        display_name = "Qwen 3.7 Plus"
        endpoint_type = "messages"
    else:
        target_model = model_choice
        display_name = model_choice
        endpoint_type = "chat"

    try:
        base_url = settings.opencode_base_url.rstrip("/")
        if not base_url.endswith("/zen/v1"):
            base_url = f"{base_url}/zen/v1" if "/zen" not in base_url else base_url

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

        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            
            # Se /responses retornar 404 para GPT, tenta fallback para /chat/completions
            if res.status_code == 404 and endpoint_type == "responses":
                url_fallback = f"{base_url}/chat/completions"
                payload_fallback = {
                    "model": target_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 800,
                }
                res = await client.post(url_fallback, headers=headers, json=payload_fallback)

            if res.status_code == 200:
                data = res.json()
                if "choices" in data and len(data["choices"]) > 0:
                    raw_text = data["choices"][0]["message"]["content"]
                elif "output_text" in data:
                    raw_text = data["output_text"]
                elif "content" in data and isinstance(data["content"], list):
                    raw_text = data["content"][0].get("text", "")
                elif "output" in data and isinstance(data["output"], list) and len(data["output"]) > 0:
                    raw_text = data["output"][0].get("content", [{}])[0].get("text", "")
                else:
                    raw_text = str(data)

                return _parse_llm_response(
                    raw_text, model_name=display_name, provider="OpenCode Go"
                )
            logger.warning("opencode_api_error", status_code=res.status_code, body=res.text)
            return _generate_deterministic_report(
                req, fallback_reason=f"OpenCode Go erro {res.status_code}"
            )
    except Exception as e:
        logger.error("opencode_exception", error=str(e))
        return _generate_deterministic_report(
            req, fallback_reason=f"Erro de conexão OpenCode Go: {e}"
        )


def _parse_llm_response(raw_text: str, model_name: str, provider: str) -> ReportResponse:
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
    )
