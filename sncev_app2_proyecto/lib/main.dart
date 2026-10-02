// =============================================================================
// SNCEV App 2 — Entry point
// =============================================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'screens/dashboard_cobertura_screen.dart';
import 'screens/rezago_screen.dart';
import 'screens/lotes_screen.dart';
import 'screens/mapa_cobertura_screen.dart';
import 'screens/login_screen.dart';
import 'services/auth_providers.dart';

void main() {
  // NOTA — Syncfusion Maps (usado en la pantalla "Mapa"): la versión gratuita
  // ("Community License") exige registrarse en syncfusion.com y llamar aquí a
  // SyncfusionLicense.registerLicense('TU_CLAVE'); si no se registra, el mapa
  // funciona igual pero muestra un banner de "trial". No es un bloqueante para
  // desarrollo/pruebas.
  runApp(const ProviderScope(child: SncevApp2()));
}

class SncevApp2 extends StatelessWidget {
  const SncevApp2({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SNCEV — Coberturas',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF185FA5),
        fontFamily: 'Noto Sans',
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Color(0xFF2B2B28),
          elevation: 0,
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: const Color(0xFF185FA5),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
        ),
      ),
      home: const _AuthGate(),
    );
  }
}

/// Muestra el login mientras no haya sesión guardada; una vez autenticado,
/// muestra el shell principal. sesionActivaProvider se invalida (recalcula)
/// justo después de un login o logout exitoso.
class _AuthGate extends ConsumerWidget {
  const _AuthGate();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sesion = ref.watch(sesionActivaProvider);
    return sesion.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (_, __) => const LoginScreen(),
      data: (haySesion) => haySesion ? const _Shell() : const LoginScreen(),
    );
  }
}

class _Shell extends ConsumerStatefulWidget {
  const _Shell();

  @override
  ConsumerState<_Shell> createState() => _ShellState();
}

class _ShellState extends ConsumerState<_Shell> {
  int _indice = 0;

  static const _pantallas = [
    DashboardCoberturaScreen(),
    RezagoScreen(),
    LotesScreen(),
    MapaCoberturaScreen(),
  ];

  static const _titulos = ['Cobertura', 'Rezago', 'Lotes', 'Mapa'];

  Future<void> _cerrarSesion() async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Seguro que quiere salir?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Cerrar sesión')),
        ],
      ),
    );
    if (confirmar != true) return;
    await ref.read(authServiceProvider).logout();
    ref.read(usuarioActualProvider.notifier).state = null;
    ref.invalidate(sesionActivaProvider);
  }

  @override
  Widget build(BuildContext context) {
    final usuario = ref.watch(usuarioActualProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(_titulos[_indice]),
        actions: [
          if (usuario != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Center(
                child: Text(
                  '${usuario.username} · ${usuario.rol}',
                  style: const TextStyle(fontSize: 13, color: Colors.grey),
                ),
              ),
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: _cerrarSesion,
          ),
        ],
      ),
      body: _pantallas[_indice],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indice,
        onDestinationSelected: (i) => setState(() => _indice = i),
        backgroundColor: Colors.white,
        destinations: const [
          NavigationDestination(
            icon:        Icon(Icons.shield_outlined),
            selectedIcon: Icon(Icons.shield),
            label:       'Cobertura',
          ),
          NavigationDestination(
            icon:        Icon(Icons.person_search_outlined),
            selectedIcon: Icon(Icons.person_search),
            label:       'Rezago',
          ),
          NavigationDestination(
            icon:        Icon(Icons.vaccines_outlined),
            selectedIcon: Icon(Icons.vaccines),
            label:       'Lotes',
          ),
          NavigationDestination(
            icon:        Icon(Icons.map_outlined),
            selectedIcon: Icon(Icons.map),
            label:       'Mapa',
          ),
        ],
      ),
    );
  }
}

class _PlaceholderScreen extends StatelessWidget {
  final String titulo;
  final IconData icono;
  const _PlaceholderScreen({required this.titulo, required this.icono});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(titulo)),
    body: Center(child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icono, size: 56, color: const Color(0xFFC3C2B7)),
        const SizedBox(height: 12),
        Text(titulo, style: const TextStyle(color: Color(0xFF888780))),
      ],
    )),
  );
}
