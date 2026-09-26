import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { CalendarDays, Plus, Clock, MapPin, Syringe } from "lucide-react";
import {
  pacientes, citas, vacunasCatalogo, unidades,
  nombreCompleto, nombreVacuna, nombreUnidad, edadEnAnios,
} from "@/lib/mockData";
import { useToast } from "@/components/ui/use-toast";

export default function Citas() {
  const { toast } = useToast();
  const [lista, setLista] = useState(citas);
  const [nueva, setNueva] = useState({ paciente_id: "", fecha: "", hora: "", unidad: "u4", vacuna_id: "" });
  const [open, setOpen] = useState(false);

  const agrupadas = lista.reduce((acc, c) => {
    (acc[c.fecha] = acc[c.fecha] || []).push(c);
    return acc;
  }, {});
  const fechas = Object.keys(agrupadas).sort();

  const crear = () => {
    if (!nueva.paciente_id || !nueva.fecha || !nueva.hora || !nueva.vacuna_id) {
      toast({ title: "Completa todos los campos", variant: "destructive" });
      return;
    }
    const id = "c" + Date.now();
    setLista([...lista, { id, ...nueva, estado: "programada", notas: "" }]);
    toast({ title: "Cita programada", description: "La cita se agregó a la agenda." });
    setNueva({ paciente_id: "", fecha: "", hora: "", unidad: "u4", vacuna_id: "" });
    setOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-heading font-semibold">Citas</h1>
          <p className="text-muted-foreground text-sm mt-1">{lista.length} citas programadas</p>
        </div>
        <Button onClick={() => setOpen(!open)}>
          <Plus className="w-4 h-4 mr-2" /> Nueva cita
        </Button>
      </div>

      {open && (
        <Card>
          <CardHeader><CardTitle className="text-base">Programar nueva cita</CardTitle></CardHeader>
          <CardContent className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <Label>Paciente</Label>
              <Select value={nueva.paciente_id} onValueChange={(v) => setNueva({ ...nueva, paciente_id: v })}>
                <SelectTrigger><SelectValue placeholder="Selecciona…" /></SelectTrigger>
                <SelectContent>
                  {pacientes.map((p) => (
                    <SelectItem key={p.id} value={p.id}>{nombreCompleto(p)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Vacuna</Label>
              <Select value={nueva.vacuna_id} onValueChange={(v) => setNueva({ ...nueva, vacuna_id: v })}>
                <SelectTrigger><SelectValue placeholder="Selecciona…" /></SelectTrigger>
                <SelectContent>
                  {vacunasCatalogo.map((v) => (
                    <SelectItem key={v.id} value={String(v.id)}>{v.nombre_generico}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Unidad</Label>
              <Select value={nueva.unidad} onValueChange={(v) => setNueva({ ...nueva, unidad: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {unidades.map((u) => (
                    <SelectItem key={u.id} value={u.id}>{u.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Fecha</Label>
              <Input type="date" value={nueva.fecha} onChange={(e) => setNueva({ ...nueva, fecha: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label>Hora</Label>
              <Input type="time" value={nueva.hora} onChange={(e) => setNueva({ ...nueva, hora: e.target.value })} />
            </div>
            <div className="flex items-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
              <Button onClick={crear}>Guardar</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-6">
        {fechas.map((f) => (
          <Card key={f}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <CalendarDays className="w-4 h-4 text-muted-foreground" />
                {new Date(f + "T00:00").toLocaleDateString("es-MX", { weekday: "long", day: "numeric", month: "long" })}
              </CardTitle>
              <CardDescription>{agrupadas[f].length} citas</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {agrupadas[f].sort((a, b) => a.hora.localeCompare(b.hora)).map((c) => {
                const p = pacientes.find((x) => x.id === c.paciente_id);
                return (
                  <div key={c.id} className="flex items-center gap-4 rounded-lg border p-3 hover:bg-muted/40">
                    <div className="flex items-center gap-2 w-20 text-sm font-medium">
                      <Clock className="w-4 h-4 text-muted-foreground" /> {c.hora}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{p ? nombreCompleto(p) : "—"}</p>
                      <p className="text-xs text-muted-foreground flex items-center gap-2 flex-wrap">
                        <Syringe className="w-3 h-3" /> {nombreVacuna(c.vacuna_id)} · dosis {c.numero_dosis}
                        <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {nombreUnidad(c.unidad_medica_id)}</span>
                        {p && <span>· {edadEnAnios(p.fecha_nacimiento)} años</span>}
                      </p>
                    </div>
                    <Badge variant="outline" className="capitalize">{c.estado}</Badge>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}