// =============================================================================
// SNCEV App 2 — Servicio de Coberturas
// Consume el API REST de reportes: /reportes/cobertura, /tendencia, /rezago
// =============================================================================

import 'package:dio/dio.dart';

import '../config/app_config.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'auth_service.dart';

part 'cobertura_service.freezed.dart';
part 'cobertura_service.g.dart';

// ---------------------------------------------------------------------------
// Modelos de respuesta
// ---------------------------------------------------------------------------

@freezed
class CoberturaItem with _$CoberturaItem {
  const factory CoberturaItem({
    required String dimensionId,
    required String dimensionNombre,
    required String vacunaClave,
    required String vacunaNombre,
    required int numeroDosis,
    required int dosisAplicadas,
    required int poblacionObjetivo,
    required double coberturaPct,
    required double concordanciaPct,
    required int dosisInvalidas,
  }) = _CoberturaItem;

  factory CoberturaItem.fromJson(Map<String, dynamic> json) =>
      _$CoberturaItemFromJson(json);
}

@freezed
class TendenciaPunto with _$TendenciaPunto {
  const factory TendenciaPunto({
    required int anio,
    required int semana,
    required int dosisAplicadas,
    required int poblacionObjetivo,
    required double coberturaPct,
  }) = _TendenciaPunto;

  factory TendenciaPunto.fromJson(Map<String, dynamic> json) =>
      _$TendenciaPuntoFromJson(json);
}

@freezed
class PacienteRezago with _$PacienteRezago {
  const factory PacienteRezago({
    required String pacienteId,
    required String fechaNacimiento,
    required String vacuna,
    required String serie,
    required String fechaLimite,
    required int diasRezago,
    required String municipio,
  }) = _PacienteRezago;

  factory PacienteRezago.fromJson(Map<String, dynamic> json) =>
      _$PacienteRezagoFromJson(json);
}

// ---------------------------------------------------------------------------
// Filtros para queries
// ---------------------------------------------------------------------------

@freezed
class FiltrosCobertura with _$FiltrosCobertura {
  const factory FiltrosCobertura({
    int? vacunaId,
    int? numeroDosis,
    int? tipoCartillaId,
    String? estadoClave,
    int? jurisdiccionId,
    int? municipioId,
    required int anio,
    @Default(1)  int semanaDesde,
    @Default(52) int semanaHasta,
    @Default('estado') String dimension,  // ageb|municipio|jurisdiccion|estado|nacional
  }) = _FiltrosCobertura;
}

// ---------------------------------------------------------------------------
// Provider del servicio
// ---------------------------------------------------------------------------

@riverpod
CoberturaService coberturaService(Ref ref) => CoberturaService();

// ---------------------------------------------------------------------------
// Servicio
// ---------------------------------------------------------------------------

class CoberturaService {
  static const _baseUrl = AppConfig.baseUrl;
  final _storage = const FlutterSecureStorage();
  late final Dio _dio;

  CoberturaService() {
    _dio = Dio(BaseOptions(
      baseUrl:        _baseUrl,
      connectTimeout: const Duration(seconds: 20),
      receiveTimeout: const Duration(seconds: 60),
    ));
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        // El access token dura 15 minutos; ante un 401 intentamos renovarlo
        // una sola vez con el refresh token y reintentamos la petición original.
        final esNoAutorizado = error.response?.statusCode == 401;
        final yaReintentado = error.requestOptions.extra['_reintentado'] == true;
        if (esNoAutorizado && !yaReintentado) {
          final renovado = await AuthService().refresh();
          if (renovado) {
            final nuevoToken = await _storage.read(key: 'access_token');
            final opciones = error.requestOptions;
            opciones.extra['_reintentado'] = true;
            opciones.headers['Authorization'] = 'Bearer $nuevoToken';
            try {
              final respuesta = await _dio.fetch(opciones);
              return handler.resolve(respuesta);
            } on DioException catch (e) {
              return handler.next(e);
            }
          }
        }
        handler.next(error);
      },
    ));
  }

  // Datos de cobertura por dimensión (para tabla y mapa)
  Future<List<CoberturaItem>> obtenerCobertura(FiltrosCobertura filtros) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/reportes/cobertura',
      queryParameters: {
        if (filtros.vacunaId != null)       'vacuna_id':        filtros.vacunaId,
        if (filtros.numeroDosis != null)    'numero_dosis':     filtros.numeroDosis,
        if (filtros.tipoCartillaId != null) 'tipo_cartilla_id': filtros.tipoCartillaId,
        if (filtros.estadoClave != null)    'estado_clave':     filtros.estadoClave,
        if (filtros.jurisdiccionId != null) 'jurisdiccion_id':  filtros.jurisdiccionId,
        if (filtros.municipioId != null)    'municipio_id':     filtros.municipioId,
        'anio':          filtros.anio,
        'semana_desde':  filtros.semanaDesde,
        'semana_hasta':  filtros.semanaHasta,
        'dimension':     filtros.dimension,
      },
    );
    final datos = (response.data!['datos'] as List);
    return datos.map((d) => CoberturaItem.fromJson(d as Map<String, dynamic>)).toList();
  }

  // Serie temporal para gráfica de tendencia
  Future<List<TendenciaPunto>> obtenerTendencia({
    required int vacunaId,
    int? numeroDosis,
    String? estadoClave,
    required int anioDesde,
    required int anioHasta,
  }) async {
    final response = await _dio.get<List<dynamic>>(
      '/reportes/cobertura/tendencia',
      queryParameters: {
        'vacuna_id':    vacunaId,
        if (numeroDosis != null)  'numero_dosis': numeroDosis,
        if (estadoClave != null)  'estado_clave': estadoClave,
        'anio_desde':   anioDesde,
        'anio_hasta':   anioHasta,
      },
    );
    return (response.data as List)
        .map((d) => TendenciaPunto.fromJson(d as Map<String, dynamic>))
        .toList();
  }

  // Pacientes con rezago de vacunación
  Future<({List<PacienteRezago> datos, int total})> obtenerRezago({
    int? tipoCartillaId,
    int? vacunaId,
    int? municipioId,
    int diasRezago = 0,
    int pagina = 1,
    int porPagina = 30,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/reportes/rezago',
      queryParameters: {
        if (tipoCartillaId != null) 'tipo_cartilla_id': tipoCartillaId,
        if (vacunaId != null)       'vacuna_id':        vacunaId,
        if (municipioId != null)    'municipio_id':     municipioId,
        'dias_rezago': diasRezago,
        'page':        pagina,
        'per_page':    porPagina,
      },
    );
    final data  = response.data!;
    final items = (data['data'] as List)
        .map((d) => PacienteRezago.fromJson(d as Map<String, dynamic>))
        .toList();
    return (datos: items, total: data['total'] as int);
  }

  // Solicitar exportación asíncrona
  Future<String> solicitarExporte({
    required String tipo,
    required String formato,
    required Map<String, dynamic> filtros,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/reportes/exportar',
      data: {'tipo': tipo, 'formato': formato, 'filtros': filtros},
    );
    return response.data!['job_id'] as String;
  }

  // Consultar estado del job de exportación
  Future<Map<String, dynamic>> consultarExporte(String jobId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/reportes/exportar/$jobId',
    );
    return response.data!;
  }

  // Consultar el detalle de un lote (trazabilidad + alertas de cadena de frío)
  Future<Map<String, dynamic>> obtenerLote(String lote, {int? vacunaId}) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/reportes/lotes',
      queryParameters: {
        'lote': lote,
        if (vacunaId != null) 'vacuna_id': vacunaId,
      },
    );
    return response.data!;
  }
}
