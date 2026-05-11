:-dynamic posicao/3.
:-dynamic memory/3.
:-dynamic visitado/2.
:-dynamic certeza/2.
:-dynamic energia/1.
:-dynamic pontuacao/1.
:-dynamic tile/3.
:-dynamic map_size/2.

delete([], _, []).
delete([Elem|Tail], Del, Result) :-
    (   \+ Elem \= Del
    ->  delete(Tail, Del, Result)
    ;   Result = [Elem|Rest],
        delete(Tail, Del, Rest)
    ).

reset_game :- retractall(memory(_,_,_)),
              retractall(visitado(_,_)),
              retractall(certeza(_,_)),
              retractall(energia(_)),
              retractall(pontuacao(_)),
              retractall(posicao(_,_,_)),
              assert(energia(100)),
              assert(pontuacao(0)),
              assert(posicao(1,1,norte)).

:-reset_game.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Controle de Status
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

atualiza_pontuacao(X) :- pontuacao(P), retract(pontuacao(P)), NP is P + X, assert(pontuacao(NP)), !.

atualiza_energia(N) :- energia(E), retract(energia(E)), NE is E + N,
    (
        (NE =< 0, assert(energia(0)), posicao(X,Y,_), retract(posicao(_,_,_)), assert(posicao(X,Y,morto)), !);
        (NE > 100, assert(energia(100)), !);
        (NE > 0, assert(energia(NE)), !)
    ).

% Poco: morte instantanea
verifica_player :- posicao(X,Y,_), tile(X,Y,'P'),
    atualiza_energia(-100), atualiza_pontuacao(-1000), !.
% Inimigo grande (D): -50 energia e -50 pts
verifica_player :- posicao(X,Y,_), tile(X,Y,'D'),
    atualiza_energia(-50), atualiza_pontuacao(-50), !.
% Inimigo pequeno (d): -20 energia e -20 pts
verifica_player :- posicao(X,Y,_), tile(X,Y,'d'),
    atualiza_energia(-20), atualiza_pontuacao(-20), !.
% Teleporter (T): teletransporta para posicao aleatoria
verifica_player :- posicao(X,Y,Z), tile(X,Y,'T'),
    map_size(SX,SY), random_between(1,SX,NX), random_between(1,SY,NY),
    retract(posicao(X,Y,Z)), assert(posicao(NX,NY,Z)),
    atualiza_obs, verifica_player, !.
verifica_player :- true.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Comandos
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

virar_direita :- posicao(X,Y,norte), retract(posicao(_,_,_)), assert(posicao(X,Y,leste)),  atualiza_pontuacao(-1), !.
virar_direita :- posicao(X,Y,oeste), retract(posicao(_,_,_)), assert(posicao(X,Y,norte)), atualiza_pontuacao(-1), !.
virar_direita :- posicao(X,Y,sul),   retract(posicao(_,_,_)), assert(posicao(X,Y,oeste)), atualiza_pontuacao(-1), !.
virar_direita :- posicao(X,Y,leste), retract(posicao(_,_,_)), assert(posicao(X,Y,sul)),   atualiza_pontuacao(-1), !.

virar_esquerda :- posicao(X,Y,norte), retract(posicao(_,_,_)), assert(posicao(X,Y,oeste)), atualiza_pontuacao(-1), !.
virar_esquerda :- posicao(X,Y,oeste), retract(posicao(_,_,_)), assert(posicao(X,Y,sul)),   atualiza_pontuacao(-1), !.
virar_esquerda :- posicao(X,Y,sul),   retract(posicao(_,_,_)), assert(posicao(X,Y,leste)), atualiza_pontuacao(-1), !.
virar_esquerda :- posicao(X,Y,leste), retract(posicao(_,_,_)), assert(posicao(X,Y,norte)), atualiza_pontuacao(-1), !.

