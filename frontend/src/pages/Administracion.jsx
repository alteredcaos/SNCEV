import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UserPlus, ShieldCheck, Search } from "lucide-react";
import { usuarios, roles } from "@/lib/mockData";
import { useToast } from "@/components/ui/use-toast";

const iniciales = (n) => n.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();

export default function Administracion() {
  const { toast } = useToast();
  const [q, setQ] = useState("");
  const [lista, setLista] = useState(usuarios);
  const [nuevo, setNuevo] = useState({ nombre: "", email: "", rol: "Vacunador", unidad: "" });
  const [open, setOpen] = useState(false);

  const filtrados = lista.filter(
    (u) => !q || u.nombre.toLowerCase().includes(q.toLowerCase()) || u.email.includes(q)
  );

  const toggleActivo = (id) => {
    setLista(lista.map((u) => (u.id === id ? { ...u, activo: !u.activo } : u)));
  };

  const crear = () => {
    if (!nuevo.nombre || !nuevo.email) {
      toast({ title: "Nombre y correo son obligatorios", variant: "destructive" });
      return;
    }
    const id = "us" + Date.now();
    setLista([
      ...lista,
      { id, username: nuevo.email.split("@")[0], nombre: nuevo.nombre, email: nuevo.email, rol: nuevo.rol, unidad: nuevo.unidad || "—", activo: true, ultimo_acceso: "—" },
    ]);
    toast({ title: "Usuario creado", description: "Se envió invitación por correo." });
    setNuevo({ nombre: "", email: "", rol: "Vacunador", unidad: "" });
    setOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-heading font-semibold">Administración</h1>
          <p className="text-muted-foreground text-sm mt-1">Usuarios, roles y permisos del sistema</p>
        </div>
        <Button onClick={() => setOpen(!open)}>
          <UserPlus className="w-4 h-4 mr-2" /> Nuevo usuario
        </Button>
      </div>

      {open && (
        <Card>
          <CardHeader><CardTitle className="text-base">Crear usuario</CardTitle></CardHeader>
          <CardContent className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <Label>Nombre completo</Label>
              <Input value={nuevo.nombre} onChange={(e) => setNuevo({ ...nuevo, nombre: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label>Correo</Label>
              <Input type="email" value={nuevo.email} onChange={(e) => setNuevo({ ...nuevo, email: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label>Rol</Label>
              <Select value={nuevo.rol} onValueChange={(v) => setNuevo({ ...nuevo, rol: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {roles.map((r) => (
                    <SelectItem key={r.nombre} value={r.nombre}>{r.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Unidad / Jurisdicción</Label>
              <Input value={nuevo.unidad} onChange={(e) => setNuevo({ ...nuevo, unidad: e.target.value })} />
            </div>
            <div className="sm:col-span-2 lg:col-span-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
              <Button onClick={crear}>Crear usuario</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="usuarios">
        <TabsList>
          <TabsTrigger value="usuarios">Usuarios</TabsTrigger>
          <TabsTrigger value="roles">Roles y permisos</TabsTrigger>
        </TabsList>

        <TabsContent value="usuarios" className="space-y-4">
          <div className="relative max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Buscar usuario…" className="pl-9" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Unidad</TableHead>
                    <TableHead>Último acceso</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acción</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtrados.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="w-9 h-9"><AvatarFallback>{iniciales(u.nombre)}</AvatarFallback></Avatar>
                          <div>
                            <p className="font-medium">{u.nombre}</p>
                            <p className="text-xs text-muted-foreground">{u.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell><Badge variant="secondary">{u.rol}</Badge></TableCell>
                      <TableCell className="text-muted-foreground">{u.unidad}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{u.ultimo_acceso}</TableCell>
                      <TableCell>
                        {u.activo ? <Badge className="bg-emerald-100 text-emerald-700">Activo</Badge> : <Badge variant="outline">Inactivo</Badge>}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => toggleActivo(u.id)}>
                          {u.activo ? "Desactivar" : "Activar"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="roles" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            {roles.map((r) => (
              <Card key={r.nombre}>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-primary" />
                    <CardTitle className="text-base">{r.nombre}</CardTitle>
                  </div>
                  <CardDescription>{r.descripcion}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground mb-2">Permisos</p>
                  <div className="flex flex-wrap gap-1.5">
                    {r.permisos.map((p) => (
                      <Badge key={p} variant="outline" className="capitalize">{p === "*" ? "Todos" : p}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}