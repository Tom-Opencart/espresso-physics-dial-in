#!/usr/bin/env python3
"""CLI-анализатор эспрессо. Только стандартная библиотека Python.

Расчетные величины Дарси являются оценкой на основе среднего потока.
Они не заменяют измеренный график давления/потока и не доказывают каналообразование.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Optional


def water_viscosity_pa_s(temp_c: float) -> float:
    """Приближение Вогеля для динамической вязкости чистой воды (Па·с).

    mu = 2.414e-5 * 10**(247.8/(T_kelvin - 140)).
    Использовать ориентировочно от 0 до 100 °C.
    """
    kelvin = temp_c + 273.15
    return 2.414e-5 * 10.0 ** (247.8 / (kelvin - 140.0))


def positive(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Ожидается число") from exc
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Значение должно быть конечным и > 0")
    return number


def nonnegative(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Ожидается число") from exc
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("Значение должно быть конечным и >= 0")
    return number


def next_step(taste: str, yield_g: float) -> Optional[str]:
    tokens = {token.strip().lower() for token in taste.replace(",", "+").split("+") if token.strip()}
    acidic = bool(tokens & {"sour", "acidic", "кислый", "кисло", "кислота"})
    dry = bool(tokens & {"dry", "astringent", "вяжущий", "сухой", "сушит"})
    bitter = bool(tokens & {"bitter", "горький", "горечь"})
    if acidic and dry:
        return "Для следующего шота попробуйте помол на 1 шаг крупнее; сохраните остальные параметры. Одного вкуса недостаточно для диагноза каналообразования."
    if bitter:
        return f"Для следующего шота попробуйте уменьшить выход до {max(1.0, yield_g - 4.0):.1f} г, оставив остальные параметры без изменений."
    if acidic:
        return f"Для следующего шота попробуйте увеличить выход до {yield_g + 4.0:.1f} г, оставив остальные параметры без изменений."
    return None


def analyze(args: argparse.Namespace) -> dict:
    if args.preinfusion >= args.time:
        raise ValueError("--preinfusion должно быть меньше --time")
    if not 0 <= args.temp <= 100:
        raise ValueError("--temp должен быть от 0 до 100 °C для используемой модели")
    if args.tds is not None and not 0 < args.tds < 100:
        raise ValueError("--tds должен быть между 0 и 100 (%)")

    viscosity = water_viscosity_pa_s(args.temp)
    ratio = args.yield_g / args.dose
    avg_flow = args.yield_g / args.time
    post_preinfusion_s = args.time - args.preinfusion
    flow_after_preinfusion = args.yield_g / post_preinfusion_s

    # Должны измеряться отдельно: плотность реального напитка и
    # распределение выхода по времени. Для индекса принято rho=1 г/мл.
    flow_ml_s_approx = avg_flow
    hydraulic_resistance = args.pressure * 1e5 / (flow_ml_s_approx * 1e-6)
    darcy_index = args.pressure / flow_ml_s_approx  # бар·с/мл

    permeability = None
    if args.puck_height_mm is not None:
        radius_m = args.basket_diameter_mm / 2000.0
        area_m2 = math.pi * radius_m**2
        height_m = args.puck_height_mm / 1000.0
        volume_flow_m3_s = flow_ml_s_approx * 1e-6
        permeability = (volume_flow_m3_s * viscosity * height_m) / (area_m2 * args.pressure * 1e5)

    return {
        "dose_g": args.dose,
        "yield_g": args.yield_g,
        "brew_ratio": ratio,
        "total_time_s": args.time,
        "preinfusion_s": args.preinfusion,
        "flow_total_g_s": avg_flow,
        "flow_after_preinfusion_g_s_assuming_zero_earlier": flow_after_preinfusion,
        "water_viscosity_mpa_s": viscosity * 1000.0,
        "darcy_pressure_flow_index_bar_s_ml": darcy_index,
        "hydraulic_resistance_pa_s_m3_approx": hydraulic_resistance,
        "permeability_m2_approx": permeability,
        "tds_percent": args.tds,
        "extraction_yield_percent": (args.yield_g * args.tds / args.dose) if args.tds is not None else None,
        "next_step": next_step(args.taste, args.yield_g),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Расчет эспрессо: Brew Ratio, EY при наличии TDS, вязкость воды и оценка сопротивления")
    p.add_argument("--dose", type=positive, required=True, help="Масса сухого кофе, г")
    p.add_argument("--yield_g", type=positive, required=True, help="Масса готового напитка, г")
    p.add_argument("--time", type=positive, required=True, help="Полное время шота, с")
    p.add_argument("--preinfusion", type=nonnegative, default=0.0, help="Время предсмачивания, с")
    p.add_argument("--pressure", type=positive, default=9.0, help="Условное среднее давление на таблетке, бар")
    p.add_argument("--temp", type=float, default=93.0, help="Температура воды, °C")
    p.add_argument("--taste", default="", help='Ощущения, например "sour+dry"')
    p.add_argument("--tds", type=float, help="Измеренная TDS напитка, %%")
    p.add_argument("--basket-diameter-mm", type=positive, default=58.0, help="Внутренний диаметр корзины, мм")
    p.add_argument("--puck-height-mm", type=positive, help="Толщина таблетки, мм; включает оценку проницаемости")
    p.add_argument("--json", action="store_true", help="Вывести машиночитаемый JSON")
    args = p.parse_args()
    try:
        out = analyze(args)
    except ValueError as exc:
        p.error(str(exc))

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print("=== Espresso Physics Dial-In: анализ шота ===")
    print(f"Доза / выход: {args.dose:.1f} / {args.yield_g:.1f} г | Brew Ratio 1:{out['brew_ratio']:.2f}")
    print(f"Время: {args.time:.1f} с (предсмачивание {args.preinfusion:.1f} с)")
    print(f"Средний выход: {out['flow_total_g_s']:.2f} г/с (включая предсмачивание)")
    print(f"Если до конца предсмачивания выход был нулевым: {out['flow_after_preinfusion_g_s_assuming_zero_earlier']:.2f} г/с")
    print(f"Вязкость чистой воды при {args.temp:.1f} °C: {out['water_viscosity_mpa_s']:.3f} мПа·с")
    print(f"Индекс ΔP/Q: {out['darcy_pressure_flow_index_bar_s_ml']:.3f} бар·с/мл")
    print(f"Оценка R_h: {out['hydraulic_resistance_pa_s_m3_approx']:.3e} Па·с/м³")
    if out["permeability_m2_approx"] is not None:
        print(f"Оценка проницаемости k: {out['permeability_m2_approx']:.3e} м²")
    if out["extraction_yield_percent"] is None:
        print("EY: не вычисляется без измеренной TDS; по времени, вкусу и выходу получить достоверную EY нельзя.")
    else:
        print(f"TDS: {args.tds:.2f}% | EY: {out['extraction_yield_percent']:.2f}%")
    if out["next_step"]:
        print(f"Следующий эксперимент: {out['next_step']}")
    print("Ограничение: среднее давление, плотность напитка≈1 г/мл и постоянная проницаемость — упрощения;")
    print("индекс и k не являются прямыми измерениями таблетки и не доказывают каналообразование.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