andar :- posicao(X,Y,P), P=norte, map_size(_,MAX_Y), Y < MAX_Y, YY is Y + 1,
         retract(posicao(X,Y,_)), assert(posicao(X,YY,P)),
         set_real(X,YY),
         ((retract(visitado(X,Y)), assert(visitado(X,Y))); assert(visitado(X,Y))),
         atualiza_pontuacao(-1), !.
andar :- posicao(X,Y,P), P=sul, Y > 1, YY is Y - 1,
         retract(posicao(X,Y,_)), assert(posicao(X,YY,P)),
         set_real(X,YY),
         ((retract(visitado(X,Y)), assert(visitado(X,Y))); assert(visitado(X,Y))),
         atualiza_pontuacao(-1), !.
andar :- posicao(X,Y,P), P=leste, map_size(MAX_X,_), X < MAX_X, XX is X + 1,
         retract(posicao(X,Y,_)), assert(posicao(XX,Y,P)),
         set_real(XX,Y),
         ((retract(visitado(X,Y)), assert(visitado(X,Y))); assert(visitado(X,Y))),
         atualiza_pontuacao(-1), !.
andar :- posicao(X,Y,P), P=oeste, X > 1, XX is X - 1,
         retract(posicao(X,Y,_)), assert(posicao(XX,Y,P)),
         set_real(XX,Y),
         ((retract(visitado(X,Y)), assert(visitado(X,Y))); assert(visitado(X,Y))),
         atualiza_pontuacao(-1), !.

% Pegar ouro: +1000 pts (custo -1 incluso)
pegar :- posicao(X,Y,_), tile(X,Y,'O'),
         retract(tile(X,Y,'O')), assert(tile(X,Y,'')),
         atualiza_pontuacao(-1), atualiza_pontuacao(1000), set_real(X,Y), !.
% Pegar powerup: +20 energia (custo -1 incluso)
pegar :- posicao(X,Y,_), tile(X,Y,'U'),
         retract(tile(X,Y,'U')), assert(tile(X,Y,'')),
         atualiza_pontuacao(-1), atualiza_energia(20), set_real(X,Y), !.
pegar :- atualiza_pontuacao(-1), !.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Funcoes Auxiliares de navegacao e observacao
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

adjacente(X,Y) :- posicao(PX,Y,_), map_size(MAX_X,_), PX < MAX_X, X is PX + 1.
adjacente(X,Y) :- posicao(PX,Y,_), PX > 1, X is PX - 1.
adjacente(X,Y) :- posicao(X,PY,_), map_size(_,MAX_Y), PY < MAX_Y, Y is PY + 1.
adjacente(X,Y) :- posicao(X,PY,_), PY > 1, Y is PY - 1.

adjacentes(L) :- findall(Z, (adjacente(X,Y), tile(X,Y,Z)), L).

observacao_loc(brilho,L) :- member('O',L).
observacao_loc(reflexo,L) :- member('U',L).

% Sensores de adjacencia:
%   brisa  -> poco (P)
%   flash  -> teleporter/morcego (T)
%   passos -> inimigo grande (D) ou pequeno (d)
observacao_adj(brisa,L)  :- member('P',L).
observacao_adj(flash,L)  :- member('T',L).
observacao_adj(passos,L) :- member('D',L).
observacao_adj(passos,L) :- member('d',L).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Tratamento de KB e observacoes
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

atualiza_obs :- adj_cand_obs(LP), observacoes(LO), iter_pos_list(LP,LO),
                observacao_certeza, observacao_vazia.

adj_cand_obs(L) :- findall((X,Y), (adjacente(X,Y), \+visitado(X,Y)), L).

observacoes(X) :- adjacentes(L), findall(Y, observacao_adj(Y,L), X).

iter_pos_list([], _) :- !.
iter_pos_list([H|T], LO) :-
    H=(X,Y),
    ((corrige_observacoes_antigas(X,Y,LO), !); adiciona_observacoes(X,Y,LO)),
    iter_pos_list(T,LO).

