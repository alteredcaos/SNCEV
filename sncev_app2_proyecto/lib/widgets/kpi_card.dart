// =============================================================================
// SNCEV App 2 — Widget KpiCard
// =============================================================================

import 'package:flutter/material.dart';

class KpiCard extends StatelessWidget {
  final String label;
  final String valor;
  final IconData icono;
  final Color color;

  const KpiCard({
    super.key,
    required this.label,
    required this.valor,
    required this.icono,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE1E0D9)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icono, size: 20, color: color),
          const SizedBox(height: 8),
          Text(
            valor,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w500,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: Color(0xFF888780)),
          ),
        ],
      ),
    );
  }
}
