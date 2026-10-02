// =============================================================================
// SNCEV App 2 — Pantalla de Mapa de Cobertura
// Mapa coroplético por estado/municipio usando syncfusion_flutter_maps.
// Carga el GeoJSON oficial del INEGI desde el servidor propio
// (se sirve desde la misma infraestructura del API, no desde CDN externo).
// =============================================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:syncfusion_flutter_maps/maps.dart';
import '../config/app_config.dart';

import '../services/cobertura_service.dart';

part 'mapa_cobertura_screen.g.dart';

// ---------------------------------------------------------------------------
// Modelo de dato geográfico para el mapa
// ---------------------------------------------------------------------------

class DatoMapa {
  final String clave;        // clave INEGI del estado o municipio
  final String nombre;
  final double coberturaPct;
  final int dosisAplicadas;
  final int poblacionObjetivo;

  const DatoMapa({
    required this.clave,
    required this.nombre,
    required this.coberturaPct,
    required this.dosisAplicadas,
    required this.poblacionObjetivo,
  });

  Color get colorMapa {
    if (coberturaPct >= 95) return const Color(0xFF5DCAA5); // teal-400
    if (coberturaPct >= 90) return const Color(0xFF9FE1CB); // teal-200
    if (coberturaPct >= 80) return const Color(0xFFFAC775); // amber-100
    if (coberturaPct >= 70) return const Color(0xFFEF9F27); // amber-400
    return const Color(0xFFE24B4A);                          // red-400
  }
}

// ---------------------------------------------------------------------------
// Estado y controlador
// ---------------------------------------------------------------------------

class MapaState {
  final List<DatoMapa> datos;
  final bool cargando;
  final String nivel;          // 'estado' | 'municipio'
  final int? vacunaId;
  final int anio;
  final int semana;
  final DatoMapa? seleccionado;
  final String? error;

  const MapaState({
    this.datos = const [],
    this.cargando = true,
    this.nivel = 'estado',
    this.vacunaId,
    this.anio = 2026,
    this.semana = 26,
    this.seleccionado,
    this.error,
  });

  MapaState copyWith({
    List<DatoMapa>? datos,
    bool? cargando,
    String? nivel,
    int? vacunaId,
    int? anio,
    int? semana,
    DatoMapa? seleccionado,
    String? error,
  }) => MapaState(
    datos:        datos        ?? this.datos,
    cargando:     cargando     ?? this.cargando,
    nivel:        nivel        ?? this.nivel,
    vacunaId:     vacunaId     ?? this.vacunaId,
    anio:         anio         ?? this.anio,
    semana:       semana       ?? this.semana,
    seleccionado: seleccionado ?? this.seleccionado,
    error:        error,
  );
}

@riverpod
class MapaController extends _$MapaController {
  @override
  MapaState build() {
    Future.microtask(cargar);
    return const MapaState();
  }

  Future<void> cargar() async {
    state = state.copyWith(cargando: true, error: null, seleccionado: null);
    try {
      final service = ref.read(coberturaServiceProvider);
      // Obtener datos de cobertura para el mapa
      final items = await service.obtenerCobertura(FiltrosCobertura(
        vacunaId:  state.vacunaId,
        anio:      state.anio,
        semanaDesde: state.semana,
        semanaHasta: state.semana,
        dimension: state.nivel,
      ));

      final datos = items.map((i) => DatoMapa(
        clave:             i.dimensionId,
        nombre:            i.dimensionNombre,
        coberturaPct:      i.coberturaPct,
        dosisAplicadas:    i.dosisAplicadas,
        poblacionObjetivo: i.poblacionObjetivo,
      )).toList();

      state = state.copyWith(datos: datos, cargando: false);
    } catch (e) {
      state = state.copyWith(cargando: false, error: e.toString());
    }
  }

  void seleccionar(DatoMapa? dato) =>
      state = state.copyWith(seleccionado: dato);

  void cambiarNivel(String nivel) {
    state = state.copyWith(nivel: nivel);
    cargar();
  }

  void cambiarVacuna(int? vacunaId) {
    state = state.copyWith(vacunaId: vacunaId);
    cargar();
  }

  void cambiarSemana(int semana) {
    state = state.copyWith(semana: semana);
    cargar();
  }
}

// ---------------------------------------------------------------------------
// Pantalla principal
// ---------------------------------------------------------------------------

