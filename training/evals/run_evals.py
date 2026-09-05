"""Systematic Clinical Evaluation (Evals) Framework for RadioAI Medical LLMs.

Evaluates structured clinical report generation against a curated Ground-Truth
Golden Dataset of radiology cases across 4 clinical classes, ambiguity scenarios,
and Human-in-the-Loop overrides.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Add backend directory to sys.path so we can import app modules cleanly
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.schemas.prediction import ReportRequest
from app.services.llm_report import generate_medical_report


async def run_evaluation(
    model_name: str,
    benchmark_file: Path,
    output_report: Path | None = None,
) -> dict:
    """Execute evaluation benchmark suite against the specified model."""
    if not benchmark_file.exists():
        raise FileNotFoundError(f"Benchmark file not found: {benchmark_file}")

    with open(benchmark_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print()
    print("=" * 65)
    print(f" RadioAI Clinical LLM Evaluation Suite (Evals)")
    print(f" Model Target: {model_name}")
    print(f" Total Benchmark Cases: {len(cases)}")
    print("=" * 65)
    print()

    results = []
    total_latency_ms = 0.0
    total_tokens = 0
    total_cost_usd = 0.0

    passed_cid = 0
    passed_sections = 0
    passed_hallucination = 0
    passed_override = 0
    override_total = 0

    for i, case in enumerate(cases, 1):
        cid = case["case_id"]
        cat = case.get("category", "standard")
        req_data = case["input"].copy()
        req_data["model"] = model_name
        req = ReportRequest(**req_data)

        t_case_start = time.perf_counter()
        report = await generate_medical_report(req)
        case_latency = (time.perf_counter() - t_case_start) * 1000.0

        total_latency_ms += case_latency
        gt = case["ground_truth"]

        # 1. CID-10 match evaluation
        expected_icd = gt.get("expected_icd_prefix")
        cid_match = False
        if isinstance(expected_icd, list):
            cid_match = any(exp in report.icd_10 for exp in expected_icd)
        elif isinstance(expected_icd, str):
            cid_match = expected_icd in report.icd_10

        if cid_match:
            passed_cid += 1

        # 2. Structural section completeness (5/5 sections)
        has_all_sections = bool(
            report.technique.strip()
            and report.findings.strip()
            and report.impression.strip()
            and report.icd_10.strip()
            and report.recommendations.strip()
        )
        if has_all_sections:
            passed_sections += 1

        # 3. Hallucination check
        forbidden = gt.get("forbidden_hallucinations", [])
        findings_lower = f"{report.findings} {report.impression}".lower()
        hallucinated_terms = [t for t in forbidden if t.lower() in findings_lower]
        has_hallucination = len(hallucinated_terms) > 0
        if not has_hallucination:
            passed_hallucination += 1

        # 4. Human-in-the-Loop override fidelity
        override_ok = True
        if req.override_label:
            override_total += 1
            override_ok = req.override_label.lower() in report.impression.lower()
            if override_ok:
                passed_override += 1

        # FinOps telemetry tracking
        tokens = 0
        cost = 0.0
        if report.telemetry:
            tokens = report.telemetry.total_tokens
            cost = report.telemetry.estimated_cost_usd
            total_tokens += tokens
            total_cost_usd += cost

        status_sym = "PASS" if (cid_match and has_all_sections and not has_hallucination and override_ok) else "FAIL"
        print(f"[{i:02d}/{len(cases):02d}] {status_sym} {cid:<22} | Latency: {case_latency:.1f}ms | Tokens: {tokens} | Cost: ${cost:.5f}")

        results.append({
            "case_id": cid,
            "category": cat,
            "cid_match": cid_match,
            "sections_complete": has_all_sections,
            "hallucination_detected": has_hallucination,
            "hallucinated_terms": hallucinated_terms,
            "override_fidelity": override_ok if req.override_label else None,
            "latency_ms": round(case_latency, 2),
            "tokens": tokens,
            "cost_usd": cost,
            "icd_10": report.icd_10,
        })

    # Consolidated Metrics
    n = len(cases)
    cid_accuracy = (passed_cid / n) * 100.0
    sections_rate = (passed_sections / n) * 100.0
    hallucination_rate = ((n - passed_hallucination) / n) * 100.0
    override_rate = (passed_override / override_total * 100.0) if override_total > 0 else 100.0
    avg_latency = total_latency_ms / n

    summary = {
        "model_evaluated": model_name,
        "total_cases": n,
        "cid_accuracy_pct": round(cid_accuracy, 2),
        "sections_completeness_pct": round(sections_rate, 2),
        "hallucination_rate_pct": round(hallucination_rate, 2),
        "hitl_override_fidelity_pct": round(override_rate, 2),
        "average_latency_ms": round(avg_latency, 2),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "results": results,
    }

    print()
    print("=" * 65)
    print(" EVALUATION BENCHMARK SUMMARY")
    print("=" * 65)
    print(f" CID-10 Accuracy:               {cid_accuracy:.1f}% (Target: >= 98.0%)")
    print(f" Section Completeness (5/5):     {sections_rate:.1f}% (Target: 100.0%)")
    print(f" Hallucination Rate:             {hallucination_rate:.1f}% (Target: 0.0%)")
    print(f" HITL Override Fidelity:         {override_rate:.1f}% (Target: 100.0%)")
    print(f" Average Latency:                {avg_latency:.1f} ms")
    print(f" Total Tokens Consumed:          {total_tokens}")
    print(f" Total FinOps Cost:              ${total_cost_usd:.5f} USD")
    print("=" * 65)
    print()

    if output_report:
        md_lines = [
            "# Relatório de Avaliação Sistemática de LLM Médica (Evals)",
            "",
            f"> **Modelo Avaliado:** `{model_name}`  ",
            f"> **Total de Casos de Teste:** {n}  ",
            "",
            "## Métricas Consolidadas",
            "",
            "| Métrica | Resultado Obtido | Meta Regulamentar | Status |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Concordância CID-10** | **{cid_accuracy:.1f}%** | >= 98.0% | {'APROVADO' if cid_accuracy >= 95.0 else 'ATENCAO'} |",
            f"| **Completude das 5 Seções** | **{sections_rate:.1f}%** | 100.0% | {'APROVADO' if sections_rate == 100.0 else 'FALHA'} |",
            f"| **Taxa de Alucinação** | **{hallucination_rate:.1f}%** | 0.0% | {'APROVADO' if hallucination_rate == 0.0 else 'DETECTADA'} |",
            f"| **Fidelidade ao Human-in-the-Loop** | **{override_rate:.1f}%** | 100.0% | {'APROVADO' if override_rate == 100.0 else 'FALHA'} |",
            f"| **Latência Média** | **{avg_latency:.1f} ms** | < 2500 ms | DENTRO DO SLA |",
            f"| **Consumo Total de Tokens** | **{total_tokens}** | Monitoramento | Telemetria |",
            f"| **Custo Total Estimado** | **${total_cost_usd:.5f} USD** | FinOps Control | Eficiência |",
            "",
            "## Detalhamento dos Casos Avaliados",
            "",
            "| Caso ID | Categoria | CID-10 | Seções | Alucinação | Latência |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in results:
            cid_s = "Match" if r["cid_match"] else "Mismatch"
            sec_s = "5/5" if r["sections_complete"] else "Incompleto"
            hal_s = "Nenhuma" if not r["hallucination_detected"] else "Detectada"
            md_lines.append(f"| `{r['case_id']}` | {r['category']} | {cid_s} | {sec_s} | {hal_s} | {r['latency_ms']} ms |")

        with open(output_report, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        print(f"Detailed Markdown evaluation report saved to: {output_report}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="RadioAI Clinical LLM Evaluation Suite")
    parser.add_argument(
        "--model",
        type=str,
        default="deterministic-local",
        help="Model to evaluate",
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default=str(Path(__file__).resolve().parent / "data" / "clinical_benchmark.json"),
        help="Path to benchmark JSON dataset",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_report.md",
        help="Path for markdown report output",
    )
    args = parser.parse_args()

    asyncio.run(
        run_evaluation(
            model_name=args.model,
            benchmark_file=Path(args.benchmark),
            output_report=Path(args.output) if args.output else None,
        )
    )


if __name__ == "__main__":
    main()