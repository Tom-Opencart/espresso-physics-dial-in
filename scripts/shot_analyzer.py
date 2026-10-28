#!/usr/bin/env python3
"""Independent espresso shot calculator.

Not source code from Jonathan Gagné's book. Only measured quantities are
reported as observations. Water viscosity and Darcy resistance are OPTIONAL
engineering approximations; they are not conclusions attributed to the book.

Requires Python >= 3.8; uses the standard library only.
"""
from __future__ import annotations

import argparse
import json
import math


def finite_float(value: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Ожидается число.") from exc
    if not math.isfinite(result):
        raise argparse.ArgumentTypeError("Требуется конечное число.")
    return result


def positive(value: str) -> float:
    result = finite_float(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("Значение должно быть > 0.")
    return result


def nonnegative(value: str) -> float:
    result = finite_float(value)
    if result < 0:
        raise argparse.ArgumentTypeError("Значение должно быть >= 0.")
    return result


def viscosity_water_pa_s(temp_c: float) -> float:
    """Empirical Vogel approximation (pure water), not a citation to the book."""
    temperature_k = temp_c + 273.15
    return 2.414e-5 * 10.0 ** (247.8 / (temperature_k - 140.0))


def analyze(args: argparse.Namespace) -> dict:
    if args.preinfusion >= args.time:
        raise ValueError("Предсмачивание должно быть короче общего времени шота.")
    if not (0 <= args.temp <= 100):
        raise ValueError("Температура должна быть в диапазоне 0–100 °C.")
    if args.tds is not None and not (0 < args.tds < 100):
        raise ValueError("TDS должна быть в диапазоне (0, 100)%.")

    result = {
        "dose_g": args.dose,
        "beverage_mass_g": args.yield_g,
        "brew_ratio": args.yield_g / args.dose,
        "total_time_s": args.time,
        "preinfusion_s": args.preinfusion,
        "average_beverage_mass_flow_g_s": args.yield_g / args.time,
        "measured_tds_percent": args.tds,
        "extraction_yield_percent": (
            args.yield_g * args.tds / args.dose
            if args.tds is not None else None
        ),
        "taste_notes": args.taste or None,
        "water_viscosity_mpa_s_empirical": viscosity_water_pa_s(args.temp) * 1000,
        "darcy_estimate": None,
        "limitations": [
            "Время считается от начала включения помпы.",
            "Массовый выход г/с не тождественен объемному потоку мл/с.",
            "EY нельзя вычислить без измеренной TDS.",
            "Вкус и средний поток не доказывают каналообразование.",
        ],
    }

    if args.puck_flow_ml_s is not None:
        # Requested explicitly: observed volume flux through the puck, not
        # estimated from the beverage mass in the cup.
        pressure_pa = args.pressure * 1e5
        flow_m3_s = args.puck_flow_ml_s * 1e-6
        resistance = pressure_pa / flow_m3_s
        estimate = {
            "pressure_drop_bar_assumed": args.pressure,
            "measured_puck_flow_ml_s": args.puck_flow_ml_s,
            "hydraulic_resistance_pa_s_m3_approx": resistance,
            "empirical_sqrt_pressure_over_flow_bar_half_s_ml": (args.pressure ** 0.5) / args.puck_flow_ml_s,
            "empirical_pressure_power_065_over_flow_bar_065_s_ml": (args.pressure ** 0.65) / args.puck_flow_ml_s,
        }
        if args.puck_height_mm is not None:
            radius_m = args.basket_diameter_mm / 2000.0
            area_m2 = math.pi * radius_m * radius_m
            length_m = args.puck_height_mm / 1000.0
            viscosity_pa_s = viscosity_water_pa_s(args.temp)
            estimate["effective_permeability_m2_approx"] = (
                flow_m3_s * viscosity_pa_s * length_m / (area_m2 * pressure_pa)
            )
        result["darcy_estimate"] = estimate
        result["limitations"].append(
            "Показатели ΔP^0.5/Q и ΔP^0.65/Q обсуждаются на с. 87–88 книги Ганье "
            "как эмпирические нормировки; они имеют особые размерности и не являются проницаемостью. "
            "Расчет Дарси предполагает стационарный поток, однородную геометрию "
            "и что заданное давление действительно является перепадом на таблетке."
        )
    elif args.puck_height_mm is not None:
        result["limitations"].append(
            "Проницаемость не рассчитывается без --puck-flow-ml-s."
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Эспрессо: Ratio, средний массовый выход, EY по TDS; опциональные инженерные оценки."
    )
    parser.add_argument("--dose", type=positive, required=True, help="Доза кофе, г.")
    parser.add_argument("--yield_g", type=positive, required=True, help="Масса напитка, г.")
    parser.add_argument("--time", type=positive, required=True, help="Время от включения помпы, с.")
    parser.add_argument("--preinfusion", type=nonnegative, default=0.0, help="Предсмачивание, с.")
    parser.add_argument("--pressure", type=positive, default=9.0, help="Принятый перепад давления на таблетке, бар; только для опциональной модели.")
    parser.add_argument("--temp", type=finite_float, default=93.0, help="Температура для инженерной формулы вязкости, °C.")
    parser.add_argument("--taste", default="", help="Заметка о вкусе, не используется для доказательства каналов.")
    parser.add_argument("--tds", type=finite_float, help="TDS напитка, измеренная рефрактометром, %.")
    parser.add_argument("--puck-flow-ml-s", type=positive, help="Отдельно измеренный объемный поток через таблетку, мл/с.")
    parser.add_argument("--basket-diameter-mm", type=positive, default=58.0, help="Внутренний диаметр корзины, мм.")
    parser.add_argument("--puck-height-mm", type=positive, help="Толщина таблетки, мм.")
    parser.add_argument("--json", action="store_true", help="Машиночитаемый JSON.")
    args = parser.parse_args()

    try:
        out = analyze(args)
    except ValueError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print("=== Espresso Physics Dial-In (independent calculator) ===")
    print(f"Доза: {args.dose:.1f} г; напиток: {args.yield_g:.1f} г; Ratio 1:{out['brew_ratio']:.2f}")
    print(f"Время от включения помпы: {args.time:.1f} с; предсмачивание: {args.preinfusion:.1f} с")
    print(f"Средний массовый выход: {out['average_beverage_mass_flow_g_s']:.3f} г/с")
    if args.tds is None:
        print("EY: неизвестна; требуется измеренная TDS.")
    else:
        print(f"TDS: {args.tds:.2f}%; EY: {out['extraction_yield_percent']:.2f}%")
    print(f"Модельная вязкость чистой воды при {args.temp:.1f} °C: {out['water_viscosity_mpa_s_empirical']:.3f} мПа·с")
    if args.puck_flow_ml_s is None:
        print("Сопротивление Дарси: не рассчитывается без отдельно измеренного объемного потока через таблетку.")
    else:
        d = out["darcy_estimate"]
        print(f"Оценка гидравлического сопротивления (ΔP/Q): {d['hydraulic_resistance_pa_s_m3_approx']:.3e} Па·с/м³")
        print(f"Эмпирический индекс √ΔP/Q: {d['empirical_sqrt_pressure_over_flow_bar_half_s_ml']:.3f} бар^0.5·с/мл")
        print(f"Эмпирический индекс ΔP^0.65/Q: {d['empirical_pressure_power_065_over_flow_bar_065_s_ml']:.3f} бар^0.65·с/мл")
        if "effective_permeability_m2_approx" in d:
            print(f"Оценка эффективной проницаемости: {d['effective_permeability_m2_approx']:.3e} м²")
    if args.taste:
        print(f"Заметка о вкусе: {args.taste}")
    print("Ограничения: " + " ".join(out["limitations"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
