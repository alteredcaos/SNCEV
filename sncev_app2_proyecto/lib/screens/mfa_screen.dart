// =============================================================================
// SNCEV App 2 — Segundo factor (TOTP)
//
// Los roles de nivel >= 4 (coordinador jurisdiccional en adelante) exigen MFA
// obligatorio (ver core/config.py, MFA_REQUIRED_LEVEL en el backend). Si la
// cuenta todavía no tiene un autenticador dado de alta, primero hay que
// enrolarlo (mostrar el secreto para agregarlo a Google Authenticator/Authy/
// etc. y confirmar con un código); si ya lo tiene, solo se pide el código.
// =============================================================================

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/auth_providers.dart';
import '../services/auth_service.dart';

class MfaScreen extends ConsumerStatefulWidget {
  final String sessionToken;
  final bool enrolamiento;

  const MfaScreen({super.key, required this.sessionToken, required this.enrolamiento});

  @override
  ConsumerState<MfaScreen> createState() => _MfaScreenState();
}

class _MfaScreenState extends ConsumerState<MfaScreen> {
  final _codigoCtrl = TextEditingController();
  bool _cargando = false;
  bool _cargandoSecreto = false;
  String? _secreto;
  String? _error;

  @override
  void initState() {
    super.initState();
    if (widget.enrolamiento) _cargarSecreto();
  }

  @override
  void dispose() {
    _codigoCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarSecreto() async {
    setState(() => _cargandoSecreto = true);
    try {
      final secreto = await ref.read(authServiceProvider).enrollStart(widget.sessionToken);
      if (mounted) setState(() => _secreto = secreto);
    } on AuthException catch (e) {
      if (mounted) setState(() => _error = e.mensaje);
    } finally {
      if (mounted) setState(() => _cargandoSecreto = false);
    }
  }

  Future<void> _confirmar() async {
    final codigo = _codigoCtrl.text.trim();
    if (codigo.length < 6) {
      setState(() => _error = 'El código debe tener 6 dígitos');
      return;
    }
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final servicio = ref.read(authServiceProvider);
      final usuario = widget.enrolamiento
          ? await servicio.enrollConfirm(widget.sessionToken, codigo)
          : await servicio.verifyMfa(widget.sessionToken, codigo);
      ref.read(usuarioActualProvider.notifier).state = usuario;
      if (mounted) Navigator.of(context).pop(true);
    } on AuthException catch (e) {
      setState(() => _error = e.mensaje);
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verificación en dos pasos')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (widget.enrolamiento) ...[
                  const Text(
                    'Su rol requiere autenticación de dos factores. Configure un '
                    'autenticador (Google Authenticator, Authy, etc.) con esta clave:',
                  ),
                  const SizedBox(height: 16),
                  if (_cargandoSecreto)
                    const Center(child: CircularProgressIndicator())
                  else if (_secreto != null)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Column(
                        children: [
                          SelectableText(
                            _secreto!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontFamily: 'monospace', fontSize: 18, letterSpacing: 2),
                          ),
                          const SizedBox(height: 8),
                          TextButton.icon(
                            icon: const Icon(Icons.copy, size: 16),
                            label: const Text('Copiar clave'),
                            onPressed: () {
                              Clipboard.setData(ClipboardData(text: _secreto!));
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Clave copiada')),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 16),
                  const Text('Después, escriba el código de 6 dígitos que le muestre la app:'),
                ] else
                  const Text('Escriba el código de 6 dígitos de su aplicación autenticadora:'),
                const SizedBox(height: 16),
                TextField(
                  controller: _codigoCtrl,
                  keyboardType: TextInputType.number,
                  textAlign: TextAlign.center,
                  maxLength: 6,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  style: const TextStyle(fontSize: 28, letterSpacing: 8),
                  decoration: const InputDecoration(counterText: '', border: OutlineInputBorder()),
                  enabled: !_cargando,
                  onSubmitted: (_) => _confirmar(),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 8),
                  Text(_error!, style: TextStyle(color: Colors.red.shade700), textAlign: TextAlign.center),
                ],
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _cargando ? null : _confirmar,
                  style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: _cargando
                      ? const SizedBox(
                          width: 20, height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : Text(widget.enrolamiento ? 'Activar y entrar' : 'Verificar'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
