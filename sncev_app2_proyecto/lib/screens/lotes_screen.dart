// =============================================================================
// SNCEV App 2 — Pantalla de Trazabilidad de Lotes
// Búsqueda por número de lote: unidades que lo usaron, temperaturas,
// fechas de aplicación y alertas de cadena de frío.
// =============================================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../services/cobertura_service.dart';

part 'lotes_screen.g.dart';

// ---------------------------------------------------------------------------
// Modelo de lote (responde al GET /reportes/lotes)
// ---------------------------------------------------------------------------

class LoteDetalle {
  final String lote;
  final String vacunaNombre;
  final String claveCensia;
  final int totalDosis;
  final String fechaPrimera;
  final String fechaUltima;
  final String? fechaCaducidad;
  final int alertas;
  final List<UnidadLote> unidades;

  const LoteDetalle({
    required this.lote,
    required this.vacunaNombre,
    required this.claveCensia,
    required this.totalDosis,
    required this.fechaPrimera,
    required this.fechaUltima,
    this.fechaCaducidad,
    required this.alertas,
    required this.unidades,
  });

  factory LoteDetalle.fromJson(Map<String, dynamic> j) => LoteDetalle(
    lote:           j['lote'] as String,
    vacunaNombre:   j['vacuna']['nombre_generico'] as String,
    claveCensia:    j['vacuna']['clave_censia'] as String,
    totalDosis:     j['total_dosis'] as int,
    fechaPrimera:   j['fecha_primera'] as String,
    fechaUltima:    j['fecha_ultima'] as String,
    fechaCaducidad: j['fecha_caducidad'] as String?,
    alertas:        j['alertas'] as int,
    unidades: (j['unidades'] as List)
        .map((u) => UnidadLote.fromJson(u as Map<String, dynamic>))
        .toList(),
  );
}

class UnidadLote {
  final String clues;
  final String nombre;
  final String municipio;
  final String estado;
  final int dosisAplicadas;
  final double? tempMin;
  final double? tempMax;

  const UnidadLote({
    required this.clues,
    required this.nombre,
    required this.municipio,
    required this.estado,
    required this.dosisAplicadas,
    this.tempMin,
    this.tempMax,
  });

  bool get tieneAlertaTemp =>
      (tempMin != null && tempMin! < 2) || (tempMax != null && tempMax! > 8);

  factory UnidadLote.fromJson(Map<String, dynamic> j) => UnidadLote(
    clues:          j['clues'] as String,
    nombre:         j['nombre'] as String,
    municipio:      j['municipio'] as String,
    estado:         j['estado'] as String,
    dosisAplicadas: j['dosis_aplicadas'] as int,
    tempMin:        (j['temp_min'] as num?)?.toDouble(),
    tempMax:        (j['temp_max'] as num?)?.toDouble(),
  );
}

// ---------------------------------------------------------------------------
// Estado y controlador
// ---------------------------------------------------------------------------

class LotesState {
  final String query;
  final LoteDetalle? resultado;
  final bool cargando;
  final String? error;
  final bool sinResultados;

  const LotesState({
    this.query = '',
    this.resultado,
    this.cargando = false,
    this.error,
    this.sinResultados = false,
  });
}

@riverpod
class LotesController extends _$LotesController {
  @override
  LotesState build() => const LotesState();

