// =============================================================================
// SNCEV App 2 — Dashboard de Cobertura
// Pantalla principal: KPIs, gráfica de tendencia, tabla por estado/municipio
// =============================================================================

import 'package:data_table_2/data_table_2.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/dashboard_state.dart';
import '../services/cobertura_service.dart';
import '../widgets/kpi_card.dart';
import '../widgets/semaforo_badge.dart';

part 'dashboard_cobertura_screen.g.dart';

// ---------------------------------------------------------------------------
// Provider del estado del dashboard
// ---------------------------------------------------------------------------

@riverpod
class DashboardController extends _$DashboardController {
  @override
  Future<DashboardState> build() async => _cargar(DashboardState.inicial());

  Future<DashboardState> _cargar(DashboardState estado) async {
    final service = ref.read(coberturaServiceProvider);

    final filtros = estado.filtros;

    final cobertura = await service.obtenerCobertura(filtros);
    final tendencia = await service.obtenerTendencia(
      vacunaId:   filtros.vacunaId ?? 1,
      anioDesde:  filtros.anio - 1,
      anioHasta:  filtros.anio,
    );

    return estado.copyWith(
      items:           cobertura,
      tendencia:        tendencia,
      cargando:         false,
      ultimaActualizacion: DateTime.now(),
    );
  }

  Future<void> aplicarFiltros(FiltrosCobertura nuevosFiltros) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _cargar(
      (state.value ?? DashboardState.inicial()).copyWith(
        filtros:  nuevosFiltros,
        cargando: true,
      ),
    ));
  }

  Future<void> refrescar() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() =>
        _cargar(state.value ?? DashboardState.inicial()));
  }
}

// ---------------------------------------------------------------------------
// Pantalla principal
// ---------------------------------------------------------------------------

class DashboardCoberturaScreen extends ConsumerWidget {
  const DashboardCoberturaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final estado = ref.watch(dashboardControllerProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF5F3EE),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'Coberturas de vacunación',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune_outlined),
            tooltip: 'Filtros',
            onPressed: () => _mostrarFiltros(context, ref),
          ),
          IconButton(
            icon: const Icon(Icons.download_outlined),
            tooltip: 'Exportar',
            onPressed: () => _exportar(context, ref),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_outlined),
            onPressed: () => ref.read(dashboardControllerProvider.notifier).refrescar(),
          ),
        ],
      ),
      body: estado.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error:   (e, _) => _ErrorView(mensaje: e.toString()),
        data:    (data) => _DashboardContent(data: data),
      ),
    );
  }

  void _mostrarFiltros(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => _FiltrosSheet(ref: ref),
    );
  }

  void _exportar(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (_) => _ExportDialog(ref: ref),
    );
  }
}

// ---------------------------------------------------------------------------
// Contenido principal del dashboard
// ---------------------------------------------------------------------------

class _DashboardContent extends StatelessWidget {
  final DashboardState data;
  const _DashboardContent({required this.data});

