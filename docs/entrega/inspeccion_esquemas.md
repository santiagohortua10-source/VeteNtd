# Inspecci?n de esquemas PawCare

Fecha de inspecci?n: 2026-11-22. Las consultas fueron de s?lo lectura sobre information_schema y COUNT(*).

## Compatibilidad

Se compararon tablas, columnas y tipos, restricciones, PK/FK, ?ndices y vistas de `ahp_veterinaria` y `veterinaria`. El conjunto es id?ntico: 15 tablas, 96 columnas, 38 entradas de ?ndice y 19 claves for?neas. Ambas usan InnoDB. No se detectaron vistas ni triggers antes de instalar.

## Conteo de filas (s?lo lectura)

| Tabla | ahp_veterinaria | veterinaria | Faltan para llegar a 11 en ahp_veterinaria |
|---|---:|---:|---:|
| catalogo_servicios | 5 | 5 | 6 |
| cliente | 5 | 5 | 6 |
| detalle_factura | 3 | 3 | 8 |
| empleado | 4 | 4 | 7 |
| facturacion | 2 | 2 | 9 |
| historial_clinico | 7 | 7 | 4 |
| horario | 20 | 20 | 0 |
| mascota | 7 | 7 | 4 |
| pago | 2 | 2 | 9 |
| pedidos | 1 | 1 | 10 |
| pedido_detalle | 2 | 2 | 9 |
| productos | 5 | 5 | 6 |
| reservas | 14 | 14 | 0 |
| responsable_alterno | 0 | 0 | 11 |
| usuarios | 1 | 1 | 10 |

La columna de faltantes usa como meta 11 filas (m?s de 10). El conteo se hizo con `COUNT(*)` en cada tabla de `ahp_veterinaria`; no se extrapol? desde `veterinaria`.

## Interpretaci?n

Las estructuras permiten usar el c?digo existente en cualquiera de las bases. La configuraci?n privada de este equipo mantiene `DB_NAME=veterinaria`; no se modific?. Para la entrega, cambia esa variable de forma consciente a `ahp_veterinaria` despu?s de validar una copia y mantener respaldo.

El script `seed_complementario.sql` se conserv? y no se ejecut?. Los scripts de auditor?a creados aqu? tampoco se ejecutaron en ninguna base.
