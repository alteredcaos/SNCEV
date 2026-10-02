// =============================================================================
// SNCEV App 2 — Pantalla de Rezago de Vacunación
// Tabla paginada de pacientes con dosis vencidas o fuera de plazo,
// con filtros por cartilla, vacuna y municipio.
// =============================================================================

import 'package:data_table_2/data_table_2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../services/cobertura_service.dart';
import '../widgets/semaforo_badge.dart';

part 'rezago_screen.g.dart';

// ---------------------------------------------------------------------------
// Estado y controlador
// ---------------------------------------------------------------------------

class RezagoFiltros {
  final int? tipoCartillaId;
  final int? vacunaId;
  final int? municipioId;
  final int diasRezago;
  final int pagina;
  final int porPagina;

  const RezagoFiltros({
    this.tipoCartillaId,
    this.vacunaId,
    this.municipioId,
    this.diasRezago = 0,
    this.pagina = 1,
    this.porPagina = 30,
  });

  RezagoFiltros copyWith({
    int? tipoCartillaId,
    int? vacunaId,
    int? municipioId,
    int? diasRezago,
    int? pagina,
    int? porPagina,
  }) => RezagoFiltros(
    tipoCartillaId: tipoCartillaId ?? this.tipoCartillaId,
    vacunaId:       vacunaId       ?? this.vacunaId,
    municipioId:    municipioId    ?? this.municipioId,
    diasRezago:     diasRezago     ?? this.diasRezago,
    pagina:         pagina         ?? this.pagina,
    porPagina:      porPagina      ?? this.porPagina,
  );
}

class RezagoState {
  final List<PacienteRezago> datos;
  final int total;
  final bool cargando;
  final RezagoFiltros filtros;
  final String? error;

  const RezagoState({
    this.datos = const [],
    this.total = 0,
    this.cargando = true,
    this.filtros = const RezagoFiltros(),
    this.error,
  });

  int get totalPaginas => (total / filtros.porPagina).ceil().clamp(1, 9999);

  RezagoState copyWith({
    List<PacienteRezago>? datos,
    int? total,
    bool? cargando,
    RezagoFiltros? filtros,
    String? error,
  }) => RezagoState(
    datos:    datos    ?? this.datos,
    total:    total    ?? this.total,
    cargando: cargando ?? this.cargando,
    filtros:  filtros  ?? this.filtros,
    error:    error,
  );
}

@riverpod
class RezagoController extends _$RezagoController {
  @override
  RezagoState build() {
    Future.microtask(cargar);
    return const RezagoState();
  }

  Future<void> cargar() async {
    state = state.copyWith(cargando: true, error: null);
    try {
      final service = ref.read(coberturaServiceProvider);
      final f = state.filtros;
      final result = await service.obtenerRezago(
        tipoCartillaId: f.tipoCartillaId,
        vacunaId:       f.vacunaId,
        municipioId:    f.municipioId,
        diasRezago:     f.diasRezago,
        pagina:         f.pagina,
        porPagina:      f.porPagina,
      );
      state = state.copyWith(
        datos:    result.datos,
        total:    result.total,
        cargando: false,
      );
    } catch (e) {
      state = state.copyWith(cargando: false, error: e.toString());
    }
  }

  void cambiarFiltros(RezagoFiltros nuevos) {
    state = state.copyWith(filtros: nuevos.copyWith(pagina: 1));
    cargar();
  }

  void irAPagina(int p) {
    state = state.copyWith(filtros: state.filtros.copyWith(pagina: p));
    cargar();
  }

  Future<void> exportar(BuildContext context) async {
    try {
      final service = ref.read(coberturaServiceProvider);
      final jobId = await service.solicitarExporte(
        tipo:    'rezago',
        formato: 'xlsx',
        filtros: {
          'tipo_cartilla_id': state.filtros.tipoCartillaId,
          'vacuna_id':        state.filtros.vacunaId,
          'dias_rezago':      state.filtros.diasRezago,
        },
      );
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Exportación iniciada (job: $jobId)')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al exportar: $e'),
              backgroundColor: const Color(0xFFA32D2D)),
        );
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Pantalla principal
// ---------------------------------------------------------------------------

