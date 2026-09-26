import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from "@/components/ui/table";
import { Search, Syringe, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import {
  pacientes, vacunasAplicadas, esquema, vacunasCatalogo, unidades,
  nombreCompleto, edadEnAnios, edadMeses, nombreVacuna,
} from "@/lib/mockData";
import { useToast } from "@/components/ui/use-toast";

export default function Vacunacion() {
  const { toast } = useToast();
  const [q, setQ] = useState("");
  const [pacienteSel, setPacienteSel] = useState(null);
  const [form, setForm] = useState({ vacuna_id: "", lote: "", laboratorio: "", unidad: "u4", aplicador: "Dra. Karina Mendoza" });

  const candidatos = useMemo(() => {
    return pacientes.filter((p) =>
      !q || nombreCompleto(p).toLowerCase().includes(q.toLowerCase()) || p.curp?.includes(q)
    );
  }, [q]);

  const pendientesPaciente = (p) => {
    const aplicadas = vacunasAplicadas.filter((a) => a.paciente_id === p.id && a.es_valida);
    return esquema
      .filter((e) => e.tipo_cartilla_id === p.tipo_cartilla_id)
      .filter((e) => !aplicadas.some((a) => a.vacuna_id === e.vacuna_id && a.numero_dosis === e.numero_dosis));
  };

  const aplicar = () => {
    if (!pacienteSel || !form.vacuna_id || !form.lote) {
      toast({ title: "Faltan datos", description: "Selecciona paciente, vacuna y lote.", variant: "destructive" });
      return;
    }
    toast({ title: "Dosis registrada", description: `${nombreVacuna(Number(form.vacuna_id))} aplicada a ${nombreCompleto(pacienteSel)}.` });
    setPacienteSel(null);
    setForm({ ...form, vacuna_id: "", lote: "" });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-heading font-semibold">Vacunación</h1>
        <p className="text-muted-foreground text-sm mt-1">Registra la aplicación de dosis y revisa pendientes por paciente</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Buscador + lista */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Seleccionar paciente</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Nombre o CURP…" className="pl-9" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
            <div className="divide-y max-h-[420px] overflow-y-auto">
              {candidatos.map((p) => {
                const pend = pendientesPaciente(p).length;
                return (
                  <button
                    key={p.id}
                    onClick={() => setPacienteSel(p)}
                    className={`w-full text-left py-2.5 px-1 flex items-center justify-between hover:bg-muted/50 rounded-md ${pacienteSel?.id === p.id ? "bg-muted" : ""}`}
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-sm truncate">{nombreCompleto(p)}</p>
                      <p className="text-xs text-muted-foreground">{edadEnAnios(p.fecha_nacimiento) >= 1 ? `${edadEnAnios(p.fecha_nacimiento)} años` : `${edadMeses(p.fecha_nacimiento)} meses`}</p>
                    </div>
                    {pend > 0 ? (
                      <Badge variant="outline" className="text-amber-700 border-amber-300">{pend} pend.</Badge>
                    ) : (
                      <Badge className="bg-emerald-100 text-emerald-700">Completo</Badge>
                    )}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Formulario de aplicación */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Registrar aplicación</CardTitle>
            <CardDescription>
              {pacienteSel ? `Paciente: ${nombreCompleto(pacienteSel)}` : "Selecciona un paciente para continuar"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {pacienteSel ? (
              <>
                <div className="rounded-lg border p-3 bg-amber-50/50">
                  <p className="text-xs font-medium text-amber-800 mb-2 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" /> Dosis pendientes
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {pendientesPaciente(pacienteSel).length ? pendientesPaciente(pacienteSel).map((e) => (
                      <Badge key={e.id} variant="outline" className="bg-white">
                        {nombreVacuna(e.vacuna_id)} · {e.numero_dosis}
                      </Badge>
                    )) : <span className="text-sm text-emerald-700">Esquema completo</span>}
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>Vacuna</Label>
                    <Select value={form.vacuna_id} onValueChange={(v) => setForm({ ...form, vacuna_id: v })}>
                      <SelectTrigger><SelectValue placeholder="Selecciona…" /></SelectTrigger>
                      <SelectContent>
                        {vacunasCatalogo.map((v) => (
                          <SelectItem key={v.id} value={String(v.id)}>{v.nombre_generico} ({v.clave_censia})</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Número de dosis</Label>
                    <Input type="number" min={1} defaultValue={1} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Lote</Label>
                    <Input value={form.lote} onChange={(e) => setForm({ ...form, lote: e.target.value })} placeholder="Ej. PENT-2026-01" />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Laboratorio</Label>
                    <Input value={form.laboratorio} onChange={(e) => setForm({ ...form, laboratorio: e.target.value })} placeholder="BIRMEX" />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Unidad médica</Label>
                    <Select value={form.unidad} onValueChange={(v) => setForm({ ...form, unidad: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {unidades.map((u) => (
                          <SelectItem key={u.id} value={u.id}>{u.nombre}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Aplicador</Label>
                    <Input value={form.aplicador} onChange={(e) => setForm({ ...form, aplicador: e.target.value })} />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="outline" onClick={() => setPacienteSel(null)}>Cancelar</Button>
                  <Button onClick={aplicar}><Syringe className="w-4 h-4 mr-2" /> Registrar dosis</Button>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Syringe className="w-8 h-8 mx-auto mb-3 opacity-40" />
                <p className="text-sm">Busca y selecciona un paciente para registrar una dosis</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Aplicaciones recientes */}
      <Card>
        <CardHeader>
          <CardTitle>Aplicaciones recientes</CardTitle>
          <CardDescription>Últimas dosis registradas en el sistema</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Paciente</TableHead>
                <TableHead>Vacuna</TableHead>
                <TableHead>Dosis</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Lote</TableHead>
                <TableHead>Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {vacunasAplicadas.slice().reverse().slice(0, 8).map((a) => {
                const p = pacientes.find((x) => x.id === a.paciente_id);
                return (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">{p ? nombreCompleto(p) : "—"}</TableCell>
                    <TableCell>{nombreVacuna(a.vacuna_id)}</TableCell>
                    <TableCell>{a.numero_dosis}</TableCell>
                    <TableCell className="text-xs">{a.fecha_aplicacion}</TableCell>
                    <TableCell className="font-mono text-xs">{a.lote}</TableCell>
                    <TableCell>
                      {a.es_valida
                        ? <Badge className="bg-emerald-100 text-emerald-700"><CheckCircle2 className="w-3 h-3 mr-1" />Válida</Badge>
                        : <Badge variant="destructive">Invalidada</Badge>}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}