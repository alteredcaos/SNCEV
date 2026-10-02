// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint, type=warning, deprecated_member_use, deprecated_member_use_from_same_package
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'cobertura_service.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$CoberturaItem {

 String get dimensionId; String get dimensionNombre; String get vacunaClave; String get vacunaNombre; int get numeroDosis; int get dosisAplicadas; int get poblacionObjetivo; double get coberturaPct; double get concordanciaPct; int get dosisInvalidas;
/// Create a copy of CoberturaItem
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CoberturaItemCopyWith<CoberturaItem> get copyWith => _$CoberturaItemCopyWithImpl<CoberturaItem>(this as CoberturaItem, _$identity);

  /// Serializes this CoberturaItem to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  final _this = this as CoberturaItem;
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CoberturaItem&&(identical(other.dimensionId, _this.dimensionId) || other.dimensionId == _this.dimensionId)&&(identical(other.dimensionNombre, _this.dimensionNombre) || other.dimensionNombre == _this.dimensionNombre)&&(identical(other.vacunaClave, _this.vacunaClave) || other.vacunaClave == _this.vacunaClave)&&(identical(other.vacunaNombre, _this.vacunaNombre) || other.vacunaNombre == _this.vacunaNombre)&&(identical(other.numeroDosis, _this.numeroDosis) || other.numeroDosis == _this.numeroDosis)&&(identical(other.dosisAplicadas, _this.dosisAplicadas) || other.dosisAplicadas == _this.dosisAplicadas)&&(identical(other.poblacionObjetivo, _this.poblacionObjetivo) || other.poblacionObjetivo == _this.poblacionObjetivo)&&(identical(other.coberturaPct, _this.coberturaPct) || other.coberturaPct == _this.coberturaPct)&&(identical(other.concordanciaPct, _this.concordanciaPct) || other.concordanciaPct == _this.concordanciaPct)&&(identical(other.dosisInvalidas, _this.dosisInvalidas) || other.dosisInvalidas == _this.dosisInvalidas));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode {
  final _this = this as CoberturaItem;
  return Object.hash(runtimeType,_this.dimensionId,_this.dimensionNombre,_this.vacunaClave,_this.vacunaNombre,_this.numeroDosis,_this.dosisAplicadas,_this.poblacionObjetivo,_this.coberturaPct,_this.concordanciaPct,_this.dosisInvalidas);
}

@override
String toString() {
  final _this = this as CoberturaItem;
  return 'CoberturaItem(dimensionId: ${_this.dimensionId}, dimensionNombre: ${_this.dimensionNombre}, vacunaClave: ${_this.vacunaClave}, vacunaNombre: ${_this.vacunaNombre}, numeroDosis: ${_this.numeroDosis}, dosisAplicadas: ${_this.dosisAplicadas}, poblacionObjetivo: ${_this.poblacionObjetivo}, coberturaPct: ${_this.coberturaPct}, concordanciaPct: ${_this.concordanciaPct}, dosisInvalidas: ${_this.dosisInvalidas})';
}


}

/// @nodoc
abstract mixin class $CoberturaItemCopyWith<$Res>  {
  factory $CoberturaItemCopyWith(CoberturaItem value, $Res Function(CoberturaItem) _then) = _$CoberturaItemCopyWithImpl;
@useResult
$Res call({
 String dimensionId, String dimensionNombre, String vacunaClave, String vacunaNombre, int numeroDosis, int dosisAplicadas, int poblacionObjetivo, double coberturaPct, double concordanciaPct, int dosisInvalidas
});




}
/// @nodoc
class _$CoberturaItemCopyWithImpl<$Res>
    implements $CoberturaItemCopyWith<$Res> {
  _$CoberturaItemCopyWithImpl(this._self, this._then);

  final CoberturaItem _self;
  final $Res Function(CoberturaItem) _then;

/// Create a copy of CoberturaItem
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? dimensionId = null,Object? dimensionNombre = null,Object? vacunaClave = null,Object? vacunaNombre = null,Object? numeroDosis = null,Object? dosisAplicadas = null,Object? poblacionObjetivo = null,Object? coberturaPct = null,Object? concordanciaPct = null,Object? dosisInvalidas = null,}) {
  return _then(CoberturaItem(
dimensionId: null == dimensionId ? _self.dimensionId : dimensionId // ignore: cast_nullable_to_non_nullable
as String,dimensionNombre: null == dimensionNombre ? _self.dimensionNombre : dimensionNombre // ignore: cast_nullable_to_non_nullable
as String,vacunaClave: null == vacunaClave ? _self.vacunaClave : vacunaClave // ignore: cast_nullable_to_non_nullable
as String,vacunaNombre: null == vacunaNombre ? _self.vacunaNombre : vacunaNombre // ignore: cast_nullable_to_non_nullable
as String,numeroDosis: null == numeroDosis ? _self.numeroDosis : numeroDosis // ignore: cast_nullable_to_non_nullable
as int,dosisAplicadas: null == dosisAplicadas ? _self.dosisAplicadas : dosisAplicadas // ignore: cast_nullable_to_non_nullable
as int,poblacionObjetivo: null == poblacionObjetivo ? _self.poblacionObjetivo : poblacionObjetivo // ignore: cast_nullable_to_non_nullable
as int,coberturaPct: null == coberturaPct ? _self.coberturaPct : coberturaPct // ignore: cast_nullable_to_non_nullable
as double,concordanciaPct: null == concordanciaPct ? _self.concordanciaPct : concordanciaPct // ignore: cast_nullable_to_non_nullable
as double,dosisInvalidas: null == dosisInvalidas ? _self.dosisInvalidas : dosisInvalidas // ignore: cast_nullable_to_non_nullable
as int,
  ));
}

}


