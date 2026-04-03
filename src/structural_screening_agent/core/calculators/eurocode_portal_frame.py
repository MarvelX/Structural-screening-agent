from dataclasses import dataclass

from structural_screening_agent.core.calculators.base import (
    CalculationRow,
    PortalFrameScreeningResult,
    estimate_column_stability_sensitivity,
    estimate_primary_frame_reference_moment,
    estimate_rafter_deflection_sensitivity,
    resolve_controlling_path,
)
from structural_screening_agent.core.domain import PortalFrameScreeningCase


@dataclass(frozen=True)
class EurocodePortalFrameCalculator:
    standard: str = "eurocode"

    def calculate(self, case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
        added_load = case.pv_load.added_dead_load_kpa or 0.0
        spacing = case.secondary_members.purlin_spacing_m or 1.5
        tributary_load = added_load * spacing
        strength_ratio = round(tributary_load / 0.30, 2)
        deflection_ratio = round(tributary_load / 0.24, 2)
        span = case.geometry.span_m or 0.0
        bay_spacing = case.geometry.bay_spacing_m or 0.0
        eave_height = case.geometry.eave_height_m or 0.0
        primary_frame_line_load = round(added_load * bay_spacing, 2)
        primary_frame_added_moment = round(primary_frame_line_load * (span**2) / 8.0, 2) if span else 0.0
        primary_frame_column_added_moment = (
            round(primary_frame_line_load * span * eave_height / 4.0, 2)
            if span and eave_height
            else 0.0
        )
        rafter_reference_moment = estimate_primary_frame_reference_moment(
            case.primary_frame.rafter_section,
            standard="eurocode",
            steel_grade=case.primary_frame.steel_grade,
        )
        column_reference_moment = estimate_primary_frame_reference_moment(
            case.primary_frame.column_section,
            standard="eurocode",
            steel_grade=case.primary_frame.steel_grade,
        )
        rafter_ratio = (
            round(primary_frame_added_moment / rafter_reference_moment, 2)
            if rafter_reference_moment
            else None
        )
        column_ratio = (
            round(primary_frame_column_added_moment / column_reference_moment, 2)
            if column_reference_moment
            else None
        )
        rafter_deflection_sensitivity = estimate_rafter_deflection_sensitivity(
            line_load=primary_frame_line_load,
            span_m=span,
            rafter_reference_moment=rafter_reference_moment,
        )
        column_stability_sensitivity = estimate_column_stability_sensitivity(
            column_added_moment=primary_frame_column_added_moment,
            eave_height_m=eave_height,
            column_section=case.primary_frame.column_section,
            column_reference_moment=column_reference_moment,
        )
        primary_frame_ratio_candidates = {
            "rafter": rafter_ratio or 0.0,
            "column": column_ratio or 0.0,
        }
        governing_primary_member = max(primary_frame_ratio_candidates, key=primary_frame_ratio_candidates.get)
        primary_frame_ratio = primary_frame_ratio_candidates[governing_primary_member]
        governing_reference_moment = (
            rafter_reference_moment if governing_primary_member == "rafter" else column_reference_moment
        )
        controlling_component, controlling_path, governing_ratio = resolve_controlling_path(
            strength_ratio=strength_ratio,
            deflection_ratio=deflection_ratio,
            rafter_ratio=rafter_ratio,
            column_ratio=column_ratio,
        )
        conclusion_status = "formal_review_required" if governing_ratio >= 0.85 else "screening_pass"

        rows = [
            CalculationRow(
                row_id="purlin_strength_ratio",
                numeric_value=strength_ratio,
                value_text=f"{strength_ratio:.2f}",
                unit="dimensionless",
                label_en="Purlin strength ratio",
                label_zh="檩条强度比值",
                formula_en="R_purlin,str = (q_pv * s_purlin) / 0.30",
                formula_zh="R_檩条,强度 = (q_光伏 * s_檩条) / 0.30",
            ),
            CalculationRow(
                row_id="purlin_deflection_ratio",
                numeric_value=deflection_ratio,
                value_text=f"{deflection_ratio:.2f}",
                unit="dimensionless",
                label_en="Purlin deflection ratio",
                label_zh="檩条挠度比值",
                formula_en="R_purlin,defl = (q_pv * s_purlin) / 0.24",
                formula_zh="R_檩条,挠度 = (q_光伏 * s_檩条) / 0.24",
            ),
            CalculationRow(
                row_id="primary_frame_line_load",
                numeric_value=primary_frame_line_load,
                value_text=f"{primary_frame_line_load:.2f}",
                unit="kN/m",
                label_en="Primary-frame line load",
                label_zh="主门架附加线荷载",
                formula_en="w_frame = q_pv * s_bay",
                formula_zh="w_门架 = q_光伏 * s_柱距",
            ),
            CalculationRow(
                row_id="primary_frame_added_moment_proxy",
                numeric_value=primary_frame_added_moment,
                value_text=f"{primary_frame_added_moment:.2f}",
                unit="kN*m",
                label_en="Primary-frame added moment proxy",
                label_zh="主门架附加弯矩代理值",
                formula_en="M_add = w_frame * L^2 / 8",
                formula_zh="M_附加 = w_门架 * L^2 / 8",
            ),
            CalculationRow(
                row_id="primary_frame_column_added_moment_proxy",
                numeric_value=primary_frame_column_added_moment,
                value_text=f"{primary_frame_column_added_moment:.2f}",
                unit="kN*m",
                label_en="Primary-frame column added moment proxy",
                label_zh="主门架柱附加弯矩代理值",
                formula_en="M_col,add = w_frame * L * h_e / 4",
                formula_zh="M_柱,附加 = w_门架 * L * h_e / 4",
            ),
        ]
        if rafter_reference_moment is not None and rafter_ratio is not None:
            rows.extend(
                [
                    CalculationRow(
                        row_id="primary_frame_rafter_reference_moment_proxy",
                        numeric_value=rafter_reference_moment,
                        value_text=f"{rafter_reference_moment:.2f}",
                        unit="kN*m",
                        label_en="Primary-frame rafter reference moment proxy",
                        label_zh="主门架梁参考弯矩代理值",
                        formula_en="M_ref,rafter = (d_r * b_fr * t_fr / 3000) * (f_y / 345)",
                        formula_zh="M_参考,梁 = (d_梁 * b_f梁 * t_f梁 / 3000) * (f_y / 345)",
                    ),
                    CalculationRow(
                        row_id="primary_frame_rafter_screening_ratio",
                        numeric_value=rafter_ratio,
                        value_text=f"{rafter_ratio:.2f}",
                        unit="dimensionless",
                        label_en="Primary Frame Rafter Screening Ratio",
                        label_zh="主门架梁筛查比值",
                        formula_en="R_rafter = M_add / M_ref,rafter",
                        formula_zh="R_梁 = M_附加 / M_参考,梁",
                    ),
                ]
            )
            if rafter_deflection_sensitivity is not None:
                rows.append(
                    CalculationRow(
                        row_id="primary_frame_rafter_deflection_sensitivity",
                        numeric_value=rafter_deflection_sensitivity,
                        value_text=f"{rafter_deflection_sensitivity:.2f}",
                        unit="dimensionless",
                        label_en="Primary Frame Rafter Deflection Sensitivity",
                        label_zh="主门架梁挠度敏感性",
                        formula_en="S_rafter,defl = (w_frame * L^3 / M_ref,rafter) / 100",
                        formula_zh="S_梁,挠度 = (w_门架 * L^3 / M_参考,梁) / 100",
                    )
                )
        if column_reference_moment is not None and column_ratio is not None:
            rows.extend(
                [
                    CalculationRow(
                        row_id="primary_frame_column_reference_moment_proxy",
                        numeric_value=column_reference_moment,
                        value_text=f"{column_reference_moment:.2f}",
                        unit="kN*m",
                        label_en="Primary-frame column reference moment proxy",
                        label_zh="主门架柱参考弯矩代理值",
                        formula_en="M_ref,column = (d_c * b_fc * t_fc / 3000) * (f_y / 345)",
                        formula_zh="M_参考,柱 = (d_柱 * b_f柱 * t_f柱 / 3000) * (f_y / 345)",
                    ),
                    CalculationRow(
                        row_id="primary_frame_column_screening_ratio",
                        numeric_value=column_ratio,
                        value_text=f"{column_ratio:.2f}",
                        unit="dimensionless",
                        label_en="Primary Frame Column Screening Ratio",
                        label_zh="主门架柱筛查比值",
                        formula_en="R_column = M_add / M_ref,column",
                        formula_zh="R_柱 = M_附加 / M_参考,柱",
                    ),
                ]
            )
            if column_stability_sensitivity is not None:
                rows.append(
                    CalculationRow(
                        row_id="primary_frame_column_stability_sensitivity",
                        numeric_value=column_stability_sensitivity,
                        value_text=f"{column_stability_sensitivity:.2f}",
                        unit="dimensionless",
                        label_en="Primary Frame Column Stability Sensitivity",
                        label_zh="主门架柱稳定敏感性",
                        formula_en="S_column,stab = (R_column * h_e / d_column) / 10",
                        formula_zh="S_柱,稳定 = (R_柱 * h_e / d_柱) / 10",
                    )
                )
        if governing_reference_moment is not None:
            rows.extend(
                [
                    CalculationRow(
                        row_id="primary_frame_reference_moment_proxy",
                        numeric_value=governing_reference_moment,
                        value_text=f"{governing_reference_moment:.2f}",
                        unit="kN*m",
                        label_en="Primary-frame reference moment proxy",
                        label_zh="主门架参考弯矩代理值",
                        formula_en="M_ref = governing(M_ref,rafter, M_ref,column)",
                        formula_zh="M_参考 = 控制构件(M_参考,梁, M_参考,柱)",
                    ),
                    CalculationRow(
                        row_id="primary_frame_screening_ratio",
                        numeric_value=primary_frame_ratio,
                        value_text=f"{primary_frame_ratio:.2f}",
                        unit="dimensionless",
                        label_en="Primary Frame Screening Ratio",
                        label_zh="主门架筛查比值",
                        formula_en="R_frame = M_add / M_ref",
                        formula_zh="R_门架 = M_附加 / M_参考",
                    ),
                ]
            )
        return PortalFrameScreeningResult(
            conclusion_status=conclusion_status,
            screening_level=case.evidence.screening_level,
            code_path="eurocode",
            calculation_summary=(
                "Eurocode portal-frame first-pass screening based on purlin tributary load plus primary-frame rafter/column added-moment proxies."
            ),
            calculation_rows=rows,
            controlling_component=controlling_component,
            controlling_path=controlling_path,
            code_reference_ids=["eurocode_portal_frame_purlin_screening"],
        )
