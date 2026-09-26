import React from "react";
import { useParams, Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from "@/components/ui/table";
import { ArrowLeft, Syringe, CalendarDays, FileText, CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import {
  pacientes, vacunasAplicadas, nombreCompleto, nombreTipoCartilla, nombreUnidad,
  nombreMunicipio, edadEnAnios, edadMeses, esquemaParaPaciente, nombreVacuna,
} from "@/lib/mockData";

const EstadoBadge = ({ estado }) => {
  if (estado === "aplicada")
    return <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100"><CheckCircle2 className="w-3 h-3 mr-1" /> Aplicada</Badge>;
  return <Badge variant="outline" className="text-amber-700 border-amber-300"><Clock className="w-3 h-3 mr-1" /> Pendiente</Badge>;
};

export default function PacienteDetalle() {
  const { id } = useParams();
  const p = pacientes.find((x) => x.id === id);

  if (!p) {
    return (
      <div className="text-center py-20">
        <AlertTriangle className="w-10 h-10 mx-auto text-muted-foreground" />
        <p className="mt-3 text-muted-foreground">Paciente no encontrado</p>
        <Link to="/pacientes"><Button variant="outline" className="mt-4">Volver a pacientes</Button></Link>
      </div>
    );
  }

  const esquema = esquemaParaPaciente(p);
  const aplicadas = esquema.filter((e) => e.estado === "aplicada").length;
  const pendientes = esquema.length - aplicadas;
  const avance = Math.round((aplicadas / esquema.length) * 100);
  const anios = edadEnAnios(p.fecha_nacimiento);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/pacientes">
          <Button variant="ghost" size="sm"><ArrowLeft className="w-4 h-4 mr-1" /> Pacientes</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-semibold">
              {p.nombre[0]}{p.ap_paterno[0]}
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-heading font-semibold">{nombreCompleto(p)}</h1>
              <p className="text-sm text-muted-foreground font-mono">{p.curp}</p>
              <div className="flex flex-wrap gap-2 mt-2">
                <Badge variant="secondary">{nombreTipoCartilla(p.tipo_cartilla_id)}</Badge>
                <Badge variant="outline">{p.sexo === "M" ? "Masculino" : "Femenino"}</Badge>
                <Badge variant="outline">{anios >= 1 ? `${anios} años` : `${edadMeses(p.fecha_nacimiento)} meses`}</Badge>
                {p.gestante_semanas && <Badge className="bg-pink-100 text-pink-700">Gestante · {p.gestante_semanas} sem</Badge>}
              </div>
            </div>
            <div className="flex gap-2">
              <Link to="/vacunacion"><Button><Syringe className="w-4 h-4 mr-2" /> Aplicar dosis</Button></Link>
              <Link to="/cartilla"><Button variant="outline"><FileText className="w-4 h-4 mr-2" /> Cartilla</Button></Link>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardDescription>Dosis aplicadas</CardDescription></CardHeader>
          <CardContent><p className="text-3xl font-heading font-semibold text-emerald-600">{aplicadas}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardDescription>Pendientes</CardDescription></CardHeader>
          <CardContent><p className="text-3xl font-heading font-semibold text-amber-600">{pendientes}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardDescription>Avance del esquema</CardDescription></CardHeader>
          <CardContent><p className="text-3xl font-heading font-semibold">{avance}%</p></CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Datos generales</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Fecha de nacimiento" value={new Date(p.fecha_nacimiento).toLocaleDateString("es-MX")} />
            <Row label="Lugar de nacimiento" value={nombreMunicipio(p.municipio_nacimiento_id)} />
            <Row label="Unidad de registro" value={nombreUnidad(p.unidad_med_registro_id)} />
            <Separator />
            <Row label="Responsable principal" value={p.responsable_principal} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Esquema de vacunación</CardTitle>
            <CardDescription>{aplicadas} de {esquema.length} dosis aplicadas</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vacuna</TableHead>
                  <TableHead>Dosis</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Estado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {esquema.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="font-medium">{e.vacuna}</TableCell>
                    <TableCell>{e.numero_dosis}{e.es_refuerzo ? " (R)" : ""}</TableCell>
                    <TableCell className="text-xs">{e.fecha_aplicacion ?? "—"}</TableCell>
                    <TableCell><EstadoBadge estado={e.estado} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-right">{value}</span>
    </div>
  );
}