class RezagoScreen extends ConsumerWidget {
  const RezagoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(rezagoControllerProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF5F3EE),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Row(children: [
          const Text('Rezago de vacunación',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
          const SizedBox(width: 10),
          if (!state.cargando)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: const Color(0xFFFCEBEB),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${NumberFormat.decimalPattern('es_MX').format(state.total)} casos',
                style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: Color(0xFFA32D2D)),
              ),
            ),
        ]),
        actions: [
          IconButton(
            icon: const Icon(Icons.download_outlined),
            tooltip: 'Exportar a Excel',
            onPressed: () =>
                ref.read(rezagoControllerProvider.notifier).exportar(context),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_outlined),
            onPressed: () =>
                ref.read(rezagoControllerProvider.notifier).cargar(),
          ),
        ],
      ),
      body: Column(children: [
        _FiltrosBar(state: state, ref: ref),
        Expanded(child: _Contenido(state: state)),
        _Paginacion(state: state, ref: ref),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// Barra de filtros
// ---------------------------------------------------------------------------

class _FiltrosBar extends StatelessWidget {
  final RezagoState state;
  final WidgetRef ref;
  const _FiltrosBar({required this.state, required this.ref});

  @override
  Widget build(BuildContext context) {
    final filtros = state.filtros;
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          _DropdownFiltro(
            label: 'Cartilla',
            valor: filtros.tipoCartillaId?.toString(),
            opciones: const {
              null: 'Todas',
              '1': 'Niña y niño',
              '2': 'Adolescente',
              '3': 'Mujer',
              '4': 'Adulto',
              '5': 'Adulto mayor',
            },
            onChange: (v) => ref
                .read(rezagoControllerProvider.notifier)
                .cambiarFiltros(filtros.copyWith(
                    tipoCartillaId: v == null ? null : int.parse(v))),
          ),
          _DropdownFiltro(
            label: 'Vacuna',
            valor: filtros.vacunaId?.toString(),
            opciones: const {
              null:  'Todas',
              '3':   'Pentavalente',
              '5':   'Neumocócica',
              '6':   'Triple viral SRP',
              '2':   'Hepatitis B',
            },
            onChange: (v) => ref
                .read(rezagoControllerProvider.notifier)
                .cambiarFiltros(filtros.copyWith(
                    vacunaId: v == null ? null : int.parse(v))),
          ),
          _DropdownFiltro(
            label: 'Días de rezago',
            valor: filtros.diasRezago.toString(),
            opciones: const {
              '0':  'Cualquier rezago',
              '7':  'Más de 7 días',
              '14': 'Más de 14 días',
              '30': 'Más de 30 días',
              '60': 'Más de 60 días',
            },
            onChange: (v) => ref
                .read(rezagoControllerProvider.notifier)
                .cambiarFiltros(
                    filtros.copyWith(diasRezago: int.parse(v ?? '0'))),
          ),
        ],
      ),
    );
  }
}

class _DropdownFiltro extends StatelessWidget {
  final String label;
  final String? valor;
  final Map<String?, String> opciones;
  final void Function(String?) onChange;

  const _DropdownFiltro({
    required this.label,
    required this.valor,
    required this.opciones,
    required this.onChange,
  });

  @override
  Widget build(BuildContext context) {
    return DropdownButton<String?>(
      value: valor,
      underline: const SizedBox.shrink(),
      style: const TextStyle(fontSize: 13, color: Color(0xFF2B2B28)),
      hint: Text(label,
          style: const TextStyle(fontSize: 13, color: Color(0xFF888780))),
      items: opciones.entries
          .map((e) => DropdownMenuItem(
                value: e.key,
                child: Text(e.value),
              ))
          .toList(),
      onChanged: onChange,
    );
  }
}

// ---------------------------------------------------------------------------
// Tabla de resultados
// ---------------------------------------------------------------------------

class _Contenido extends StatelessWidget {
  final RezagoState state;
  const _Contenido({required this.state});

