// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'rezago_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(RezagoController)
final rezagoControllerProvider = RezagoControllerProvider._();

final class RezagoControllerProvider
    extends $NotifierProvider<RezagoController, RezagoState> {
  RezagoControllerProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'rezagoControllerProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$rezagoControllerHash();

  @$internal
  @override
  RezagoController create() => RezagoController();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(RezagoState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<RezagoState>(value),
    );
  }
}

String _$rezagoControllerHash() => r'50de214491c7ad8f68a537fd825c14a0e4b8cc8b';

abstract class _$RezagoController extends $Notifier<RezagoState> {
  RezagoState build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<RezagoState, RezagoState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<RezagoState, RezagoState>,
              RezagoState,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
