/* Motor de reglas para recomendar vehículos compatibles con un pedido.
   Entrada/salida JSON por stdin/stdout para integrar SWI-Prolog con Python. */
:- use_module(library(http/json)).
:- dynamic vehiculo/5.

registrar_vehiculo(V) :-
    assertz(vehiculo(V.patente, V.capacidad_maxima, V.estado,
                     V.tiene_conductor, V.tiene_pedido_activo)).

candidato(VolumenPedido, Patente, Capacidad, Restante) :-
    vehiculo(Patente, Capacidad, "Disponible", true, false),
    Capacidad >= VolumenPedido,
    Restante is Capacidad - VolumenPedido.

comparar(Orden, A, B) :-
    ( A.espacio_restante < B.espacio_restante -> Orden = '<'
    ; A.espacio_restante > B.espacio_restante -> Orden = '>'
    ; compare(Orden, A.patente, B.patente)
    ).

main :-
    json_read_dict(user_input, Datos),
    retractall(vehiculo(_, _, _, _, _)),
    maplist(registrar_vehiculo, Datos.vehiculos),
    findall(_{patente:Patente, capacidad_maxima:Capacidad,
             espacio_restante:Restante},
            candidato(Datos.volumen_pedido, Patente, Capacidad, Restante),
            Candidatos),
    predsort(comparar, Candidatos, Ordenados),
    json_write_dict(current_output, Ordenados),
    nl.
