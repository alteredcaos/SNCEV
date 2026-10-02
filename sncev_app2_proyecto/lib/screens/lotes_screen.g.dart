// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'lotes_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(LotesController)
final lotesControllerProvider = LotesControllerProvider._();

final class LotesControllerProvider
    extends $NotifierProvider<LotesController, LotesState> {
  LotesControllerProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'lotesControllerProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$lotesControllerHash();

  @$internal
  @override
  LotesController create() => LotesController();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(LotesState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<LotesState>(value),
    );
  }
}

String _$lotesControllerHash() => r'5808149406dccc39115fd5586ba121781b07981b';

abstract class _$LotesController extends $Notifier<LotesState> {
  LotesState build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<LotesState, LotesState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<LotesState, LotesState>,
              LotesState,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