  @override
  Widget build(BuildContext context) {
    final items = data.items;
    if (items.isEmpty) {
      return const Center(child: Text('Sin datos para los filtros seleccionados'));
    }

    // KPIs agregados
    final totalDosis     = items.fold(0, (s, i) => s + i.dosisAplicadas);
    final totalPoblacion = items.fold(0, (s, i) => s + i.poblacionObjetivo);
    final coberturaGlobal = totalPoblacion > 0
        ? (totalDosis / totalPoblacion * 100)
        : 0.0;
    final enAlerta = items.where((i) => i.coberturaPct < 80).length;

    return RefreshIndicator(
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Chip de última actualización
          if (data.ultimaActualizacion != null)
            Text(
              'Actualizado ${DateFormat('dd/MM/yyyy HH:mm').format(data.ultimaActualizacion!)}',
              style: const TextStyle(fontSize: 12, color: Color(0xFF888780)),
            ),
          const SizedBox(height: 12),

          // --- KPIs ---
          Row(children: [
            Expanded(child: KpiCard(
              label:   'Cobertura global',
              valor:   '${coberturaGlobal.toStringAsFixed(1)}%',
              icono:   Icons.shield_outlined,
              color:   coberturaGlobal >= 95 ? const Color(0xFF1D9E75)
                       : coberturaGlobal >= 80 ? const Color(0xFFBA7517)
                       : const Color(0xFFBA1717),
            )),
            const SizedBox(width: 10),
            Expanded(child: KpiCard(
              label: 'Dosis aplicadas',
              valor: NumberFormat.compact(locale: 'es_MX').format(totalDosis),
              icono: Icons.vaccines_outlined,
              color: const Color(0xFF185FA5),
            )),
            const SizedBox(width: 10),
            Expanded(child: KpiCard(
              label: 'Unidades en alerta',
              valor: '$enAlerta',
              icono: Icons.warning_amber_outlined,
              color: enAlerta > 0 ? const Color(0xFFBA7517) : const Color(0xFF1D9E75),
            )),
          ]),
          const SizedBox(height: 20),

          // --- Gráfica de tendencia ---
          _TendenciaCard(tendencia: data.tendencia),
          const SizedBox(height: 20),

          // --- Tabla de cobertura por dimensión ---
          _TablaCobertura(items: items),
          const SizedBox(height: 20),

          // --- Semáforo de estados en alerta ---
          if (enAlerta > 0) _AlertasCard(items: items),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Gráfica de línea: tendencia semanal de cobertura
// ---------------------------------------------------------------------------

class _TendenciaCard extends StatelessWidget {
  final List<TendenciaPunto> tendencia;
  const _TendenciaCard({required this.tendencia});

  @override
  Widget build(BuildContext context) {
    if (tendencia.isEmpty) return const SizedBox.shrink();

    // Construir puntos para fl_chart
    final spots = tendencia.asMap().entries.map((e) =>
      FlSpot(e.key.toDouble(), e.value.coberturaPct),
    ).toList();

    final metaLinea = [
      FlSpot(0, 95),
      FlSpot((tendencia.length - 1).toDouble(), 95),
    ];

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE1E0D9)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Tendencia de cobertura',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 4),
          const Text(
            'Porcentaje semanal vs meta nacional 95%',
            style: TextStyle(fontSize: 12, color: Color(0xFF888780)),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 200,
            child: LineChart(
              LineChartData(
                minY: 0,
                maxY: 110,
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 20,
                  getDrawingHorizontalLine: (v) => const FlLine(
                    color: Color(0xFFE1E0D9),
                    strokeWidth: 1,
                  ),
                ),
                borderData: FlBorderData(
                  show: true,
                  border: const Border(
                    bottom: BorderSide(color: Color(0xFFC3C2B7)),
                    left:   BorderSide(color: Color(0xFFC3C2B7)),
                  ),
                ),
                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: 20,
                      reservedSize: 36,
                      getTitlesWidget: (v, _) => Text(
                        '${v.toInt()}%',
                        style: const TextStyle(fontSize: 11, color: Color(0xFF888780)),
                      ),
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: (tendencia.length / 6).ceilToDouble(),
                      getTitlesWidget: (v, _) {
                        final idx = v.toInt();
                        if (idx >= 0 && idx < tendencia.length) {
                          final p = tendencia[idx];
                          return Text(
                            'S${p.semana}',
                            style: const TextStyle(fontSize: 10, color: Color(0xFF888780)),
                          );
                        }
                        return const SizedBox.shrink();
                      },
                    ),
                  ),
                  topTitles:   const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                lineBarsData: [
                  // Línea de meta 95%
                  LineChartBarData(
                    spots:           metaLinea,
                    isCurved:        false,
                    color:           const Color(0xFFBA1717).withValues(alpha: 0.5),
                    barWidth:        1,
                    dashArray:       [6, 4],
                    dotData:         const FlDotData(show: false),
                    belowBarData:    BarAreaData(show: false),
                  ),
                  // Línea de cobertura real
                  LineChartBarData(
                    spots:        spots,
                    isCurved:     true,
                    color:        const Color(0xFF185FA5),
                    barWidth:     2,
                    dotData:      FlDotData(
                      show: true,
                      getDotPainter: (spot, _, __, ___) => FlDotCirclePainter(
                        radius:      3,
                        color:       const Color(0xFF185FA5),
                        strokeWidth: 2,
                        strokeColor: Colors.white,
                      ),
                    ),
                    belowBarData: BarAreaData(
                      show:  true,
                      color: const Color(0xFF185FA5).withValues(alpha: 0.08),
                    ),
                  ),
                ],
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    getTooltipColor: (_) => const Color(0xFF2B2B28),
                    getTooltipItems: (spots) => spots.map((s) => LineTooltipItem(
                      '${s.y.toStringAsFixed(1)}%',
                      const TextStyle(color: Colors.white, fontSize: 12),
                    )).toList(),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          // Leyenda manual
          Row(children: [
            _LegendItem(color: const Color(0xFF185FA5), label: 'Cobertura real'),
            const SizedBox(width: 16),
            _LegendItem(color: const Color(0xFFBA1717).withValues(alpha: 0.5), label: 'Meta 95%', dashed: true),
          ]),
        ],
      ),
    );
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;
  final bool dashed;
  const _LegendItem({required this.color, required this.label, this.dashed = false});