class MapaCoberturaScreen extends ConsumerWidget {
  const MapaCoberturaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mapaControllerProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF5F3EE),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text('Mapa de cobertura',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_outlined),
            onPressed: () =>
                ref.read(mapaControllerProvider.notifier).cargar(),
          ),
        ],
      ),
      body: Column(children: [
        _BarraControles(state: state, ref: ref),
        Expanded(
          child: state.cargando
              ? const Center(child: CircularProgressIndicator())
              : state.error != null
                  ? _ErrorView(mensaje: state.error!)
                  : _VistaConMapa(state: state, ref: ref),
        ),
        _Leyenda(),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// Controles superiores
// ---------------------------------------------------------------------------

class _BarraControles extends StatelessWidget {
  final MapaState state;
  final WidgetRef ref;
  const _BarraControles({required this.state, required this.ref});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Wrap(
        spacing: 10,
        runSpacing: 8,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          // Nivel geográfico
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'estado',     label: Text('Estado')),
              ButtonSegment(value: 'municipio',  label: Text('Municipio')),
            ],
            selected: {state.nivel},
            style: ButtonStyle(
              textStyle: WidgetStateProperty.all(
                  const TextStyle(fontSize: 12)),
            ),
            onSelectionChanged: (s) => ref
                .read(mapaControllerProvider.notifier)
                .cambiarNivel(s.first),
          ),
          // Vacuna
          DropdownButton<int?>(
            value: state.vacunaId,
            underline: const SizedBox.shrink(),
            hint: const Text('Todas las vacunas',
                style: TextStyle(fontSize: 13)),
            style: const TextStyle(
                fontSize: 13, color: Color(0xFF2B2B28)),
            items: const [
              DropdownMenuItem(value: null,  child: Text('Todas las vacunas')),
              DropdownMenuItem(value: 3,     child: Text('Pentavalente D1')),
              DropdownMenuItem(value: 5,     child: Text('Neumocócica D1')),
              DropdownMenuItem(value: 6,     child: Text('Triple viral SRP')),
              DropdownMenuItem(value: 1,     child: Text('BCG')),
            ],
            onChanged: (v) => ref
                .read(mapaControllerProvider.notifier)
                .cambiarVacuna(v),
          ),
          // Semana
          Row(mainAxisSize: MainAxisSize.min, children: [
            const Text('Sem. ',
                style: TextStyle(fontSize: 13, color: Color(0xFF888780))),
            SizedBox(
              width: 60,
              child: TextFormField(
                initialValue: state.semana.toString(),
                style: const TextStyle(fontSize: 13),
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  isDense: true,
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  border: OutlineInputBorder(),
                ),
                onFieldSubmitted: (v) {
                  final s = int.tryParse(v);
                  if (s != null && s >= 1 && s <= 53) {
                    ref
                        .read(mapaControllerProvider.notifier)
                        .cambiarSemana(s);
                  }
                },
              ),
            ),
          ]),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Vista del mapa + panel lateral
// ---------------------------------------------------------------------------

class _VistaConMapa extends StatelessWidget {
  final MapaState state;
  final WidgetRef ref;
  const _VistaConMapa({required this.state, required this.ref});

  @override
  Widget build(BuildContext context) {
    return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      // Mapa principal
      Expanded(
        flex: 3,
        child: _MapaWidget(state: state, ref: ref),
      ),
      // Panel lateral: detalle del seleccionado + ranking de alertas
      SizedBox(
        width: 220,
        child: _PanelLateral(state: state),
      ),
    ]);
  }
}

// ---------------------------------------------------------------------------
// Widget del mapa coroplético (Syncfusion)
// ---------------------------------------------------------------------------

class _MapaWidget extends StatefulWidget {
  final MapaState state;
  final WidgetRef ref;
  const _MapaWidget({required this.state, required this.ref});

  @override
  State<_MapaWidget> createState() => _MapaWidgetState();
}

class _MapaWidgetState extends State<_MapaWidget> {
  late MapShapeLayerController _mapController;

  @override
  void initState() {
    super.initState();
    _mapController = MapShapeLayerController();
  }

