// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dashboard_cobertura_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(DashboardController)
final dashboardControllerProvider = DashboardControllerProvider._();

final class DashboardControllerProvider
    extends $AsyncNotifierProvider<DashboardController, DashboardState> {
  DashboardControllerProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'dashboardControllerProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$dashboardControllerHash();

  @$internal
  @override
  DashboardController create() => DashboardController();
}

String _$dashboardControllerHash() =>
    r'2e28181acc647b63676989e0e0a5fec28a2177df';

abstract class _$DashboardController extends $AsyncNotifier<DashboardState> {
  FutureOr<DashboardState> build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<AsyncValue<DashboardState>, DashboardState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<DashboardState>, DashboardState>,
              AsyncValue<DashboardState>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
