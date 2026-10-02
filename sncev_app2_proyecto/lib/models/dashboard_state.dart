// =============================================================================
// SNCEV App 2 — Estado del dashboard (Freezed)
// =============================================================================

import 'package:freezed_annotation/freezed_annotation.dart';

import '../services/cobertura_service.dart';

part 'dashboard_state.freezed.dart';

@freezed
abstract class DashboardState with _$DashboardState {
  const factory DashboardState({
    required FiltrosCobertura filtros,
    @Default([]) List<CoberturaItem> items,
    @Default([]) List<TendenciaPunto> tendencia,
    @Default(true)  bool cargando,
    DateTime? ultimaActualizacion,
  }) = _DashboardState;

  factory DashboardState.inicial() => DashboardState(
    filtros: FiltrosCobertura(anio: DateTime.now().year),
  );
}