  @override
  void dispose() {
    _mapController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final datos = widget.state.datos;

    // Mapa de clave → DatoMapa para lookup rápido en el tooltip
    final mapaLookup = {for (final d in datos) d.clave: d};

    return Padding(
      padding: const EdgeInsets.all(12),
      child: SfMaps(
        layers: [
          MapShapeLayer(
            // GeoJSON servido desde el API propio (estados de México INEGI)
            // Endpoint: GET /static/geo/estados-mexico.json
            // El archivo GeoJSON debe tener una propiedad "CVE_ENT" (clave INEGI)
            source: MapShapeSource.network(
              '${AppConfig.baseUrl}/static/geo/estados-mexico.json',
              shapeDataField: 'CVE_ENT',
              dataCount: datos.length,
              primaryValueMapper: (i) => datos[i].clave,
              shapeColorValueMapper: (i) => datos[i].coberturaPct,
              shapeColorMappers: [
                // Rangos de color del semáforo epidemiológico
                const MapRangeColorMapper(
                    from: 0,
                    to: 79.99,
                    color: Color(0xFFE24B4A),
                    text: '< 80% (alerta)'),
                const MapRangeColorMapper(
                    from: 80,
                    to: 94.99,
                    color: Color(0xFFFAC775),
                    text: '80-94% (regular)'),
                const MapRangeColorMapper(
                    from: 95,
                    to: 110,
                    color: Color(0xFF5DCAA5),
                    text: '≥ 95% (óptima)'),
              ],
            ),
            controller: _mapController,
            strokeColor: Colors.white,
            strokeWidth: 0.8,
            // Tooltip al tocar un estado
            shapeTooltipBuilder: (context, index) {
              if (index >= datos.length) return const SizedBox.shrink();
              final d = datos[index];
              return Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF2B2B28),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(d.nombre,
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w500)),
                    const SizedBox(height: 4),
                    Text('Cobertura: ${d.coberturaPct.toStringAsFixed(1)}%',
                        style: const TextStyle(
                            color: Color(0xFFC3C2B7), fontSize: 12)),
                    Text(
                        'Dosis: ${_fmt(d.dosisAplicadas)} / ${_fmt(d.poblacionObjetivo)}',
                        style: const TextStyle(
                            color: Color(0xFFC3C2B7), fontSize: 12)),
                  ],
                ),
              );
            },
            onSelectionChanged: (index) {
              final ctrl = widget.ref.read(mapaControllerProvider.notifier);
              if (index >= 0 && index < datos.length) {
                ctrl.seleccionar(datos[index]);
              } else {
                ctrl.seleccionar(null);
              }
            },
            selectionSettings: const MapSelectionSettings(
              color: Color(0xFF185FA5),
              strokeColor: Colors.white,
              strokeWidth: 2,
            ),
            tooltipSettings: const MapTooltipSettings(
              color: Color(0xFF2B2B28),
            ),
          ),
        ],
      ),
    );
  }

  String _fmt(int n) => n >= 1000000
      ? '${(n / 1000000).toStringAsFixed(1)}M'
      : n >= 1000
          ? '${(n / 1000).toStringAsFixed(0)}k'
          : '$n';
}

// ---------------------------------------------------------------------------
// Panel lateral
// ---------------------------------------------------------------------------

class _PanelLateral extends StatelessWidget {
  final MapaState state;
  const _PanelLateral({required this.state});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(0, 12, 12, 0),
      child: Column(children: [
        // Detalle del estado seleccionado
        if (state.seleccionado != null) ...[
          _TarjetaSeleccionado(dato: state.seleccionado!),
          const SizedBox(height: 10),
        ],
        // Ranking de estados con menor cobertura
        _RankingAlertas(datos: state.datos),
      ]),
    );
  }
}

class _TarjetaSeleccionado extends StatelessWidget {
  final DatoMapa dato;
  const _TarjetaSeleccionado({required this.dato});

  @override
  Widget build(BuildContext context) {
    final s = _semaforo(dato.coberturaPct);
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE1E0D9)),
      ),
      padding: const EdgeInsets.all(12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(dato.nombre,
            style: const TextStyle(
                fontSize: 14, fontWeight: FontWeight.w500)),
        const SizedBox(height: 8),
        Row(children: [
          Text('${dato.coberturaPct.toStringAsFixed(1)}%',
              style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w500,
                  color: s.color)),
          const Spacer(),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
                color: s.bg, borderRadius: BorderRadius.circular(10)),
            child: Text(s.label,
                style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: s.color)),
          ),
        ]),
        const SizedBox(height: 6),
        Text(
            'Dosis: ${_fmtN(dato.dosisAplicadas)} / '
            '${_fmtN(dato.poblacionObjetivo)}',
            style: const TextStyle(
                fontSize: 11, color: Color(0xFF888780))),
        const SizedBox(height: 8),
        // Barra de progreso
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: (dato.coberturaPct / 100).clamp(0.0, 1.0),
            minHeight: 6,
            backgroundColor: const Color(0xFFF5F3EE),
            valueColor: AlwaysStoppedAnimation(s.color),
          ),
        ),
      ]),
    );
  }

  String _fmtN(int n) => n >= 1000000
      ? '${(n / 1000000).toStringAsFixed(1)}M'
      : n >= 1000
          ? '${(n / 1000).toStringAsFixed(0)}k'
          : '$n';
}