/// Adds pattern-matching-related methods to [CoberturaItem].
extension CoberturaItemPatterns on CoberturaItem {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _CoberturaItem value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CoberturaItem() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _CoberturaItem value)  $default,){
final _that = this;
switch (_that) {
case _CoberturaItem():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _CoberturaItem value)?  $default,){
final _that = this;
switch (_that) {
case _CoberturaItem() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String dimensionId,  String dimensionNombre,  String vacunaClave,  String vacunaNombre,  int numeroDosis,  int dosisAplicadas,  int poblacionObjetivo,  double coberturaPct,  double concordanciaPct,  int dosisInvalidas)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CoberturaItem() when $default != null:
return $default(_that.dimensionId,_that.dimensionNombre,_that.vacunaClave,_that.vacunaNombre,_that.numeroDosis,_that.dosisAplicadas,_that.poblacionObjetivo,_that.coberturaPct,_that.concordanciaPct,_that.dosisInvalidas);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String dimensionId,  String dimensionNombre,  String vacunaClave,  String vacunaNombre,  int numeroDosis,  int dosisAplicadas,  int poblacionObjetivo,  double coberturaPct,  double concordanciaPct,  int dosisInvalidas)  $default,) {final _that = this;
switch (_that) {
case _CoberturaItem():
return $default(_that.dimensionId,_that.dimensionNombre,_that.vacunaClave,_that.vacunaNombre,_that.numeroDosis,_that.dosisAplicadas,_that.poblacionObjetivo,_that.coberturaPct,_that.concordanciaPct,_that.dosisInvalidas);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String dimensionId,  String dimensionNombre,  String vacunaClave,  String vacunaNombre,  int numeroDosis,  int dosisAplicadas,  int poblacionObjetivo,  double coberturaPct,  double concordanciaPct,  int dosisInvalidas)?  $default,) {final _that = this;
switch (_that) {
case _CoberturaItem() when $default != null:
return $default(_that.dimensionId,_that.dimensionNombre,_that.vacunaClave,_that.vacunaNombre,_that.numeroDosis,_that.dosisAplicadas,_that.poblacionObjetivo,_that.coberturaPct,_that.concordanciaPct,_that.dosisInvalidas);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _CoberturaItem implements CoberturaItem {
  const _CoberturaItem({required this.dimensionId, required this.dimensionNombre, required this.vacunaClave, required this.vacunaNombre, required this.numeroDosis, required this.dosisAplicadas, required this.poblacionObjetivo, required this.coberturaPct, required this.concordanciaPct, required this.dosisInvalidas});
  factory _CoberturaItem.fromJson(Map<String, dynamic> json) => _$CoberturaItemFromJson(json);

@override final  String dimensionId;
@override final  String dimensionNombre;
@override final  String vacunaClave;
@override final  String vacunaNombre;
@override final  int numeroDosis;
@override final  int dosisAplicadas;
@override final  int poblacionObjetivo;
@override final  double coberturaPct;
@override final  double concordanciaPct;
@override final  int dosisInvalidas;

/// Create a copy of CoberturaItem
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CoberturaItemCopyWith<_CoberturaItem> get copyWith => __$CoberturaItemCopyWithImpl<_CoberturaItem>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CoberturaItemToJson(this, );
}

@override
bool operator ==(Object other) {
    return identical(this, other) || (other.runtimeType == runtimeType&&other is _CoberturaItem&&(identical(other.dimensionId, dimensionId) || other.dimensionId == dimensionId)&&(identical(other.dimensionNombre, dimensionNombre) || other.dimensionNombre == dimensionNombre)&&(identical(other.vacunaClave, vacunaClave) || other.vacunaClave == vacunaClave)&&(identical(other.vacunaNombre, vacunaNombre) || other.vacunaNombre == vacunaNombre)&&(identical(other.numeroDosis, numeroDosis) || other.numeroDosis == numeroDosis)&&(identical(other.dosisAplicadas, dosisAplicadas) || other.dosisAplicadas == dosisAplicadas)&&(identical(other.poblacionObjetivo, poblacionObjetivo) || other.poblacionObjetivo == poblacionObjetivo)&&(identical(other.coberturaPct, coberturaPct) || other.coberturaPct == coberturaPct)&&(identical(other.concordanciaPct, concordanciaPct) || other.concordanciaPct == concordanciaPct)&&(identical(other.dosisInvalidas, dosisInvalidas) || other.dosisInvalidas == dosisInvalidas));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode {
    return Object.hash(runtimeType,dimensionId,dimensionNombre,vacunaClave,vacunaNombre,numeroDosis,dosisAplicadas,poblacionObjetivo,coberturaPct,concordanciaPct,dosisInvalidas);
}

@override
String toString() {
    return 'CoberturaItem(dimensionId: $dimensionId, dimensionNombre: $dimensionNombre, vacunaClave: $vacunaClave, vacunaNombre: $vacunaNombre, numeroDosis: $numeroDosis, dosisAplicadas: $dosisAplicadas, poblacionObjetivo: $poblacionObjetivo, coberturaPct: $coberturaPct, concordanciaPct: $concordanciaPct, dosisInvalidas: $dosisInvalidas)';
}


}

/// @nodoc
abstract mixin class _$CoberturaItemCopyWith<$Res> implements $CoberturaItemCopyWith<$Res> {
  factory _$CoberturaItemCopyWith(_CoberturaItem value, $Res Function(_CoberturaItem) _then) = __$CoberturaItemCopyWithImpl;
@override @useResult
$Res call({
 String dimensionId, String dimensionNombre, String vacunaClave, String vacunaNombre, int numeroDosis, int dosisAplicadas, int poblacionObjetivo, double coberturaPct, double concordanciaPct, int dosisInvalidas
});




}
/// @nodoc
class __$CoberturaItemCopyWithImpl<$Res>
    implements _$CoberturaItemCopyWith<$Res> {
  __$CoberturaItemCopyWithImpl(this._self, this._then);

  final _CoberturaItem _self;
  final $Res Function(_CoberturaItem) _then;

/// Create a copy of CoberturaItem
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? dimensionId = null,Object? dimensionNombre = null,Object? vacunaClave = null,Object? vacunaNombre = null,Object? numeroDosis = null,Object? dosisAplicadas = null,Object? poblacionObjetivo = null,Object? coberturaPct = null,Object? concordanciaPct = null,Object? dosisInvalidas = null,}) {
  return _then(_CoberturaItem(
dimensionId: null == dimensionId ? _self.dimensionId : dimensionId // ignore: cast_nullable_to_non_nullable
as String,dimensionNombre: null == dimensionNombre ? _self.dimensionNombre : dimensionNombre // ignore: cast_nullable_to_non_nullable
as String,vacunaClave: null == vacunaClave ? _self.vacunaClave : vacunaClave // ignore: cast_nullable_to_non_nullable
as String,vacunaNombre: null == vacunaNombre ? _self.vacunaNombre : vacunaNombre // ignore: cast_nullable_to_non_nullable
as String,numeroDosis: null == numeroDosis ? _self.numeroDosis : numeroDosis // ignore: cast_nullable_to_non_nullable
as int,dosisAplicadas: null == dosisAplicadas ? _self.dosisAplicadas : dosisAplicadas // ignore: cast_nullable_to_non_nullable
as int,poblacionObjetivo: null == poblacionObjetivo ? _self.poblacionObjetivo : poblacionObjetivo // ignore: cast_nullable_to_non_nullable
as int,coberturaPct: null == coberturaPct ? _self.coberturaPct : coberturaPct // ignore: cast_nullable_to_non_nullable
as double,concordanciaPct: null == concordanciaPct ? _self.concordanciaPct : concordanciaPct // ignore: cast_nullable_to_non_nullable
as double,dosisInvalidas: null == dosisInvalidas ? _self.dosisInvalidas : dosisInvalidas // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}


/// @nodoc
mixin _$TendenciaPunto {

 int get anio; int get semana; int get dosisAplicadas; int get poblacionObjetivo; double get coberturaPct;
/// Create a copy of TendenciaPunto
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$TendenciaPuntoCopyWith<TendenciaPunto> get copyWith => _$TendenciaPuntoCopyWithImpl<TendenciaPunto>(this as TendenciaPunto, _$identity);

  /// Serializes this TendenciaPunto to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  final _this = this as TendenciaPunto;
  return identical(this, other) || (other.runtimeType == runtimeType&&other is TendenciaPunto&&(identical(other.anio, _this.anio) || other.anio == _this.anio)&&(identical(other.semana, _this.semana) || other.semana == _this.semana)&&(identical(other.dosisAplicadas, _this.dosisAplicadas) || other.dosisAplicadas == _this.dosisAplicadas)&&(identical(other.poblacionObjetivo, _this.poblacionObjetivo) || other.poblacionObjetivo == _this.poblacionObjetivo)&&(identical(other.coberturaPct, _this.coberturaPct) || other.coberturaPct == _this.coberturaPct));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode {
  final _this = this as TendenciaPunto;
  return Object.hash(runtimeType,_this.anio,_this.semana,_this.dosisAplicadas,_this.poblacionObjetivo,_this.coberturaPct);
}

@override
String toString() {
  final _this = this as TendenciaPunto;
  return 'TendenciaPunto(anio: ${_this.anio}, semana: ${_this.semana}, dosisAplicadas: ${_this.dosisAplicadas}, poblacionObjetivo: ${_this.poblacionObjetivo}, coberturaPct: ${_this.coberturaPct})';
}


}

/// @nodoc
abstract mixin class $TendenciaPuntoCopyWith<$Res>  {
  factory $TendenciaPuntoCopyWith(TendenciaPunto value, $Res Function(TendenciaPunto) _then) = _$TendenciaPuntoCopyWithImpl;
@useResult
$Res call({
 int anio, int semana, int dosisAplicadas, int poblacionObjetivo, double coberturaPct
});




}
/// @nodoc
class _$TendenciaPuntoCopyWithImpl<$Res>
    implements $TendenciaPuntoCopyWith<$Res> {
  _$TendenciaPuntoCopyWithImpl(this._self, this._then);

  final TendenciaPunto _self;
  final $Res Function(TendenciaPunto) _then;

/// Create a copy of TendenciaPunto
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? anio = null,Object? semana = null,Object? dosisAplicadas = null,Object? poblacionObjetivo = null,Object? coberturaPct = null,}) {
  return _then(TendenciaPunto(
anio: null == anio ? _self.anio : anio // ignore: cast_nullable_to_non_nullable
as int,semana: null == semana ? _self.semana : semana // ignore: cast_nullable_to_non_nullable
as int,dosisAplicadas: null == dosisAplicadas ? _self.dosisAplicadas : dosisAplicadas // ignore: cast_nullable_to_non_nullable
as int,poblacionObjetivo: null == poblacionObjetivo ? _self.poblacionObjetivo : poblacionObjetivo // ignore: cast_nullable_to_non_nullable
as int,coberturaPct: null == coberturaPct ? _self.coberturaPct : coberturaPct // ignore: cast_nullable_to_non_nullable
as double,
  ));
}

}


/// Adds pattern-matching-related methods to [TendenciaPunto].
extension TendenciaPuntoPatterns on TendenciaPunto {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _TendenciaPunto value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _TendenciaPunto() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _TendenciaPunto value)  $default,){
final _that = this;
switch (_that) {
case _TendenciaPunto():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _TendenciaPunto value)?  $default,){
final _that = this;
switch (_that) {
case _TendenciaPunto() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( int anio,  int semana,  int dosisAplicadas,  int poblacionObjetivo,  double coberturaPct)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _TendenciaPunto() when $default != null:
return $default(_that.anio,_that.semana,_that.dosisAplicadas,_that.poblacionObjetivo,_that.coberturaPct);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( int anio,  int semana,  int dosisAplicadas,  int poblacionObjetivo,  double coberturaPct)  $default,) {final _that = this;
switch (_that) {
case _TendenciaPunto():
return $default(_that.anio,_that.semana,_that.dosisAplicadas,_that.poblacionObjetivo,_that.coberturaPct);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( int anio,  int semana,  int dosisAplicadas,  int poblacionObjetivo,  double coberturaPct)?  $default,) {final _that = this;
switch (_that) {
case _TendenciaPunto() when $default != null:
return $default(_that.anio,_that.semana,_that.dosisAplicadas,_that.poblacionObjetivo,_that.coberturaPct);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _TendenciaPunto implements TendenciaPunto {
  const _TendenciaPunto({required this.anio, required this.semana, required this.dosisAplicadas, required this.poblacionObjetivo, required this.coberturaPct});
  factory _TendenciaPunto.fromJson(Map<String, dynamic> json) => _$TendenciaPuntoFromJson(json);

@override final  int anio;
@override final  int semana;
@override final  int dosisAplicadas;
@override final  int poblacionObjetivo;
@override final  double coberturaPct;

/// Create a copy of TendenciaPunto
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$TendenciaPuntoCopyWith<_TendenciaPunto> get copyWith => __$TendenciaPuntoCopyWithImpl<_TendenciaPunto>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$TendenciaPuntoToJson(this, );
}

@override
bool operator ==(Object other) {
    return identical(this, other) || (other.runtimeType == runtimeType&&other is _TendenciaPunto&&(identical(other.anio, anio) || other.anio == anio)&&(identical(other.semana, semana) || other.semana == semana)&&(identical(other.dosisAplicadas, dosisAplicadas) || other.dosisAplicadas == dosisAplicadas)&&(identical(other.poblacionObjetivo, poblacionObjetivo) || other.poblacionObjetivo == poblacionObjetivo)&&(identical(other.coberturaPct, coberturaPct) || other.coberturaPct == coberturaPct));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode {
    return Object.hash(runtimeType,anio,semana,dosisAplicadas,poblacionObjetivo,coberturaPct);
}

@override
String toString() {
    return 'TendenciaPunto(anio: $anio, semana: $semana, dosisAplicadas: $dosisAplicadas, poblacionObjetivo: $poblacionObjetivo, coberturaPct: $coberturaPct)';
}


}

/// @nodoc
abstract mixin class _$TendenciaPuntoCopyWith<$Res> implements $TendenciaPuntoCopyWith<$Res> {
  factory _$TendenciaPuntoCopyWith(_TendenciaPunto value, $Res Function(_TendenciaPunto) _then) = __$TendenciaPuntoCopyWithImpl;
@override @useResult
$Res call({
 int anio, int semana, int dosisAplicadas, int poblacionObjetivo, double coberturaPct
});




}
/// @nodoc
class __$TendenciaPuntoCopyWithImpl<$Res>
    implements _$TendenciaPuntoCopyWith<$Res> {
  __$TendenciaPuntoCopyWithImpl(this._self, this._then);

  final _TendenciaPunto _self;
  final $Res Function(_TendenciaPunto) _then;

/// Create a copy of TendenciaPunto
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? anio = null,Object? semana = null,Object? dosisAplicadas = null,Object? poblacionObjetivo = null,Object? coberturaPct = null,}) {
  return _then(_TendenciaPunto(
anio: null == anio ? _self.anio : anio // ignore: cast_nullable_to_non_nullable
as int,semana: null == semana ? _self.semana : semana // ignore: cast_nullable_to_non_nullable
as int,dosisAplicadas: null == dosisAplicadas ? _self.dosisAplicadas : dosisAplicadas // ignore: cast_nullable_to_non_nullable
as int,poblacionObjetivo: null == poblacionObjetivo ? _self.poblacionObjetivo : poblacionObjetivo // ignore: cast_nullable_to_non_nullable
as int,coberturaPct: null == coberturaPct ? _self.coberturaPct : coberturaPct // ignore: cast_nullable_to_non_nullable
as double,
  ));
}


}


/// @nodoc
mixin _$PacienteRezago {

 String get pacienteId; String get fechaNacimiento; String get vacuna; String get serie; String get fechaLimite; int get diasRezago; String get municipio;
/// Create a copy of PacienteRezago
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PacienteRezagoCopyWith<PacienteRezago> get copyWith => _$PacienteRezagoCopyWithImpl<PacienteRezago>(this as PacienteRezago, _$identity);

  /// Serializes this PacienteRezago to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  final _this = this as PacienteRezago;
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PacienteRezago&&(identical(other.pacienteId, _this.pacienteId) || other.pacienteId == _this.pacienteId)&&(identical(other.fechaNacimiento, _this.fechaNacimiento) || other.fechaNacimiento == _this.fechaNacimiento)&&(identical(other.vacuna, _this.vacuna) || other.vacuna == _this.vacuna)&&(identical(other.serie, _this.serie) || other.serie == _this.serie)&&(identical(other.fechaLimite, _this.fechaLimite) || other.fechaLimite == _this.fechaLimite)&&(identical(other.diasRezago, _this.diasRezago) || other.diasRezago == _this.diasRezago)&&(identical(other.municipio, _this.municipio) || other.municipio == _this.municipio));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode {
  final _this = this as PacienteRezago;
  return Object.hash(runtimeType,_this.pacienteId,_this.fechaNacimiento,_this.vacuna,_this.serie,_this.fechaLimite,_this.diasRezago,_this.municipio);
}

@override
String toString() {
  final _this = this as PacienteRezago;
  return 'PacienteRezago(pacienteId: ${_this.pacienteId}, fechaNacimiento: ${_this.fechaNacimiento}, vacuna: ${_this.vacuna}, serie: ${_this.serie}, fechaLimite: ${_this.fechaLimite}, diasRezago: ${_this.diasRezago}, municipio: ${_this.municipio})';
}


}

/// @nodoc
abstract mixin class $PacienteRezagoCopyWith<$Res>  {
  factory $PacienteRezagoCopyWith(PacienteRezago value, $Res Function(PacienteRezago) _then) = _$PacienteRezagoCopyWithImpl;
@useResult
$Res call({
 String pacienteId, String fechaNacimiento, String vacuna, String serie, String fechaLimite, int diasRezago, String municipio
});




}
/// @nodoc
class _$PacienteRezagoCopyWithImpl<$Res>
    implements $PacienteRezagoCopyWith<$Res> {
  _$PacienteRezagoCopyWithImpl(this._self, this._then);

  final PacienteRezago _self;
  final $Res Function(PacienteRezago) _then;

/// Create a copy of PacienteRezago
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? pacienteId = null,Object? fechaNacimiento = null,Object? vacuna = null,Object? serie = null,Object? fechaLimite = null,Object? diasRezago = null,Object? municipio = null,}) {
  return _then(PacienteRezago(
pacienteId: null == pacienteId ? _self.pacienteId : pacienteId // ignore: cast_nullable_to_non_nullable
as String,fechaNacimiento: null == fechaNacimiento ? _self.fechaNacimiento : fechaNacimiento // ignore: cast_nullable_to_non_nullable
as String,vacuna: null == vacuna ? _self.vacuna : vacuna // ignore: cast_nullable_to_non_nullable
as String,serie: null == serie ? _self.serie : serie // ignore: cast_nullable_to_non_nullable
as String,fechaLimite: null == fechaLimite ? _self.fechaLimite : fechaLimite // ignore: cast_nullable_to_non_nullable
as String,diasRezago: null == diasRezago ? _self.diasRezago : diasRezago // ignore: cast_nullable_to_non_nullable
as int,municipio: null == municipio ? _self.municipio : municipio // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [PacienteRezago].
extension PacienteRezagoPatterns on PacienteRezago {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _PacienteRezago value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _PacienteRezago() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _PacienteRezago value)  $default,){
final _that = this;
switch (_that) {
case _PacienteRezago():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _PacienteRezago value)?  $default,){
final _that = this;
switch (_that) {
case _PacienteRezago() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String pacienteId,  String fechaNacimiento,  String vacuna,  String serie,  String fechaLimite,  int diasRezago,  String municipio)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _PacienteRezago() when $default != null:
return $default(_that.pacienteId,_that.fechaNacimiento,_that.vacuna,_that.serie,_that.fechaLimite,_that.diasRezago,_that.municipio);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String pacienteId,  String fechaNacimiento,  String vacuna,  String serie,  String fechaLimite,  int diasRezago,  String municipio)  $default,) {final _that = this;
switch (_that) {
case _PacienteRezago():
return $default(_that.pacienteId,_that.fechaNacimiento,_that.vacuna,_that.serie,_that.fechaLimite,_that.diasRezago,_that.municipio);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String pacienteId,  String fechaNacimiento,  String vacuna,  String serie,  String fechaLimite,  int diasRezago,  String municipio)?  $default,) {final _that = this;
switch (_that) {
case _PacienteRezago() when $default != null:
return $default(_that.pacienteId,_that.fechaNacimiento,_that.vacuna,_that.serie,_that.fechaLimite,_that.diasRezago,_that.municipio);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _PacienteRezago implements PacienteRezago {
  const _PacienteRezago({required this.pacienteId, required this.fechaNacimiento, required this.vacuna, required this.serie, required this.fechaLimite, required this.diasRezago, required this.municipio});
  factory _PacienteRezago.fromJson(Map<String, dynamic> json) => _$PacienteRezagoFromJson(json);

@override final  String pacienteId;
@override final  String fechaNacimiento;
@override final  String vacuna;
@override final  String serie;
@override final  String fechaLimite;
@override final  int diasRezago;
@override final  String municipio;

/// Create a copy of PacienteRezago
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$PacienteRezagoCopyWith<_PacienteRezago> get copyWith => __$PacienteRezagoCopyWithImpl<_PacienteRezago>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$PacienteRezagoToJson(this, );
}

@override
bool operator ==(Object other) {
    return identical(this, other) || (other.runtimeType == runtimeType&&other is _PacienteRezago&&(identical(other.pacienteId, pacienteId) || other.pacienteId == pacienteId)&&(identical(other.fechaNacimiento, fechaNacimiento) || other.fechaNacimiento == fechaNacimiento)&&(identical(other.vacuna, vacuna) || other.vacuna == vacuna)&&(identical(other.serie, serie) || other.serie == serie)&&(identical(other.fechaLimite, fechaLimite) || other.fechaLimite == fechaLimite)&&(identical(other.diasRezago, diasRezago) || other.diasRezago == diasRezago)&&(identical(other.municipio, municipio) || other.municipio == municipio));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode {
    return Object.hash(runtimeType,pacienteId,fechaNacimiento,vacuna,serie,fechaLimite,diasRezago,municipio);
}

@override
String toString() {
    return 'PacienteRezago(pacienteId: $pacienteId, fechaNacimiento: $fechaNacimiento, vacuna: $vacuna, serie: $serie, fechaLimite: $fechaLimite, diasRezago: $diasRezago, municipio: $municipio)';
}


}

/// @nodoc
abstract mixin class _$PacienteRezagoCopyWith<$Res> implements $PacienteRezagoCopyWith<$Res> {
  factory _$PacienteRezagoCopyWith(_PacienteRezago value, $Res Function(_PacienteRezago) _then) = __$PacienteRezagoCopyWithImpl;
@override @useResult
$Res call({
 String pacienteId, String fechaNacimiento, String vacuna, String serie, String fechaLimite, int diasRezago, String municipio
});




}
/// @nodoc
class __$PacienteRezagoCopyWithImpl<$Res>
    implements _$PacienteRezagoCopyWith<$Res> {
  __$PacienteRezagoCopyWithImpl(this._self, this._then);

  final _PacienteRezago _self;
  final $Res Function(_PacienteRezago) _then;

/// Create a copy of PacienteRezago
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? pacienteId = null,Object? fechaNacimiento = null,Object? vacuna = null,Object? serie = null,Object? fechaLimite = null,Object? diasRezago = null,Object? municipio = null,}) {
  return _then(_PacienteRezago(
pacienteId: null == pacienteId ? _self.pacienteId : pacienteId // ignore: cast_nullable_to_non_nullable
as String,fechaNacimiento: null == fechaNacimiento ? _self.fechaNacimiento : fechaNacimiento // ignore: cast_nullable_to_non_nullable
as String,vacuna: null == vacuna ? _self.vacuna : vacuna // ignore: cast_nullable_to_non_nullable
as String,serie: null == serie ? _self.serie : serie // ignore: cast_nullable_to_non_nullable
as String,fechaLimite: null == fechaLimite ? _self.fechaLimite : fechaLimite // ignore: cast_nullable_to_non_nullable
as String,diasRezago: null == diasRezago ? _self.diasRezago : diasRezago // ignore: cast_nullable_to_non_nullable
as int,municipio: null == municipio ? _self.municipio : municipio // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

/// @nodoc
mixin _$FiltrosCobertura {

 int? get vacunaId; int? get numeroDosis; int? get tipoCartillaId; String? get estadoClave; int? get jurisdiccionId; int? get municipioId; int get anio; int get semanaDesde; int get semanaHasta; String get dimension;
/// Create a copy of FiltrosCobertura
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$FiltrosCoberturaCopyWith<FiltrosCobertura> get copyWith => _$FiltrosCoberturaCopyWithImpl<FiltrosCobertura>(this as FiltrosCobertura, _$identity);



@override
bool operator ==(Object other) {
  final _this = this as FiltrosCobertura;
  return identical(this, other) || (other.runtimeType == runtimeType&&other is FiltrosCobertura&&(identical(other.vacunaId, _this.vacunaId) || other.vacunaId == _this.vacunaId)&&(identical(other.numeroDosis, _this.numeroDosis) || other.numeroDosis == _this.numeroDosis)&&(identical(other.tipoCartillaId, _this.tipoCartillaId) || other.tipoCartillaId == _this.tipoCartillaId)&&(identical(other.estadoClave, _this.estadoClave) || other.estadoClave == _this.estadoClave)&&(identical(other.jurisdiccionId, _this.jurisdiccionId) || other.jurisdiccionId == _this.jurisdiccionId)&&(identical(other.municipioId, _this.municipioId) || other.municipioId == _this.municipioId)&&(identical(other.anio, _this.anio) || other.anio == _this.anio)&&(identical(other.semanaDesde, _this.semanaDesde) || other.semanaDesde == _this.semanaDesde)&&(identical(other.semanaHasta, _this.semanaHasta) || other.semanaHasta == _this.semanaHasta)&&(identical(other.dimension, _this.dimension) || other.dimension == _this.dimension));
}


@override
int get hashCode {
  final _this = this as FiltrosCobertura;
  return Object.hash(runtimeType,_this.vacunaId,_this.numeroDosis,_this.tipoCartillaId,_this.estadoClave,_this.jurisdiccionId,_this.municipioId,_this.anio,_this.semanaDesde,_this.semanaHasta,_this.dimension);
}

@override
String toString() {
  final _this = this as FiltrosCobertura;
  return 'FiltrosCobertura(vacunaId: ${_this.vacunaId}, numeroDosis: ${_this.numeroDosis}, tipoCartillaId: ${_this.tipoCartillaId}, estadoClave: ${_this.estadoClave}, jurisdiccionId: ${_this.jurisdiccionId}, municipioId: ${_this.municipioId}, anio: ${_this.anio}, semanaDesde: ${_this.semanaDesde}, semanaHasta: ${_this.semanaHasta}, dimension: ${_this.dimension})';
}


}

/// @nodoc
abstract mixin class $FiltrosCoberturaCopyWith<$Res>  {
  factory $FiltrosCoberturaCopyWith(FiltrosCobertura value, $Res Function(FiltrosCobertura) _then) = _$FiltrosCoberturaCopyWithImpl;
@useResult
$Res call({
 int? vacunaId, int? numeroDosis, int? tipoCartillaId, String? estadoClave, int? jurisdiccionId, int? municipioId, int anio, int semanaDesde, int semanaHasta, String dimension
});




}
/// @nodoc
class _$FiltrosCoberturaCopyWithImpl<$Res>
    implements $FiltrosCoberturaCopyWith<$Res> {
  _$FiltrosCoberturaCopyWithImpl(this._self, this._then);

  final FiltrosCobertura _self;
  final $Res Function(FiltrosCobertura) _then;

/// Create a copy of FiltrosCobertura
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? vacunaId = freezed,Object? numeroDosis = freezed,Object? tipoCartillaId = freezed,Object? estadoClave = freezed,Object? jurisdiccionId = freezed,Object? municipioId = freezed,Object? anio = null,Object? semanaDesde = null,Object? semanaHasta = null,Object? dimension = null,}) {
  return _then(FiltrosCobertura(
vacunaId: freezed == vacunaId ? _self.vacunaId : vacunaId // ignore: cast_nullable_to_non_nullable
as int?,numeroDosis: freezed == numeroDosis ? _self.numeroDosis : numeroDosis // ignore: cast_nullable_to_non_nullable
as int?,tipoCartillaId: freezed == tipoCartillaId ? _self.tipoCartillaId : tipoCartillaId // ignore: cast_nullable_to_non_nullable
as int?,estadoClave: freezed == estadoClave ? _self.estadoClave : estadoClave // ignore: cast_nullable_to_non_nullable
as String?,jurisdiccionId: freezed == jurisdiccionId ? _self.jurisdiccionId : jurisdiccionId // ignore: cast_nullable_to_non_nullable
as int?,municipioId: freezed == municipioId ? _self.municipioId : municipioId // ignore: cast_nullable_to_non_nullable
as int?,anio: null == anio ? _self.anio : anio // ignore: cast_nullable_to_non_nullable
as int,semanaDesde: null == semanaDesde ? _self.semanaDesde : semanaDesde // ignore: cast_nullable_to_non_nullable
as int,semanaHasta: null == semanaHasta ? _self.semanaHasta : semanaHasta // ignore: cast_nullable_to_non_nullable
as int,dimension: null == dimension ? _self.dimension : dimension // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [FiltrosCobertura].
extension FiltrosCoberturaPatterns on FiltrosCobertura {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _FiltrosCobertura value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _FiltrosCobertura() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _FiltrosCobertura value)  $default,){
final _that = this;
switch (_that) {
case _FiltrosCobertura():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _FiltrosCobertura value)?  $default,){
final _that = this;
switch (_that) {
case _FiltrosCobertura() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( int? vacunaId,  int? numeroDosis,  int? tipoCartillaId,  String? estadoClave,  int? jurisdiccionId,  int? municipioId,  int anio,  int semanaDesde,  int semanaHasta,  String dimension)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _FiltrosCobertura() when $default != null:
return $default(_that.vacunaId,_that.numeroDosis,_that.tipoCartillaId,_that.estadoClave,_that.jurisdiccionId,_that.municipioId,_that.anio,_that.semanaDesde,_that.semanaHasta,_that.dimension);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( int? vacunaId,  int? numeroDosis,  int? tipoCartillaId,  String? estadoClave,  int? jurisdiccionId,  int? municipioId,  int anio,  int semanaDesde,  int semanaHasta,  String dimension)  $default,) {final _that = this;
switch (_that) {
case _FiltrosCobertura():
return $default(_that.vacunaId,_that.numeroDosis,_that.tipoCartillaId,_that.estadoClave,_that.jurisdiccionId,_that.municipioId,_that.anio,_that.semanaDesde,_that.semanaHasta,_that.dimension);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( int? vacunaId,  int? numeroDosis,  int? tipoCartillaId,  String? estadoClave,  int? jurisdiccionId,  int? municipioId,  int anio,  int semanaDesde,  int semanaHasta,  String dimension)?  $default,) {final _that = this;
switch (_that) {
case _FiltrosCobertura() when $default != null:
return $default(_that.vacunaId,_that.numeroDosis,_that.tipoCartillaId,_that.estadoClave,_that.jurisdiccionId,_that.municipioId,_that.anio,_that.semanaDesde,_that.semanaHasta,_that.dimension);case _:
  return null;

}
}

}

/// @nodoc


class _FiltrosCobertura implements FiltrosCobertura {
  const _FiltrosCobertura({this.vacunaId, this.numeroDosis, this.tipoCartillaId, this.estadoClave, this.jurisdiccionId, this.municipioId, required this.anio, this.semanaDesde = 1, this.semanaHasta = 52, this.dimension = 'estado'});
  

@override final  int? vacunaId;
@override final  int? numeroDosis;
@override final  int? tipoCartillaId;
@override final  String? estadoClave;
@override final  int? jurisdiccionId;
@override final  int? municipioId;
@override final  int anio;
@override@JsonKey() final  int semanaDesde;
@override@JsonKey() final  int semanaHasta;
@override@JsonKey() final  String dimension;

/// Create a copy of FiltrosCobertura
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$FiltrosCoberturaCopyWith<_FiltrosCobertura> get copyWith => __$FiltrosCoberturaCopyWithImpl<_FiltrosCobertura>(this, _$identity);



@override
bool operator ==(Object other) {
    return identical(this, other) || (other.runtimeType == runtimeType&&other is _FiltrosCobertura&&(identical(other.vacunaId, vacunaId) || other.vacunaId == vacunaId)&&(identical(other.numeroDosis, numeroDosis) || other.numeroDosis == numeroDosis)&&(identical(other.tipoCartillaId, tipoCartillaId) || other.tipoCartillaId == tipoCartillaId)&&(identical(other.estadoClave, estadoClave) || other.estadoClave == estadoClave)&&(identical(other.jurisdiccionId, jurisdiccionId) || other.jurisdiccionId == jurisdiccionId)&&(identical(other.municipioId, municipioId) || other.municipioId == municipioId)&&(identical(other.anio, anio) || other.anio == anio)&&(identical(other.semanaDesde, semanaDesde) || other.semanaDesde == semanaDesde)&&(identical(other.semanaHasta, semanaHasta) || other.semanaHasta == semanaHasta)&&(identical(other.dimension, dimension) || other.dimension == dimension));
}


@override
int get hashCode {
    return Object.hash(runtimeType,vacunaId,numeroDosis,tipoCartillaId,estadoClave,jurisdiccionId,municipioId,anio,semanaDesde,semanaHasta,dimension);
}

@override
String toString() {
    return 'FiltrosCobertura(vacunaId: $vacunaId, numeroDosis: $numeroDosis, tipoCartillaId: $tipoCartillaId, estadoClave: $estadoClave, jurisdiccionId: $jurisdiccionId, municipioId: $municipioId, anio: $anio, semanaDesde: $semanaDesde, semanaHasta: $semanaHasta, dimension: $dimension)';
}


}

/// @nodoc
abstract mixin class _$FiltrosCoberturaCopyWith<$Res> implements $FiltrosCoberturaCopyWith<$Res> {
  factory _$FiltrosCoberturaCopyWith(_FiltrosCobertura value, $Res Function(_FiltrosCobertura) _then) = __$FiltrosCoberturaCopyWithImpl;
@override @useResult
$Res call({
 int? vacunaId, int? numeroDosis, int? tipoCartillaId, String? estadoClave, int? jurisdiccionId, int? municipioId, int anio, int semanaDesde, int semanaHasta, String dimension
});




}
/// @nodoc
class __$FiltrosCoberturaCopyWithImpl<$Res>
    implements _$FiltrosCoberturaCopyWith<$Res> {
  __$FiltrosCoberturaCopyWithImpl(this._self, this._then);

  final _FiltrosCobertura _self;
  final $Res Function(_FiltrosCobertura) _then;

/// Create a copy of FiltrosCobertura
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? vacunaId = freezed,Object? numeroDosis = freezed,Object? tipoCartillaId = freezed,Object? estadoClave = freezed,Object? jurisdiccionId = freezed,Object? municipioId = freezed,Object? anio = null,Object? semanaDesde = null,Object? semanaHasta = null,Object? dimension = null,}) {
  return _then(_FiltrosCobertura(
vacunaId: freezed == vacunaId ? _self.vacunaId : vacunaId // ignore: cast_nullable_to_non_nullable
as int?,numeroDosis: freezed == numeroDosis ? _self.numeroDosis : numeroDosis // ignore: cast_nullable_to_non_nullable
as int?,tipoCartillaId: freezed == tipoCartillaId ? _self.tipoCartillaId : tipoCartillaId // ignore: cast_nullable_to_non_nullable
as int?,estadoClave: freezed == estadoClave ? _self.estadoClave : estadoClave // ignore: cast_nullable_to_non_nullable
as String?,jurisdiccionId: freezed == jurisdiccionId ? _self.jurisdiccionId : jurisdiccionId // ignore: cast_nullable_to_non_nullable
as int?,municipioId: freezed == municipioId ? _self.municipioId : municipioId // ignore: cast_nullable_to_non_nullable
as int?,anio: null == anio ? _self.anio : anio // ignore: cast_nullable_to_non_nullable
as int,semanaDesde: null == semanaDesde ? _self.semanaDesde : semanaDesde // ignore: cast_nullable_to_non_nullable
as int,semanaHasta: null == semanaHasta ? _self.semanaHasta : semanaHasta // ignore: cast_nullable_to_non_nullable
as int,dimension: null == dimension ? _self.dimension : dimension // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

// dart format on