  @override
  Widget build(BuildContext context) => Row(children: [
    Container(width: 12, height: 3, color: color),
    const SizedBox(width: 6),
    Text(label, style: const TextStyle(fontSize: 11, color: Color(0xFF888780))),
  ]);
}

// ---------------------------------------------------------------------------
// Tabla de cobertura por dimensión
// ---------------------------------------------------------------------------

class _TablaCobertura extends StatelessWidget {
  final List<CoberturaItem> items;
  const _TablaCobertura({required this.items});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE1E0D9)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 14, 16, 0),
            child: Text(
              'Cobertura por unidad',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
            ),
          ),
          SizedBox(
            height: 350,
            child: DataTable2(
              columnSpacing: 12,
              horizontalMargin: 16,
              headingRowColor: WidgetStateProperty.all(const Color(0xFFF5F3EE)),
              headingTextStyle: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: Color(0xFF52514E),
              ),
              dataTextStyle: const TextStyle(fontSize: 12, color: Color(0xFF2B2B28)),
              columns: const [
                DataColumn2(label: Text('Entidad'),   size: ColumnSize.L),
                DataColumn2(label: Text('Vacuna'),    size: ColumnSize.M),
                DataColumn2(label: Text('Dosis'), numeric: true, size: ColumnSize.S),
                DataColumn2(label: Text('Pob.'),  numeric: true, size: ColumnSize.S),
                DataColumn2(label: Text('Cob. %'), numeric: true, size: ColumnSize.S),
                DataColumn2(label: Text('Estado'), size: ColumnSize.S),
              ],
              rows: items.map((item) => DataRow2(
                cells: [
                  DataCell(Text(item.dimensionNombre, overflow: TextOverflow.ellipsis)),
                  DataCell(Text(item.vacunaNombre, overflow: TextOverflow.ellipsis)),
                  DataCell(Text(NumberFormat.compact(locale: 'es_MX').format(item.dosisAplicadas))),
                  DataCell(Text(NumberFormat.compact(locale: 'es_MX').format(item.poblacionObjetivo))),
                  DataCell(Text('${item.coberturaPct.toStringAsFixed(1)}%')),
                  DataCell(SemaforoBadge(pct: item.coberturaPct)),
                ],
              )).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Alertas — estados/municipios por debajo del umbral
// ---------------------------------------------------------------------------

class _AlertasCard extends StatelessWidget {
  final List<CoberturaItem> items;
  const _AlertasCard({required this.items});

  @override
  Widget build(BuildContext context) {
    final enAlerta = items.where((i) => i.coberturaPct < 80).toList()
      ..sort((a, b) => a.coberturaPct.compareTo(b.coberturaPct));

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFBE5E5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFF09595)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: const [
            Icon(Icons.warning_amber_outlined, color: Color(0xFFA32D2D), size: 18),
            SizedBox(width: 8),
            Text(
              'Entidades por debajo del 80%',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: Color(0xFFA32D2D),
              ),
            ),
          ]),
          const SizedBox(height: 12),
          ...enAlerta.take(5).map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(child: Text(
                  item.dimensionNombre,
                  style: const TextStyle(fontSize: 12, color: Color(0xFFA32D2D)),
                  overflow: TextOverflow.ellipsis,
                )),
                Text(
                  '${item.coberturaPct.toStringAsFixed(1)}%',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: Color(0xFFA32D2D),
                  ),
                ),
              ],
            ),
          )),
          if (enAlerta.length > 5)
            Text(
              '+ ${enAlerta.length - 5} más',
              style: const TextStyle(fontSize: 11, color: Color(0xFFA32D2D)),
            ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Bottom sheet de filtros
// ---------------------------------------------------------------------------

class _FiltrosSheet extends ConsumerStatefulWidget {
  final WidgetRef ref;
  const _FiltrosSheet({required this.ref});

  @override
  ConsumerState<_FiltrosSheet> createState() => _FiltrosSheetState();
}

class _FiltrosSheetState extends ConsumerState<_FiltrosSheet> {
  late FiltrosCobertura _filtros;

  @override
  void initState() {
    super.initState();
    _filtros = ref.read(dashboardControllerProvider).value?.filtros
        ?? DashboardState.inicial().filtros;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16, right: 16, top: 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Filtros', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _filtros.dimension,
            decoration: const InputDecoration(labelText: 'Agrupar por', border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: 'nacional',     child: Text('Nacional')),
              DropdownMenuItem(value: 'estado',       child: Text('Estado')),
              DropdownMenuItem(value: 'jurisdiccion', child: Text('Jurisdicción')),
              DropdownMenuItem(value: 'municipio',    child: Text('Municipio')),
            ],
            onChanged: (v) => setState(() => _filtros = _filtros.copyWith(dimension: v!)),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: DropdownButtonFormField<int>(
              value: _filtros.anio,
              decoration: const InputDecoration(labelText: 'Año', border: OutlineInputBorder()),
              items: [2024, 2025, 2026].map((a) =>
                DropdownMenuItem(value: a, child: Text('$a')),
              ).toList(),
              onChanged: (v) => setState(() => _filtros = _filtros.copyWith(anio: v!)),
            )),
            const SizedBox(width: 12),
            Expanded(child: DropdownButtonFormField<String>(
              value: null,
              hint: const Text('Todas'),
              decoration: const InputDecoration(labelText: 'Estado', border: OutlineInputBorder()),
              items: const [], // Se poblaría desde catálogo
              onChanged: (v) => setState(() =>
                _filtros = _filtros.copyWith(estadoClave: v)),
            )),
          ]),
          const SizedBox(height: 20),
          Row(children: [
            Expanded(child: OutlinedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            )),
            const SizedBox(width: 12),
            Expanded(child: FilledButton(
              onPressed: () {
                ref.read(dashboardControllerProvider.notifier).aplicarFiltros(_filtros);
                Navigator.pop(context);
              },
              child: const Text('Aplicar'),
            )),
          ]),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Diálogo de exportación
