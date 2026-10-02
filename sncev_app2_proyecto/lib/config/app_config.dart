// =============================================================================
// SNCEV App 2 — Configuración de entorno
//
// baseUrl se resuelve en tiempo de compilación con --dart-define, así no hay que
// tocar código para apuntar a otro backend:
//
//   flutter run --dart-define=API_BASE_URL=http://192.168.1.50:8000/v1
//
// Si no se pasa nada, usa 10.0.2.2 (el alias que el EMULADOR de Android usa para
// llegar al "localhost" de la máquina donde corre el emulador). Para iOS
// Simulator, Chrome/web o desktop (Linux/Windows/macOS) usa localhost:
//
//   flutter run -d chrome  --dart-define=API_BASE_URL=http://localhost:8000/v1
//   flutter run -d linux   --dart-define=API_BASE_URL=http://localhost:8000/v1
//
// Para un teléfono físico, usa la IP de tu máquina en la red local (ej. 192.168.x.x),
// nunca localhost ni 10.0.2.2 (esos solo existen dentro del emulador).
// =============================================================================

class AppConfig {
  AppConfig._();

  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/v1',
  );

  /// Igual que [baseUrl] pero sin el sufijo "/v1", para rutas fuera del
  /// versionado del API (ej. archivos estáticos servidos en /v1/static/...
  /// ya están cubiertos por baseUrl; esto es por si se necesita la raíz).
  static String get rootUrl =>
      baseUrl.endsWith('/v1') ? baseUrl.substring(0, baseUrl.length - 3) : baseUrl;
}
