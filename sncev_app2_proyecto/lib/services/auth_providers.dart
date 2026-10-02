// =============================================================================
// SNCEV App 2 — Providers de autenticación
// =============================================================================

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_service.dart';

final authServiceProvider = Provider<AuthService>((ref) => AuthService());

/// true = hay un access_token guardado, false = hay que mostrar el login.
/// Se recalcula llamando a ref.invalidate(sesionActivaProvider) tras login/logout.
final sesionActivaProvider = FutureProvider<bool>((ref) async {
  return ref.watch(authServiceProvider).haySesion();
});

final usuarioActualProvider = StateProvider<UsuarioSesion?>((ref) => null);