// ---------------------------------------------------------------------------

class _ExportDialog extends ConsumerStatefulWidget {
  final WidgetRef ref;
  const _ExportDialog({required this.ref});

  @override
  ConsumerState<_ExportDialog> createState() => _ExportDialogState();
}

class _ExportDialogState extends ConsumerState<_ExportDialog> {
  String _formato = 'xlsx';
  bool _exportando = false;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Exportar datos'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('Formato de exportación:', style: TextStyle(fontSize: 14)),
          const SizedBox(height: 12),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'xlsx', label: Text('Excel')),
              ButtonSegment(value: 'csv',  label: Text('CSV')),
            ],
            selected: {_formato},
            onSelectionChanged: (s) => setState(() => _formato = s.first),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: _exportando ? null : () async {
            setState(() => _exportando = true);
            try {
              final service  = ref.read(coberturaServiceProvider);
              final filtros  = ref.read(dashboardControllerProvider)
                  .value?.filtros ?? DashboardState.inicial().filtros;
              final jobId = await service.solicitarExporte(
                tipo:    'cobertura',
                formato: _formato,
                filtros: {
                  'anio':      filtros.anio,
                  'dimension': filtros.dimension,
                },
              );
              if (context.mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Exportación iniciada (job: $jobId). Recibirás una notificación.')),
                );
              }
            } finally {
              if (mounted) setState(() => _exportando = false);
            }
          },
          child: _exportando
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Exportar'),
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Vista de error
// ---------------------------------------------------------------------------

class _ErrorView extends StatelessWidget {
  final String mensaje;
  const _ErrorView({required this.mensaje});

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.error_outline, size: 48, color: Color(0xFFBA1717)),
        const SizedBox(height: 12),
        Text(mensaje, textAlign: TextAlign.center),
      ],
    ),
  );
}