  @override
  Widget build(BuildContext context) {
    if (state.cargando) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null) {
      return Center(child: Text('Error: ${state.error}'));
    }
    if (state.datos.isEmpty) {
      return const Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.check_circle_outline,
              size: 48, color: Color(0xFF1D9E75)),
          SizedBox(height: 12),
          Text('Sin pacientes en rezago para los filtros seleccionados',
              style: TextStyle(color: Color(0xFF888780))),
        ]),
      );
    }

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE1E0D9)),
        ),
        child: DataTable2(
          columnSpacing: 12,
          horizontalMargin: 16,
          headingRowColor:
              WidgetStateProperty.all(const Color(0xFFF5F3EE)),
          headingTextStyle: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w500,
            color: Color(0xFF52514E),
          ),
          dataTextStyle:
              const TextStyle(fontSize: 12, color: Color(0xFF2B2B28)),
          columns: const [
            DataColumn2(label: Text('PACIENTE'),   size: ColumnSize.L),
            DataColumn2(label: Text('VACUNA'),     size: ColumnSize.L),
            DataColumn2(label: Text('MUNICIPIO'),  size: ColumnSize.M),
            DataColumn2(label: Text('FECHA LÍMITE'), size: ColumnSize.S),
            DataColumn2(
                label: Text('DÍAS'),
                numeric: true,
                size: ColumnSize.S),
          ],
          rows: state.datos.map((r) => DataRow2(
            cells: [
              DataCell(Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(r.pacienteId,
                      style: const TextStyle(
                          fontSize: 12, fontWeight: FontWeight.w500)),
                  Text(r.fechaNacimiento,
                      style: const TextStyle(
                          fontSize: 11, color: Color(0xFF888780))),
                ],
              )),
              DataCell(Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(r.vacuna,
                      style: const TextStyle(fontSize: 12)),
                  Text(r.serie,
                      style: const TextStyle(
                          fontSize: 11, color: Color(0xFF888780))),
                ],
              )),
              DataCell(Text(r.municipio,
                  style: const TextStyle(color: Color(0xFF888780)))),
              DataCell(Text(r.fechaLimite)),
              DataCell(_DiasRezagoBadge(dias: r.diasRezago)),
            ],
          )).toList(),
        ),
      ),
    );
  }
}

class _DiasRezagoBadge extends StatelessWidget {
  final int dias;
  const _DiasRezagoBadge({required this.dias});

  @override
  Widget build(BuildContext context) {
    final Color color;
    final Color bg;
    if (dias >= 30) {
      color = const Color(0xFFA32D2D);
      bg    = const Color(0xFFFCEBEB);
    } else if (dias >= 14) {
      color = const Color(0xFF854F0B);
      bg    = const Color(0xFFFAEEDA);
    } else {
      color = const Color(0xFF52514E);
      bg    = const Color(0xFFF5F3EE);
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
          color: bg, borderRadius: BorderRadius.circular(10)),
      child: Text('$dias d',
          style: TextStyle(
              fontSize: 11, fontWeight: FontWeight.w500, color: color)),
    );
  }
}

// ---------------------------------------------------------------------------
// Paginación
// ---------------------------------------------------------------------------

class _Paginacion extends StatelessWidget {
  final RezagoState state;
  final WidgetRef ref;
  const _Paginacion({required this.state, required this.ref});

  @override
  Widget build(BuildContext context) {
    final p = state.filtros.pagina;
    final total = state.totalPaginas;

    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(children: [
        Text(
          'Página $p de $total · ${NumberFormat.decimalPattern('es_MX').format(state.total)} registros',
          style: const TextStyle(fontSize: 12, color: Color(0xFF888780)),
        ),
        const Spacer(),
        OutlinedButton(
          onPressed: p > 1
              ? () => ref
                  .read(rezagoControllerProvider.notifier)
                  .irAPagina(p - 1)
              : null,
          child: const Text('← Anterior'),
        ),
        const SizedBox(width: 8),
        OutlinedButton(
          onPressed: p < total
              ? () => ref
                  .read(rezagoControllerProvider.notifier)
                  .irAPagina(p + 1)
              : null,
          child: const Text('Siguiente →'),
        ),
      ]),
    );
  }
}