corrige_observacoes_antigas(X,Y,[]) :- \+certeza(X,Y), memory(X,Y,[]).
corrige_observacoes_antigas(X,Y,LO) :-
    \+certeza(X,Y), \+memory(X,Y,[]), memory(X,Y,LM),
    intersection(LO,LM,L),
    retract(memory(X,Y,LM)), assert(memory(X,Y,L)).

adiciona_observacoes(X,Y,_)  :- certeza(X,Y), !.
adiciona_observacoes(X,Y,LO) :- \+certeza(X,Y), \+memory(X,Y,_), assert(memory(X,Y,LO)).

% Deducao: se existe apenas um candidato adjacente para uma observacao, e certeza
observacao_certeza :-
    observacao_certeza(brisa),
    observacao_certeza(flash),
    observacao_certeza(passos).

observacao_certeza(Z) :-
    findall((X,Y), (adjacente(X,Y),
        ((\+visitado(X,Y), \+certeza(X,Y)); (certeza(X,Y), memory(X,Y,[Z]))),
        memory(X,Y,[Z])), L),
    ((length(L,1), L=[(XX,YY)], assert(certeza(XX,YY)), !); true).

observacao_vazia :- adj_cand_obs(LP), observacao_vazia(LP).
observacao_vazia([]) :- !.
observacao_vazia([H|T]) :-
    H=(X,Y),
    ((memory(X,Y,[]), \+certeza(X,Y), assert(certeza(X,Y)), !); true),
    observacao_vazia(T).

% Ao visitar celula, registra conteudo real do mapa na base de conhecimento
set_real(X,Y) :-
    ((retract(certeza(X,Y)), assert(certeza(X,Y)), !); assert(certeza(X,Y))),
    set_real2(X,Y), !.
set_real2(X,Y) :- tile(X,Y,'P'), ((retract(memory(X,Y,_)), assert(memory(X,Y,[brisa])),  !); assert(memory(X,Y,[brisa]))),  !.
set_real2(X,Y) :- tile(X,Y,'O'), ((retract(memory(X,Y,_)), assert(memory(X,Y,[brilho])), !); assert(memory(X,Y,[brilho]))), !.
set_real2(X,Y) :- tile(X,Y,'T'), ((retract(memory(X,Y,_)), assert(memory(X,Y,[flash])),  !); assert(memory(X,Y,[flash]))),  !.
set_real2(X,Y) :- ((tile(X,Y,'D'), !); tile(X,Y,'d')),
                  ((retract(memory(X,Y,_)), assert(memory(X,Y,[passos])), !); assert(memory(X,Y,[passos]))), !.
set_real2(X,Y) :- tile(X,Y,'U'), ((retract(memory(X,Y,_)), assert(memory(X,Y,[reflexo])), !); assert(memory(X,Y,[reflexo]))), !.
set_real2(X,Y) :- tile(X,Y,''),  ((retract(memory(X,Y,_)), assert(memory(X,Y,[])),        !); assert(memory(X,Y,[]))),        !.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Logica de Decisao do Agente
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Celula segura para transitar (visitada OU certeza + sem hazards)
celula_segura(X,Y) :- visitado(X,Y).
celula_segura(X,Y) :- certeza(X,Y), memory(X,Y,[]).

% Celula confirmadamente perigosa
celula_perigosa(X,Y) :-
    certeza(X,Y), memory(X,Y,L),
    (member(brisa,L) ; member(passos,L) ; member(flash,L)).

% Celula boa para explorar: inferida segura, ainda nao visitada
celula_explorar(GX,GY) :-
    certeza(GX,GY), memory(GX,GY,[]), \+visitado(GX,GY),
    map_size(MX,MY), GX >= 1, GX =< MX, GY >= 1, GY =< MY.

ha_celula_explorar :- celula_explorar(_,_), !.

% Escolhe proximo objetivo de navegacao (consultado pelo Python para o A*)
% Prioridade 1: explorar celula segura nao visitada
escolhe_objetivo(GX,GY) :-
    celula_explorar(GX,GY), !.
% Prioridade 2: energia critica -> voltar ao inicio para encerrar
escolhe_objetivo(1,1) :-
    energia(E), E < 30, !.
