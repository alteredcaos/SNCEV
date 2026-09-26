#!/usr/bin/env python3
# =============================================================================
# SNCEV Jobs — CLI para ejecución manual
#
# Uso:
#   python run_job.py cobertura                     # semana actual
#   python run_job.py cobertura --semana 25         # semana específica
#   python run_job.py cobertura --anio 2025 --desde 1 --hasta 52
#   python run_job.py cobertura --todo-el-anio
#   python run_job.py limpiar-tokens
#   python run_job.py rezago
# =============================================================================

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from common.db import inicializar_pool, cerrar_pool
from cobertura.worker import JobCobertura


def cmd_cobertura(args: argparse.Namespace) -> int:
    job = JobCobertura()
    resultado = job.ejecutar(
        anio=args.anio,
        semana_desde=args.desde,
        semana_hasta=args.hasta or args.desde,
        forzar_todo_anio=args.todo_el_anio,
    )
    print(f"\n{'='*50}")
    print(f"  Semanas procesadas : {resultado.semanas_procesadas}")
    print(f"  Semanas con error  : {resultado.semanas_error}")
    print(f"  Filas calculadas   : {resultado.filas_calculadas:,}")
    print(f"  Estados en alerta  : {resultado.estados_en_alerta}")
    print(f"  Duración           : {resultado.duracion_seg:.1f}s")
    print(f"  Resultado          : {'✓ OK' if resultado.exitoso else '✗ ERROR'}")
    if resultado.errores:
        print("\n  Errores:")
        for e in resultado.errores:
            print(f"    - {e}")
    print(f"{'='*50}\n")
    return 0 if resultado.exitoso else 1


def cmd_limpiar_tokens(args: argparse.Namespace) -> int:
    from scheduler import job_limpiar_refresh_tokens
    job_limpiar_refresh_tokens()
    return 0


def cmd_rezago(args: argparse.Namespace) -> int:
    from scheduler import job_detectar_rezago
    job_detectar_rezago()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SNCEV — Ejecución manual de jobs"
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # Subcomando: cobertura
    p_cob = subparsers.add_parser(
        "cobertura", help="Recalcular coberturas de vacunación"
    )
    p_cob.add_argument("--anio",         type=int,  default=None)
    p_cob.add_argument("--desde",        type=int,  default=None,
                       help="Semana epidemiológica de inicio")
    p_cob.add_argument("--hasta",        type=int,  default=None,
                       help="Semana epidemiológica de fin")
    p_cob.add_argument("--todo-el-anio", action="store_true",
                       help="Recalcular todas las semanas del año")
    p_cob.set_defaults(func=cmd_cobertura)

    # Subcomando: limpiar-tokens
    p_tok = subparsers.add_parser(
        "limpiar-tokens", help="Eliminar refresh tokens expirados"
    )
    p_tok.set_defaults(func=cmd_limpiar_tokens)

    # Subcomando: rezago
    p_rez = subparsers.add_parser(
        "rezago", help="Actualizar cache de rezago de vacunación"
    )
    p_rez.set_defaults(func=cmd_rezago)

    args = parser.parse_args()

    inicializar_pool(minconn=1, maxconn=3)
    try:
        codigo = args.func(args)
        sys.exit(codigo)
    finally:
        cerrar_pool()


if __name__ == "__main__":
    main()
