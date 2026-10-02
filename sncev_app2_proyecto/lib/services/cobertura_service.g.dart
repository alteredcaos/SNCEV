// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cobertura_service.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_CoberturaItem _$CoberturaItemFromJson(Map<String, dynamic> json) =>
    _CoberturaItem(
      dimensionId: json['dimension_id'] as String,
      dimensionNombre: json['dimension_nombre'] as String,
      vacunaClave: json['vacuna_clave'] as String,
      vacunaNombre: json['vacuna_nombre'] as String,
      numeroDosis: (json['numero_dosis'] as num).toInt(),
      dosisAplicadas: (json['dosis_aplicadas'] as num).toInt(),
      poblacionObjetivo: (json['poblacion_objetivo'] as num).toInt(),
      coberturaPct: (json['cobertura_pct'] as num).toDouble(),
      concordanciaPct: (json['concordancia_pct'] as num).toDouble(),
      dosisInvalidas: (json['dosis_invalidas'] as num).toInt(),
    );

Map<String, dynamic> _$CoberturaItemToJson(_CoberturaItem instance) =>
    <String, dynamic>{
      'dimension_id': instance.dimensionId,
      'dimension_nombre': instance.dimensionNombre,
      'vacuna_clave': instance.vacunaClave,
      'vacuna_nombre': instance.vacunaNombre,
      'numero_dosis': instance.numeroDosis,
      'dosis_aplicadas': instance.dosisAplicadas,
      'poblacion_objetivo': instance.poblacionObjetivo,
      'cobertura_pct': instance.coberturaPct,
      'concordancia_pct': instance.concordanciaPct,
      'dosis_invalidas': instance.dosisInvalidas,
    };

_TendenciaPunto _$TendenciaPuntoFromJson(Map<String, dynamic> json) =>
    _TendenciaPunto(
      anio: (json['anio'] as num).toInt(),
      semana: (json['semana'] as num).toInt(),
      dosisAplicadas: (json['dosis_aplicadas'] as num).toInt(),
      poblacionObjetivo: (json['poblacion_objetivo'] as num).toInt(),
      coberturaPct: (json['cobertura_pct'] as num).toDouble(),
    );

Map<String, dynamic> _$TendenciaPuntoToJson(_TendenciaPunto instance) =>
    <String, dynamic>{
      'anio': instance.anio,
      'semana': instance.semana,
      'dosis_aplicadas': instance.dosisAplicadas,
      'poblacion_objetivo': instance.poblacionObjetivo,
      'cobertura_pct': instance.coberturaPct,
    };

_PacienteRezago _$PacienteRezagoFromJson(Map<String, dynamic> json) =>
    _PacienteRezago(
      pacienteId: json['paciente_id'] as String,
      fechaNacimiento: json['fecha_nacimiento'] as String,
      vacuna: json['vacuna'] as String,
      serie: json['serie'] as String,
      fechaLimite: json['fecha_limite'] as String,
      diasRezago: (json['dias_rezago'] as num).toInt(),
      municipio: json['municipio'] as String,
    );

Map<String, dynamic> _$PacienteRezagoToJson(_PacienteRezago instance) =>
    <String, dynamic>{
      'paciente_id': instance.pacienteId,
      'fecha_nacimiento': instance.fechaNacimiento,
      'vacuna': instance.vacuna,
      'serie': instance.serie,
      'fecha_limite': instance.fechaLimite,
      'dias_rezago': instance.diasRezago,
      'municipio': instance.municipio,
    };

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(coberturaService)
final coberturaServiceProvider = CoberturaServiceProvider._();

final class CoberturaServiceProvider
    extends
        $FunctionalProvider<
          CoberturaService,
          CoberturaService,
          CoberturaService
        >
    with $Provider<CoberturaService> {
  CoberturaServiceProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'coberturaServiceProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$coberturaServiceHash();

  @$internal
  @override
  $ProviderElement<CoberturaService> $createElement($ProviderPointer pointer) =>
      $ProviderElement(pointer);

  @override
  CoberturaService create(Ref ref) {
    return coberturaService(ref);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(CoberturaService value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<CoberturaService>(value),
    );
  }
}

String _$coberturaServiceHash() => r'd451e3a6d8153d7286f60a79f34f80800bb02535';
