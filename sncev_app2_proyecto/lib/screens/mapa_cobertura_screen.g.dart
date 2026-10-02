// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mapa_cobertura_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(MapaController)
final mapaControllerProvider = MapaControllerProvider._();

final class MapaControllerProvider
    extends $NotifierProvider<MapaController, MapaState> {
  MapaControllerProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'mapaControllerProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$mapaControllerHash();

  @$internal
  @override
  MapaController create() => MapaController();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(MapaState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<MapaState>(value),
    );
  }
}

String _$mapaControllerHash() => r'93b79702fe9e68a322ea2065e114e0fac4ff8dcf';

abstract class _$MapaController extends $Notifier<MapaState> {
  MapaState build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<MapaState, MapaState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<MapaState, MapaState>,
              MapaState,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