  Future<void> buscar(String lote) async {
    if (lote.trim().isEmpty) return;
    state = LotesState(query: lote, cargando: true);

    try {
      final service = ref.read(coberturaServiceProvider);
      final data = await service.obtenerLote(lote.trim());
      final detalle = LoteDetalle.fromJson(data);
      state = LotesState(query: lote, resultado: detalle);
    } on Exception catch (e) {
      if (e.toString().contains('404')) {
        state = LotesState(query: lote, sinResultados: true);
      } else {
        state = LotesState(query: lote, error: e.toString());
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Pantalla
// ---------------------------------------------------------------------------

class LotesScreen extends ConsumerStatefulWidget {
  const LotesScreen({super.key});

  @override
  ConsumerState<LotesScreen> createState() => _LotesScreenState();
}

class _LotesScreenState extends ConsumerState<LotesScreen> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(lotesControllerProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF5F3EE),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text('Trazabilidad de lotes',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
      ),
      body: Column(children: [
        _BarraBusqueda(controller: _controller, state: state, ref: ref),
        Expanded(child: _Contenido(state: state)),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// Barra de búsqueda
// ---------------------------------------------------------------------------

class _BarraBusqueda extends StatelessWidget {
  final TextEditingController controller;
  final LotesState state;
  final WidgetRef ref;

  const _BarraBusqueda({
    required this.controller,
    required this.state,
    required this.ref,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Row(children: [
        Expanded(
          child: TextField(
            controller: controller,
            style: const TextStyle(fontSize: 14),
            decoration: InputDecoration(
              hintText: 'Número de lote (ej. PT5601)',
              hintStyle: const TextStyle(color: Color(0xFF888780)),
              prefixIcon: const Icon(Icons.search, size: 20),
              suffixIcon: controller.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 18),
                      onPressed: () {
                        controller.clear();
                        ref.invalidate(lotesControllerProvider);
                      },
                    )
                  : null,
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8)),
              contentPadding: const EdgeInsets.symmetric(vertical: 10),
            ),
            textInputAction: TextInputAction.search,
            onSubmitted: (v) =>
                ref.read(lotesControllerProvider.notifier).buscar(v),
          ),
        ),
        const SizedBox(width: 10),
        FilledButton(
          onPressed: state.cargando
              ? null
              : () => ref
                  .read(lotesControllerProvider.notifier)
                  .buscar(controller.text),
          child: state.cargando
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white))
              : const Text('Buscar'),
        ),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// Contenido según estado
// ---------------------------------------------------------------------------

class _Contenido extends StatelessWidget {
  final LotesState state;
  const _Contenido({required this.state});

  @override
  Widget build(BuildContext context) {
    if (state.cargando) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null) {
      return _ErrorView(mensaje: state.error!);
    }
    if (state.sinResultados) {
      return _SinResultados(lote: state.query);
    }
    if (state.resultado == null) {
      return _EstadoInicial();
    }
    return _ResultadoDetalle(lote: state.resultado!);
  }
}

class _EstadoInicial extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: const [
      Icon(Icons.qr_code_scanner_outlined,
          size: 56, color: Color(0xFFC3C2B7)),
      SizedBox(height: 12),
      Text('Ingresa un número de lote para rastrear su uso',
          style: TextStyle(color: Color(0xFF888780))),
      SizedBox(height: 4),
      Text('Puedes escanear el código de barras del biológico',
          style: TextStyle(fontSize: 12, color: Color(0xFF888780))),
    ]),
  );
}

class _SinResultados extends StatelessWidget {
  final String lote;
  const _SinResultados({required this.lote});

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.search_off_outlined,
          size: 48, color: Color(0xFFC3C2B7)),
      const SizedBox(height: 12),
      Text('Lote "$lote" no encontrado',
          style: const TextStyle(fontWeight: FontWeight.w500)),
      const SizedBox(height: 4),
      const Text('Verifica el número e intenta de nuevo',
          style: TextStyle(fontSize: 12, color: Color(0xFF888780))),
    ]),
  );
}

class _ErrorView extends StatelessWidget {
  final String mensaje;
  const _ErrorView({required this.mensaje});

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.error_outline,
          size: 48, color: Color(0xFFA32D2D)),
      const SizedBox(height: 12),
      Text(mensaje, style: const TextStyle(color: Color(0xFF888780)),
          textAlign: TextAlign.center),
    ]),
  );
}

// ---------------------------------------------------------------------------
// Detalle del lote encontrado
// ---------------------------------------------------------------------------

class _ResultadoDetalle extends StatelessWidget {
  final LoteDetalle lote;
  const _ResultadoDetalle({required this.lote});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Tarjeta de resumen
        _TarjetaResumen(lote: lote),
        const SizedBox(height: 12),

        // Alerta de cadena de frío si aplica
        if (lote.alertas > 0) ...[
          _AlertaCadenaFrio(alertas: lote.alertas),
          const SizedBox(height: 12),
        ],

        // Estado de cadena de frío OK
        if (lote.alertas == 0) ...[
          _CadenaFrioOk(),
          const SizedBox(height: 12),
        ],

        // Lista de unidades
        _SeccionUnidades(unidades: lote.unidades),
      ],
    );
  }
}

class _TarjetaResumen extends StatelessWidget {
  final LoteDetalle lote;
  const _TarjetaResumen({required this.lote});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE1E0D9)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Lote ${lote.lote}',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w500)),
              const SizedBox(height: 2),
              Text(lote.vacunaNombre,
                  style: const TextStyle(
                      fontSize: 13, color: Color(0xFF888780))),
              Text('Clave CENSIA: ${lote.claveCensia}',
                  style: const TextStyle(
                      fontSize: 11, color: Color(0xFF888780))),
            ],
          )),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: lote.alertas > 0
                  ? const Color(0xFFFCEBEB)
                  : const Color(0xFFE8F6F0),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              lote.alertas > 0 ? '${lote.alertas} alertas' : 'Sin alertas',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: lote.alertas > 0
                    ? const Color(0xFFA32D2D)
                    : const Color(0xFF0F6E56),
              ),
            ),
          ),
        ]),
        const Divider(height: 20),
        _FilaDetalle(label: 'Total de dosis',
            valor: '${lote.totalDosis.toString()} dosis en ${lote.unidades.length} unidades'),
        _FilaDetalle(label: 'Primera aplicación', valor: lote.fechaPrimera),
        _FilaDetalle(label: 'Última aplicación',  valor: lote.fechaUltima),
        if (lote.fechaCaducidad != null)
          _FilaDetalle(label: 'Fecha de caducidad', valor: lote.fechaCaducidad!),
      ]),
    );
  }
}

