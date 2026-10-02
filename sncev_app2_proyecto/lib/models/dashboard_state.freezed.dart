// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint, type=warning, deprecated_member_use, deprecated_member_use_from_same_package
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'dashboard_state.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// dart format off
T _$identity<T>(T value) => value;
/// @nodoc
mixin _$DashboardState {

 FiltrosCobertura get filtros; List<CoberturaItem> get items; List<TendenciaPunto> get tendencia; bool get cargando; DateTime? get ultimaActualizacion;
/// Create a copy of DashboardState
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DashboardStateCopyWith<DashboardState> get copyWith => _$DashboardStateCopyWithImpl<DashboardState>(this as DashboardState, _$identity);



@override
bool operator ==(Object other) {
  final _this = this as DashboardState;
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DashboardState&&(identical(other.filtros, _this.filtros) || other.filtros == _this.filtros)&&const DeepCollectionEquality().equals(other.items, _this.items)&&const DeepCollectionEquality().equals(other.tendencia, _this.tendencia)&&(identical(other.cargando, _this.cargando) || other.cargando == _this.cargando)&&(identical(other.ultimaActualizacion, _this.ultimaActualizacion) || other.ultimaActualizacion == _this.ultimaActualizacion));
}


@override
int get hashCode {
  final _this = this as DashboardState;
  return Object.hash(runtimeType,_this.filtros,const DeepCollectionEquality().hash(_this.items),const DeepCollectionEquality().hash(_this.tendencia),_this.cargando,_this.ultimaActualizacion);
}

@override
String toString() {
  final _this = this as DashboardState;
  return 'DashboardState(filtros: ${_this.filtros}, items: ${_this.items}, tendencia: ${_this.tendencia}, cargando: ${_this.cargando}, ultimaActualizacion: ${_this.ultimaActualizacion})';
}


}

/// @nodoc
abstract mixin class $DashboardStateCopyWith<$Res>  {
  factory $DashboardStateCopyWith(DashboardState value, $Res Function(DashboardState) _then) = _$DashboardStateCopyWithImpl;
@useResult
$Res call({
 FiltrosCobertura filtros, List<CoberturaItem> items, List<TendenciaPunto> tendencia, bool cargando, DateTime? ultimaActualizacion
});


$FiltrosCoberturaCopyWith<$Res> get filtros;

}
/// @nodoc
class _$DashboardStateCopyWithImpl<$Res>
    implements $DashboardStateCopyWith<$Res> {
  _$DashboardStateCopyWithImpl(this._self, this._then);

  final DashboardState _self;
  final $Res Function(DashboardState) _then;

/// Create a copy of DashboardState
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? filtros = null,Object? items = null,Object? tendencia = null,Object? cargando = null,Object? ultimaActualizacion = freezed,}) {
  return _then(DashboardState(
filtros: null == filtros ? _self.filtros : filtros // ignore: cast_nullable_to_non_nullable
as FiltrosCobertura,items: null == items ? _self.items : items // ignore: cast_nullable_to_non_nullable
as List<CoberturaItem>,tendencia: null == tendencia ? _self.tendencia : tendencia // ignore: cast_nullable_to_non_nullable
as List<TendenciaPunto>,cargando: null == cargando ? _self.cargando : cargando // ignore: cast_nullable_to_non_nullable
as bool,ultimaActualizacion: freezed == ultimaActualizacion ? _self.ultimaActualizacion : ultimaActualizacion // ignore: cast_nullable_to_non_nullable
as DateTime?,
  ));
}
/// Create a copy of DashboardState
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$FiltrosCoberturaCopyWith<$Res> get filtros {
  
  return $FiltrosCoberturaCopyWith<$Res>(_self.filtros, (value) {
    return _then(_self.copyWith(filtros: value));
  });
}
}


