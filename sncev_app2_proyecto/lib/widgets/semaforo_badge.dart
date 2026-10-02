// =============================================================================
// SNCEV App 2 — Widget SemaforoBadge
// Verde ≥95%, Ámbar 80-94%, Rojo <80%
// =============================================================================

import 'package:flutter/material.dart';

class SemaforoBadge extends StatelessWidget {
  final double pct;
  const SemaforoBadge({super.key, required this.pct});

  @override
  Widget build(BuildContext context) {
    final Color bg;
    final Color fg;
    final String texto;

    if (pct >= 95) {
      bg = const Color(0xFFE8F6F0); fg = const Color(0xFF0F6E56); texto = 'Óptima';
    } else if (pct >= 80) {
      bg = const Color(0xFFFAEEDA); fg = const Color(0xFF854F0B); texto = 'Regular';
    } else {
      bg = const Color(0xFFFCEBEB); fg = const Color(0xFFA32D2D); texto = 'Alerta';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(texto, style: TextStyle(fontSize: 11, color: fg, fontWeight: FontWeight.w500)),
    );
  }
}