class _FilaDetalle extends StatelessWidget {
  final String label;
  final String valor;
  const _FilaDetalle({required this.label, required this.valor});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style: const TextStyle(
                fontSize: 12, color: Color(0xFF888780))),
        Text(valor,
            style: const TextStyle(
                fontSize: 12, fontWeight: FontWeight.w500)),
      ],
    ),
  );
}

class _CadenaFrioOk extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
    decoration: BoxDecoration(
      color: const Color(0xFFE8F6F0),
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: const Color(0xFF9FE1CB)),
    ),
    padding: const EdgeInsets.all(12),
    child: Row(children: const [
      Icon(Icons.check_circle_outline,
          color: Color(0xFF0F6E56), size: 18),
      SizedBox(width: 10),
      Expanded(
        child: Text(
          'Cadena de frío íntegra en todas las unidades. Ninguna dosis registrada fuera del rango 2–8 °C.',
          style: TextStyle(fontSize: 12, color: Color(0xFF0F6E56)),
        ),
      ),
    ]),
  );
}

class _AlertaCadenaFrio extends StatelessWidget {
  final int alertas;
  const _AlertaCadenaFrio({required this.alertas});

  @override
  Widget build(BuildContext context) => Container(
    decoration: BoxDecoration(
      color: const Color(0xFFFCEBEB),
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: const Color(0xFFF09595)),
    ),
    padding: const EdgeInsets.all(12),
    child: Row(children: [
      const Icon(Icons.warning_amber_outlined,
          color: Color(0xFFA32D2D), size: 18),
      const SizedBox(width: 10),
      Expanded(
        child: Text(
          '$alertas ${alertas == 1 ? 'unidad registró' : 'unidades registraron'} temperatura fuera del rango 2–8 °C. Revisa las unidades marcadas en rojo.',
          style: const TextStyle(
              fontSize: 12, color: Color(0xFFA32D2D)),
        ),
      ),
    ]),
  );
}

class _SeccionUnidades extends StatelessWidget {
  final List<UnidadLote> unidades;
  const _SeccionUnidades({required this.unidades});

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Unidades médicas que utilizaron este lote',
          style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: Color(0xFF52514E))),
      const SizedBox(height: 10),
      ...unidades.map((u) => _TarjetaUnidad(unidad: u)),
    ]);
  }
}

class _TarjetaUnidad extends StatelessWidget {
  final UnidadLote unidad;
  const _TarjetaUnidad({required this.unidad});

  @override
  Widget build(BuildContext context) {
    final alerta = unidad.tieneAlertaTemp;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: alerta
              ? const Color(0xFFF09595)
              : const Color(0xFFE1E0D9),
        ),
      ),
      padding: const EdgeInsets.all(12),
      child: Row(children: [
        Icon(
          Icons.local_hospital_outlined,
          size: 20,
          color: alerta
              ? const Color(0xFFA32D2D)
              : const Color(0xFF888780),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(unidad.nombre,
                  style: const TextStyle(
                      fontSize: 13, fontWeight: FontWeight.w500)),
              Text('${unidad.municipio}, ${unidad.estado} · '
                  'CLUES: ${unidad.clues}',
                  style: const TextStyle(
                      fontSize: 11, color: Color(0xFF888780))),
              const SizedBox(height: 4),
              Row(children: [
                _ChipTemp(
                    label: 'Mín',
                    valor: unidad.tempMin,
                    alerta: unidad.tempMin != null && unidad.tempMin! < 2),
                const SizedBox(width: 6),
                _ChipTemp(
                    label: 'Máx',
                    valor: unidad.tempMax,
                    alerta: unidad.tempMax != null && unidad.tempMax! > 8),
              ]),
            ],
          ),
        ),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('${unidad.dosisAplicadas}',
              style: const TextStyle(
                  fontSize: 16, fontWeight: FontWeight.w500)),
          const Text('dosis',
              style: TextStyle(fontSize: 11, color: Color(0xFF888780))),
        ]),
      ]),
    );
  }
}

class _ChipTemp extends StatelessWidget {
  final String label;
  final double? valor;
  final bool alerta;
  const _ChipTemp(
      {required this.label, required this.valor, required this.alerta});

  @override
  Widget build(BuildContext context) {
    if (valor == null) return const SizedBox.shrink();
    final color = alerta ? const Color(0xFFA32D2D) : const Color(0xFF0F6E56);
    final bg    = alerta ? const Color(0xFFFCEBEB) : const Color(0xFFE8F6F0);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration:
          BoxDecoration(color: bg, borderRadius: BorderRadius.circular(6)),
      child: Text('$label: ${valor!.toStringAsFixed(1)} °C',
          style: TextStyle(
              fontSize: 10, fontWeight: FontWeight.w500, color: color)),
    );
  }
}