% Prioridade 3: exploracao esgotada -> voltar ao inicio
escolhe_objetivo(1,1) :-
    \+ha_celula_explorar, !.
% Prioridade 4: arriscar celula adjacente desconhecida nao confirmadamente perigosa
escolhe_objetivo(GX,GY) :-
    posicao(PX,PY,_),
    (GX is PX+1, GY=PY ;
     GX is PX-1, GY=PY ;
     GX=PX, GY is PY+1 ;
     GX=PX, GY is PY-1),
    map_size(MX,MY), GX >= 1, GX =< MX, GY >= 1, GY =< MY,
    \+visitado(GX,GY), \+celula_perigosa(GX,GY), !.

% executa_acao: pegar se ha item na posicao atual; caso contrario Python usa escolhe_objetivo
executa_acao(pegar)   :- posicao(X,Y,_), (tile(X,Y,'O') ; tile(X,Y,'U')), !.
executa_acao(explorar) :- !.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Mostra mapa real
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

show_player(X,Y) :- posicao(X,Y,norte), write('^'), !.
show_player(X,Y) :- posicao(X,Y,oeste), write('<'), !.
show_player(X,Y) :- posicao(X,Y,leste), write('>'), !.
show_player(X,Y) :- posicao(X,Y,sul),   write('v'), !.
show_player(X,Y) :- posicao(X,Y,morto), write('+'), !.

show_position(X,Y) :-
    (show_player(X,Y); write(' ')),
    tile(X,Y,Z), ((Z='', write(' ')); write(Z)), !.

show_map :- map_size(_,MAX_Y), show_map(1,MAX_Y), !.
show_map(X,Y) :- Y >= 1, map_size(MAX_X,_), X =< MAX_X,
    show_position(X,Y), write(' | '), XX is X+1, show_map(XX,Y), !.
show_map(X,Y) :- Y >= 1, map_size(X,_), YY is Y-1, write(Y), nl, show_map(1,YY), !.
show_map(_,0) :- energia(E), pontuacao(P), write('E: '), write(E), write('   P: '), write(P), !.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Mostra mapa conhecido
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

show_mem_info(X,Y) :- memory(X,Y,Z),
    ((visitado(X,Y), write('.'), !); (\+certeza(X,Y), write('?'), !); (certeza(X,Y), write('!'))),
    ((member(brisa,Z),  write('P')); write(' ')),
    ((member(flash,Z),  write('T')); write(' ')),
    ((member(brilho,Z), write('O')); write(' ')),
    ((member(passos,Z), write('D')); write(' ')),
    ((member(reflexo,Z),write('U')); write(' ')), !.

show_mem_info(X,Y) :- \+memory(X,Y,[]),
    ((visitado(X,Y), write('.'), !); (\+certeza(X,Y), write('?'), !); (certeza(X,Y), write('!'))),
    write('     '), !.

show_mem_position(X,Y) :- posicao(X,Y,_),
    ((visitado(X,Y), write('.'), !); (certeza(X,Y), write('!'), !); write(' ')),
    write(' '), show_player(X,Y),
    ((memory(X,Y,Z),
      ((member(brilho,Z), write('O')); write(' ')),
      ((member(passos,Z), write('D')); write(' ')),
      ((member(reflexo,Z),write('U')); write(' ')), !);
     (write('   '), !)).

show_mem_position(X,Y) :- show_mem_info(X,Y), !.

show_mem :- map_size(_,MAX_Y), show_mem(1,MAX_Y), !.
show_mem(X,Y) :- Y >= 1, map_size(MAX_X,_), X =< MAX_X,
    show_mem_position(X,Y), write('|'), XX is X+1, show_mem(XX,Y), !.
show_mem(X,Y) :- Y >= 1, map_size(X,_), YY is Y-1, write(Y), nl, show_mem(1,YY), !.
show_mem(_,0) :- energia(E), pontuacao(P), write('E: '), write(E), write('   P: '), write(P), !.
