import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from "@/components/ui/table";
import { Search, Plus, UserPlus } from "lucide-react";
import {
  pacientes, nombreCompleto, nombreTipoCartilla, edadEnAnios, edadMeses,
} from "@/lib/mockData";

export default function Pacientes() {
  const [q, setQ] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("todos");

  const resultados = useMemo(() => {
    return pacientes.filter((p) => {
      const matchQ =
        !q ||
        nombreCompleto(p).toLowerCase().includes(q.toLowerCase()) ||
        p.curp?.toLowerCase().includes(q.toLowerCase());
      const matchTipo = filtroTipo === "todos" || p.tipo_cartilla_id === Number(filtroTipo);
      return matchQ && matchTipo;
    });
  }, [q, filtroTipo]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-heading font-semibold">Pacientes</h1>
          <p className="text-muted-foreground text-sm mt-1">{pacientes.length} pacientes registrados</p>
        </div>
        <Button>
          <UserPlus className="w-4 h-4 mr-2" /> Nuevo paciente
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex gap-3 flex-wrap items-center">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Buscar por nombre o CURP…"
                className="pl-9"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
            <div className="flex gap-1.5">
              {[
                { v: "todos", l: "Todos" },
                { v: "1", l: "Niños" },
                { v: "2", l: "Adolescentes" },
                { v: "3", l: "Adultos" },
                { v: "4", l: "Gestantes" },
              ].map((t) => (
                <Button
                  key={t.v}
                  variant={filtroTipo === t.v ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFiltroTipo(t.v)}
                >
                  {t.l}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Paciente</TableHead>
                <TableHead>CURP</TableHead>
                <TableHead>Edad</TableHead>
                <TableHead>Sexo</TableHead>
                <TableHead>Tipo de cartilla</TableHead>
                <TableHead className="text-right">Acción</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {resultados.map((p) => {
                const anios = edadEnAnios(p.fecha_nacimiento);
                const edad = anios >= 1 ? `${anios} años` : `${edadMeses(p.fecha_nacimiento)} meses`;
                return (
                  <TableRow key={p.id}>
                    <TableCell>
                      <div className="font-medium">{nombreCompleto(p)}</div>
                      <div className="text-xs text-muted-foreground">{p.responsable_principal}</div>
                    </TableCell>
                    <TableCell className="font-mono text-xs">{p.curp}</TableCell>
                    <TableCell>{edad}</TableCell>
                    <TableCell>{p.sexo === "M" ? "Masculino" : p.sexo === "F" ? "Femenino" : "Intersexual"}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{nombreTipoCartilla(p.tipo_cartilla_id)}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Link to={`/pacientes/${p.id}`}>
                        <Button variant="ghost" size="sm">Ver detalle</Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                );
              })}
              {resultados.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                    No se encontraron pacientes
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}