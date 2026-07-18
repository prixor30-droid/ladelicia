-- Nómina: empleados, ausencias y pagos quincenales con bono semestral

create table if not exists nomina_empleados (
  id uuid primary key default gen_random_uuid(),
  nombre text not null,
  salario_mensual numeric not null,
  fecha_ingreso date not null,
  tipo text not null default 'fijo',        -- 'fijo' (quincena por días trabajados) o 'variable' (monto manual, ej. propietaria)
  bono_semestral boolean not null default true,
  activo boolean not null default true,
  creado_en timestamptz not null default now()
);
alter table nomina_empleados enable row level security;
create policy "nomina_empleados_select" on nomina_empleados for select using (true);
create policy "nomina_empleados_insert" on nomina_empleados for insert with check (true);
create policy "nomina_empleados_update" on nomina_empleados for update using (true);
create policy "nomina_empleados_delete" on nomina_empleados for delete using (true);

create table if not exists nomina_ausencias (
  id uuid primary key default gen_random_uuid(),
  empleado_id uuid not null references nomina_empleados(id),
  fecha date not null,
  motivo text not null,
  creado_en timestamptz not null default now()
);
alter table nomina_ausencias enable row level security;
create policy "nomina_ausencias_select" on nomina_ausencias for select using (true);
create policy "nomina_ausencias_insert" on nomina_ausencias for insert with check (true);
create policy "nomina_ausencias_update" on nomina_ausencias for update using (true);
create policy "nomina_ausencias_delete" on nomina_ausencias for delete using (true);

create table if not exists nomina_pagos (
  id uuid primary key default gen_random_uuid(),
  empleado_id uuid not null references nomina_empleados(id),
  periodo_inicio date not null,
  periodo_fin date not null,
  dias_trabajados numeric,
  salario_diario numeric,
  monto_base numeric not null,
  bono_semestral numeric not null default 0,
  semestre_num integer,
  total_pagado numeric not null,
  fecha_pago date not null,
  pagado_por text,
  creado_en timestamptz not null default now()
);
alter table nomina_pagos enable row level security;
create policy "nomina_pagos_select" on nomina_pagos for select using (true);
create policy "nomina_pagos_insert" on nomina_pagos for insert with check (true);
create policy "nomina_pagos_update" on nomina_pagos for update using (true);
create policy "nomina_pagos_delete" on nomina_pagos for delete using (true);

-- Empleados actuales. Todos entraron el 1 de enero de 2026, salvo las excepciones indicadas.
-- Maria Yandun es la propietaria: tipo 'variable' (monto se ajusta a mano cada quincena) y sin bono semestral.
insert into nomina_empleados (nombre, salario_mensual, fecha_ingreso, tipo, bono_semestral, activo) values
('Nixon Urbano',     1450000, '2026-01-01', 'fijo',     true,  true),
('Ovidio Tepud',     1450000, '2026-01-01', 'fijo',     true,  true),
('Andrea Bastidas',   700000, '2026-01-01', 'fijo',     true,  true),
('Andrea Revelo',    1200000, '2026-01-01', 'fijo',     true,  true),
('Javier Villa',     1500000, '2026-01-01', 'fijo',     true,  true),
('David Causil',     1500000, '2026-03-01', 'fijo',     true,  true),
('Daniela Pistala',  1200000, '2026-01-01', 'fijo',     true,  true),
('Yoselin Villa',    1000000, '2026-01-14', 'fijo',     true,  true),
('Sofia Quitiaquez', 1000000, '2026-01-01', 'fijo',     true,  true),
('Andre Ipial',      1500000, '2026-01-01', 'fijo',     true,  true),
('Jorge Ipial',      2500000, '2026-01-01', 'fijo',     true,  true),
('Edison Lozano',    1600000, '2026-01-01', 'fijo',     true,  true),
('Alex Chapuel',     1500000, '2026-01-01', 'fijo',     true,  true),
('Maria Yandun',     5000000, '2026-01-01', 'variable', false, true);
