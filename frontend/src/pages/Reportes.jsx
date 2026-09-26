import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Download, TrendingUp, AlertTriangle, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { coberturaMunicipios, tendenciaMensual } from "@/lib/mockData";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  LineChart, Line, Cell,
} from "recharts";

const colorPorCobertura = (v) => (v >= 90 ? "#16a34a" : v >= 75 ? "#f59e0b" : "#ef4444");

export default function Reportes() {
  const [jurisdiccion, setJurisdiccion] = useState("todas");
  const datos = jurisdiccion === "todas"
    ? coberturaMunicipios
    : coberturaMunicipios.filter((m) => m.jurisdiccion === jurisdiccion);

  const promedio = Math.round(datos.reduce((s, m) => s + m.cobertura, 0) / (datos.length || 1));
  const rezagoTotal = datos.reduce((s, m) => s + m.rezago, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-heading font-semibold">Reportes de cobertura</h1>
          <p className="text-muted-foreground text-sm mt-1">Seguimiento de cobertura y rezago vacunal</p>
        </div>
        <div className="flex gap-2">
          <Select value={jurisdiccion} onValueChange={setJurisdiccion}>
            <SelectTrigger className="w-56"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="todas">Todas las jurisdicciones</SelectItem>
              {[...new Set(coberturaMunicipios.map((m) => m.jurisdiccion))].map((j) => (
                <SelectItem key={j} value={j}>{j}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="w-4 h-4 mr-2" /> Exportar</Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Cobertura promedio</p>
                <p className="text-2xl font-heading font-semibold">{promedio}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Rezago acumulado</p>
                <p className="text-2xl font-heading font-semibold">{rezagoTotal}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-violet-50 text-violet-700 flex items-center justify-center">
                <MapPin className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Municipios evaluados</p>
                <p className="text-2xl font-heading font-semibold">{datos.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Cobertura por municipio</CardTitle>
            <CardDescription>Porcentaje de meta alcanzada</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={datos} margin={{ left: -20, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="municipio" tick={{ fontSize: 11 }} stroke="#94a3b8" interval={0} angle={-15} textAnchor="end" height={60} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} formatter={(v) => [`${v}%`, "Cobertura"]} />
                  <Bar dataKey="cobertura" radius={[6, 6, 0, 0]}>
                    {datos.map((m) => (
                      <Cell key={m.municipio} fill={colorPorCobertura(m.cobertura)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tendencia mensual</CardTitle>
            <CardDescription>Evolución de la cobertura</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={tendenciaMensual} margin={{ left: -20, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} formatter={(v) => [`${v}%`, "Cobertura"]} />
                  <Line type="monotone" dataKey="cobertura" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Detalle por municipio</CardTitle>
          <CardDescription>Trazabilidad de cobertura y rezago</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Municipio</TableHead>
                <TableHead>Jurisdicción</TableHead>
                <TableHead>Aplicadas</TableHead>
                <TableHead>Rezago</TableHead>
                <TableHead className="w-48">Cobertura</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datos.map((m) => (
                <TableRow key={m.municipio}>
                  <TableCell className="font-medium">{m.municipio}</TableCell>
                  <TableCell className="text-muted-foreground">{m.jurisdiccion}</TableCell>
                  <TableCell>{m.aplicadas}</TableCell>
                  <TableCell>
                    <span className={m.rezago > 20 ? "text-red-600 font-medium" : ""}>{m.rezago}</span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={m.cobertura} className="h-2 flex-1" />
                      <span className="text-xs font-medium w-10 text-right">{m.cobertura}%</span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}