/// Adds pattern-matching-related methods to [DashboardState].
extension DashboardStatePatterns on DashboardState {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _DashboardState value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _DashboardState() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _DashboardState value)  $default,){
final _that = this;
switch (_that) {
case _DashboardState():
return $default(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _DashboardState value)?  $default,){
final _that = this;
switch (_that) {
case _DashboardState() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( FiltrosCobertura filtros,  List<CoberturaItem> items,  List<TendenciaPunto> tendencia,  bool cargando,  DateTime? ultimaActualizacion)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _DashboardState() when $default != null:
return $default(_that.filtros,_that.items,_that.tendencia,_that.cargando,_that.ultimaActualizacion);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( FiltrosCobertura filtros,  List<CoberturaItem> items,  List<TendenciaPunto> tendencia,  bool cargando,  DateTime? ultimaActualizacion)  $default,) {final _that = this;
switch (_that) {
case _DashboardState():
return $default(_that.filtros,_that.items,_that.tendencia,_that.cargando,_that.ultimaActualizacion);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( FiltrosCobertura filtros,  List<CoberturaItem> items,  List<TendenciaPunto> tendencia,  bool cargando,  DateTime? ultimaActualizacion)?  $default,) {final _that = this;
switch (_that) {
case _DashboardState() when $default != null:
return $default(_that.filtros,_that.items,_that.tendencia,_that.cargando,_that.ultimaActualizacion);case _:
  return null;

}
}

}

/// @nodoc


class _DashboardState implements DashboardState {
  const _DashboardState({required this.filtros,  List<CoberturaItem> items = const [],  List<TendenciaPunto> tendencia = const [], this.cargando = true, this.ultimaActualizacion}): _items = items,_tendencia = tendencia;
  

@override final  FiltrosCobertura filtros;
 final  List<CoberturaItem> _items;
@override@JsonKey() List<CoberturaItem> get items {
  if (_items is EqualUnmodifiableListView) return _items;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_items);
}

 final  List<TendenciaPunto> _tendencia;
@override@JsonKey() List<TendenciaPunto> get tendencia {
  if (_tendencia is EqualUnmodifiableListView) return _tendencia;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_tendencia);
}

@override@JsonKey() final  bool cargando;
@override final  DateTime? ultimaActualizacion;

/// Create a copy of DashboardState
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$DashboardStateCopyWith<_DashboardState> get copyWith => __$DashboardStateCopyWithImpl<_DashboardState>(this, _$identity);



@override
bool operator ==(Object other) {
    return identical(this, other) || (other.runtimeType == runtimeType&&other is _DashboardState&&(identical(other.filtros, filtros) || other.filtros == filtros)&&const DeepCollectionEquality().equals(other.items, _items)&&const DeepCollectionEquality().equals(other.tendencia, _tendencia)&&(identical(other.cargando, cargando) || other.cargando == cargando)&&(identical(other.ultimaActualizacion, ultimaActualizacion) || other.ultimaActualizacion == ultimaActualizacion));
}


@override
int get hashCode {
    return Object.hash(runtimeType,filtros,const DeepCollectionEquality().hash(_items),const DeepCollectionEquality().hash(_tendencia),cargando,ultimaActualizacion);
}

@override
String toString() {
    return 'DashboardState(filtros: $filtros, items: $items, tendencia: $tendencia, cargando: $cargando, ultimaActualizacion: $ultimaActualizacion)';
}


}

/// @nodoc
abstract mixin class _$DashboardStateCopyWith<$Res> implements $DashboardStateCopyWith<$Res> {
  factory _$DashboardStateCopyWith(_DashboardState value, $Res Function(_DashboardState) _then) = __$DashboardStateCopyWithImpl;
@override @useResult
$Res call({
 FiltrosCobertura filtros, List<CoberturaItem> items, List<TendenciaPunto> tendencia, bool cargando, DateTime? ultimaActualizacion
});


@override $FiltrosCoberturaCopyWith<$Res> get filtros;

}
/// @nodoc
class __$DashboardStateCopyWithImpl<$Res>
    implements _$DashboardStateCopyWith<$Res> {
  __$DashboardStateCopyWithImpl(this._self, this._then);

  final _DashboardState _self;
  final $Res Function(_DashboardState) _then;

/// Create a copy of DashboardState
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? filtros = null,Object? items = null,Object? tendencia = null,Object? cargando = null,Object? ultimaActualizacion = freezed,}) {
  return _then(_DashboardState(
filtros: null == filtros ? _self.filtros : filtros // ignore: cast_nullable_to_non_nullable
as FiltrosCobertura,items: null == items ? _self._items : items // ignore: cast_nullable_to_non_nullable
as List<CoberturaItem>,tendencia: null == tendencia ? _self._tendencia : tendencia // ignore: cast_nullable_to_non_nullable
as List<TendenciaPunto>,cargando: null == cargando ? _self.cargando : cargando // ignore: cast_nullable_to_non_nullable
as bool,ultimaActualizacion: freezed == ultimaActualizacion ? _self.ultimaActualizacion : ultimaActualizacion // ignore: cast_nullable_to_non_nullable
as DateTime?,
  ));
}

/// Create a copy of DashboardState
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$FiltrosCoberturaCopyWith<$Res> get filtros {
  
  return $FiltrosCoberturaCopyWith<$Res>(_self.filtros, (value) {
    return _then(_self.copyWith(filtros: value));
  });
}
}

// dart format on
