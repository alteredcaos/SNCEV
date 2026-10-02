// =============================================================================
// SNCEV App 2 — Servicio de autenticación
//
// Flujo:
//   1. login(username, password)
//        -> TokenResponse directo (roles sin MFA obligatorio), o
//        -> MfaRequerido (roles nivel >= 4): hay que completar el paso 2.
//   2. Si mfaEnrolamiento es true, primero enrollStart() + enrollConfirm(codigo);
//      si es false, verifyMfa(codigo) directamente con el session_token del paso 1.
//   3. Los tokens quedan en flutter_secure_storage bajo las claves 'access_token'
//      y 'refresh_token', que es justo lo que CoberturaService ya lee.
//   4. El access token dura 15 minutos: refreshIfNeeded()/el interceptor de
//      CoberturaService deben llamar a refresh() ante un 401.
// =============================================================================

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config/app_config.dart';

class UsuarioSesion {
  final String id;
  final String username;
  final String rol;
  final int nivel;
  final List<String> permisos;

  UsuarioSesion({
    required this.id,
    required this.username,
    required this.rol,
    required this.nivel,
    required this.permisos,
  });

  factory UsuarioSesion.fromJson(Map<String, dynamic> j) => UsuarioSesion(
        id: j['id'] as String,
        username: j['username'] as String,
        rol: j['rol'] as String,
        nivel: j['nivel'] as int,
        permisos: (j['permisos'] as List).cast<String>(),
      );
}

/// Resultado de login() o de completar el desafío MFA.
sealed class LoginResultado {}

class LoginExitoso extends LoginResultado {
  final UsuarioSesion usuario;
  LoginExitoso(this.usuario);
}

class MfaRequerido extends LoginResultado {
  final String sessionToken;
  final bool enrolamiento;
  MfaRequerido({required this.sessionToken, required this.enrolamiento});
}

class AuthException implements Exception {
  final String mensaje;
  AuthException(this.mensaje);
  @override
  String toString() => mensaje;
}

class AuthService {
  final _storage = const FlutterSecureStorage();
  late final Dio _dio;

  AuthService()
      : _dio = Dio(BaseOptions(
          baseUrl: AppConfig.baseUrl,
          connectTimeout: const Duration(seconds: 20),
          receiveTimeout: const Duration(seconds: 30),
        ));

  String _mensajeError(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['error'] is String) return data['error'] as String;
    if (data is Map && data['detail'] is String) return data['detail'] as String;
    return 'No se pudo conectar con el servidor. Verifique su conexión.';
  }

  Future<LoginResultado> login(String username, String password) async {
    try {
      final r = await _dio.post<Map<String, dynamic>>('/auth/login', data: {
        'username': username,
        'password': password,
      });
      final data = r.data!;
      if (data['mfa_requerido'] == true) {
        return MfaRequerido(
          sessionToken: data['session_token'] as String,
          enrolamiento: data['mfa_enrolamiento'] as bool? ?? false,
        );
      }
      return LoginExitoso(await _guardarTokens(data));
    } on DioException catch (e) {
      throw AuthException(_mensajeError(e));
    }
  }

  /// Primer paso del enrolamiento MFA: obtiene el secreto TOTP para dar de
  /// alta en Google Authenticator / Authy / etc. (mostramos el secreto en
  /// texto; no generamos QR para no añadir una dependencia nueva al proyecto).
  Future<String> enrollStart(String sessionToken) async {
    try {
      final r = await _dio.post<Map<String, dynamic>>('/auth/mfa/enroll/start', data: {
        'session_token': sessionToken,
      });
      return r.data!['secreto'] as String;
    } on DioException catch (e) {
      throw AuthException(_mensajeError(e));
    }
  }

  Future<UsuarioSesion> enrollConfirm(String sessionToken, String codigo) async {
    try {
      final r = await _dio.post<Map<String, dynamic>>('/auth/mfa/enroll/confirm', data: {
        'session_token': sessionToken,
        'codigo': codigo,
      });
      return await _guardarTokens(r.data!);
    } on DioException catch (e) {
      throw AuthException(_mensajeError(e));
    }
  }

  Future<UsuarioSesion> verifyMfa(String sessionToken, String codigo) async {
    try {
      final r = await _dio.post<Map<String, dynamic>>('/auth/mfa/verify', data: {
        'session_token': sessionToken,
        'codigo': codigo,
      });
      return await _guardarTokens(r.data!);
    } on DioException catch (e) {
      throw AuthException(_mensajeError(e));
    }
  }

  Future<UsuarioSesion> _guardarTokens(Map<String, dynamic> tokenResponse) async {
    await _storage.write(key: 'access_token', value: tokenResponse['access_token'] as String);
    await _storage.write(key: 'refresh_token', value: tokenResponse['refresh_token'] as String);
    return UsuarioSesion.fromJson(tokenResponse['usuario'] as Map<String, dynamic>);
  }

  /// Intenta renovar el access token con el refresh token guardado.
  /// Devuelve true si lo logró (y ya quedó guardado el nuevo par de tokens).
  Future<bool> refresh() async {
    final refreshToken = await _storage.read(key: 'refresh_token');
    if (refreshToken == null) return false;
    try {
      final r = await _dio.post<Map<String, dynamic>>('/auth/refresh', data: {
        'refresh_token': refreshToken,
      });
      await _guardarTokens(r.data!);
      return true;
    } on DioException {
      await logout();
      return false;
    }
  }

  Future<bool> haySesion() async => (await _storage.read(key: 'access_token')) != null;

  Future<void> logout() async {
    final refreshToken = await _storage.read(key: 'refresh_token');
    final accessToken = await _storage.read(key: 'access_token');
    if (accessToken != null) {
      try {
        await _dio.post<void>(
          '/auth/logout',
          data: {if (refreshToken != null) 'refresh_token': refreshToken},
          options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
        );
      } on DioException {
        // Aunque falle la llamada al servidor, igual borramos la sesión local.
      }
    }
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }
}