class _RankingAlertas extends StatelessWidget {
  final List<DatoMapa> datos;
  const _RankingAlertas({required this.datos});

  @override
  Widget build(BuildContext context) {
    final enAlerta = datos
        .where((d) => d.coberturaPct < 80)
        .toList()
      ..sort((a, b) => a.coberturaPct.compareTo(b.coberturaPct));

    if (enAlerta.isEmpty) {
      return Container(
        decoration: BoxDecoration(
          color: const Color(0xFFE8F6F0),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF9FE1CB)),
        ),
        padding: const EdgeInsets.all(12),
        child: Row(children: const [
          Icon(Icons.check_circle_outline,
              color: Color(0xFF0F6E56), size: 18),
          SizedBox(width: 8),
          Expanded(
            child: Text('Todos los estados superan el 80%',
                style: TextStyle(
                    fontSize: 12, color: Color(0xFF0F6E56))),
          ),
        ]),
      );
    }

    return Expanded(
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE1E0D9)),
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.warning_amber_outlined,
                  size: 14, color: Color(0xFFA32D2D)),
              const SizedBox(width: 4),
              Text('${enAlerta.length} en alerta',
                  style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: Color(0xFFA32D2D))),
            ]),
            const SizedBox(height: 10),
            Expanded(
              child: ListView.separated(
                itemCount: enAlerta.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (_, i) {
                  final d = enAlerta[i];
                  return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    Row(children: [
                      Expanded(
                        child: Text(d.nombre,
                            style: const TextStyle(
                                fontSize: 11,
                                color: Color(0xFF2B2B28))),
                      ),
                      Text(
                          '${d.coberturaPct.toStringAsFixed(1)}%',
                          style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                              color: Color(0xFFA32D2D))),
                    ]),
                    const SizedBox(height: 3),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(3),
                      child: LinearProgressIndicator(
                        value: d.coberturaPct / 100,
                        minHeight: 4,
                        backgroundColor: const Color(0xFFF5F3EE),
                        valueColor: const AlwaysStoppedAnimation(
                            Color(0xFFE24B4A)),
                      ),
                    ),
                  ]);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Leyenda del mapa
// ---------------------------------------------------------------------------

class _Leyenda extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: const [
          _ItemLeyenda(color: Color(0xFFE24B4A), label: '< 80% (alerta)'),
          SizedBox(width: 16),
          _ItemLeyenda(color: Color(0xFFEF9F27), label: '70-79%'),
          SizedBox(width: 16),
          _ItemLeyenda(color: Color(0xFFFAC775), label: '80-94% (regular)'),
          SizedBox(width: 16),
          _ItemLeyenda(color: Color(0xFF9FE1CB), label: '90-94%'),
          SizedBox(width: 16),
          _ItemLeyenda(color: Color(0xFF5DCAA5), label: '≥ 95% (óptima)'),
        ],
      ),
    );
  }
}

class _ItemLeyenda extends StatelessWidget {
  final Color color;
  final String label;
  const _ItemLeyenda({required this.color, required this.label});

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
              color: color, borderRadius: BorderRadius.circular(2))),
      const SizedBox(width: 5),
      Text(label,
          style: const TextStyle(fontSize: 11, color: Color(0xFF888780))),
    ],
  );
}

// ---------------------------------------------------------------------------
// Vista de error
// ---------------------------------------------------------------------------

class _ErrorView extends StatelessWidget {
  final String mensaje;
  const _ErrorView({required this.mensaje});

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.error_outline, size: 48, color: Color(0xFFA32D2D)),
      const SizedBox(height: 12),
      Text(mensaje,
          textAlign: TextAlign.center,
          style: const TextStyle(color: Color(0xFF888780))),
    ]),
  );
}

// ---------------------------------------------------------------------------
// Helpers locales
// ---------------------------------------------------------------------------

({Color color, Color bg, String label}) _semaforo(double pct) {
  if (pct >= 95) {
    return (
      color: const Color(0xFF0F6E56),
      bg:    const Color(0xFFE8F6F0),
      label: 'Óptima'
    );
  } else if (pct >= 80) {
    return (
      color: const Color(0xFF854F0B),
      bg:    const Color(0xFFFAEEDA),
      label: 'Regular'
    );
  } else {
    return (
      color: const Color(0xFFA32D2D),
      bg:    const Color(0xFFFCEBEB),
      label: 'Alerta'
    );
  }
}
