import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { QrCode, Download, ShieldCheck, CheckCircle2, Clock, ArrowLeft } from "lucide-react";
import {
  pacientes, nombreCompleto, nombreTipoCartilla, nombreUnidad,
  edadEnAnios, edadMeses, esquemaParaPaciente, nombreVacuna,
} from "@/lib/mockData";

export default function Cartilla() {
  const [pacienteId, setPacienteId] = useState("p1");
  const p = pacientes.find((x) => x.id === pacienteId);
  const esquema = p ? esquemaParaPaciente(p) : [];
  const aplicadas = esquema.filter((e) => e.estado === "aplicada").length;
  const avance = esquema.length ? Math.round((aplicadas / esquema.length) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-heading font-semibold">Cartilla electrónica de vacunación</h1>
          <p className="text-muted-foreground text-sm mt-1">Documento firmado digitalmente · verificación por QR</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={pacienteId} onValueChange={setPacienteId}>
            <SelectTrigger className="w-64"><SelectValue /></SelectTrigger>
            <SelectContent>
              {pacientes.map((x) => (
                <SelectItem key={x.id} value={x.id}>{nombreCompleto(x)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="w-4 h-4 mr-2" /> PDF</Button>
        </div>
      </div>

      {p && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Encabezado tipo cartilla */}
          <Card className="lg:col-span-2">
            <CardContent className="p-0">
              <div className="bg-gradient-to-r from-primary to-primary/80 text-primary-foreground p-5 rounded-t-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest opacity-80">Secretaría de Salud</p>
                    <p className="font-heading font-semibold text-lg">Cartilla Nacional de Vacunación</p>
                    <p className="text-xs opacity-80">{nombreTipoCartilla(p.tipo_cartilla_id)}</p>
                  </div>
                  <ShieldCheck className="w-9 h-9 opacity-90" />
                </div>
              </div>
              <div className="p-5 space-y-4">
                <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
                  <Campo label="Nombre completo" value={nombreCompleto(p)} />
                  <Campo label="CURP" value={p.curp} mono />
                  <Campo label="Fecha de nacimiento" value={new Date(p.fecha_nacimiento).toLocaleDateString("es-MX")} />
                  <Campo label="Edad" value={edadEnAnios(p.fecha_nacimiento) >= 1 ? `${edadEnAnios(p.fecha_nacimiento)} años` : `${edadMeses(p.fecha_nacimiento)} meses`} />
                  <Campo label="Sexo" value={p.sexo === "M" ? "Masculino" : "Femenino"} />
                  <Campo label="Unidad de registro" value={nombreUnidad(p.unidad_med_registro_id)} />
                </div>
                <Separator />
                <div>
                  <p className="text-sm font-medium mb-3">Esquema aplicado</p>
                  <div className="space-y-2">
                    {esquema.map((e) => (
                      <div key={e.id} className="flex items-center gap-3 rounded-lg border p-2.5">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${e.estado === "aplicada" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                          {e.estado === "aplicada" ? <CheckCircle2 className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{e.vacuna} <span className="text-muted-foreground">· dosis {e.numero_dosis}{e.es_refuerzo ? " (refuerzo)" : ""}</span></p>
                          <p className="text-xs text-muted-foreground">
                            {e.estado === "aplicada"
                              ? `Aplicada ${e.fecha_aplicacion} · lote ${e.lote} · ${e.aplicador}`
                              : "Pendiente"}
                          </p>
                        </div>
                        <Badge variant={e.estado === "aplicada" ? "secondary" : "outline"} className={e.estado === "aplicada" ? "bg-emerald-100 text-emerald-700" : "text-amber-700 border-amber-300"}>
                          {e.estado === "aplicada" ? "Aplicada" : "Pendiente"}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="border-t p-4 flex items-center justify-between bg-muted/30 rounded-b-xl">
                <div className="text-xs text-muted-foreground">
                  <p>Firma digital: RSA-2048 · SHA-256</p>
                  <p className="font-mono">9f3a…c1e7 (verificada)</p>
                </div>
                <Badge className="bg-emerald-100 text-emerald-700"><ShieldCheck className="w-3 h-3 mr-1" /> Documento válido</Badge>
              </div>
            </CardContent>
          </Card>

          {/* QR + avance */}
          <div className="space-y-6">
            <Card>
              <CardHeader><CardTitle className="text-base">Verificación pública</CardTitle></CardHeader>
              <CardContent className="flex flex-col items-center text-center">
                <div className="w-40 h-40 rounded-xl border-2 border-dashed flex items-center justify-center bg-muted/30">
                  <QrCode className="w-24 h-24 text-muted-foreground" />
                </div>
                <p className="text-xs text-muted-foreground mt-3">Escanea para verificar autenticidad en el portal ciudadano</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2"><CardDescription>Avance del esquema</CardDescription></CardHeader>
              <CardContent>
                <p className="text-4xl font-heading font-semibold">{avance}%</p>
                <p className="text-sm text-muted-foreground mt-1">{aplicadas} de {esquema.length} dosis</p>
                <Link to={`/pacientes/${p.id}`} className="mt-4 block">
                  <Button variant="outline" size="sm" className="w-full"><ArrowLeft className="w-4 h-4 mr-2" /> Ver expediente</Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function Campo({ label, value, mono }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`font-medium ${mono ? "font-mono text-xs" : ""}`}>{value}</p>
    </div>
  );
}