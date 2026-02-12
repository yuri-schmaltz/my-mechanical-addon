# RC Mechanism Generator

Addon Blender (3.6 LTS e 4.x) para gerar e fabricar mecanismos RC print-ready:

- suspensao double wishbone (LCA/UCA + knuckle opcional),
- estercamento (servo horn + tie rods),
- coilover com inferencia de shock mounts,
- checks DFM basicos,
- export manufacturing pack (STL/3MF + BOM + assembly notes).

## Documentacao completa

A documentacao completa da aplicacao esta em `docs/README.md`, incluindo:

- visao geral funcional e tecnica,
- guia de usuario,
- arquitetura do sistema,
- referencia de operadores e propriedades,
- guia de desenvolvimento e release.

## Estrutura

- `rc_mechanism_generator/__init__.py`
- `rc_mechanism_generator/properties.py`
- `rc_mechanism_generator/ui.py`
- `rc_mechanism_generator/operators.py`
- `rc_mechanism_generator/geometry/`
- `rc_mechanism_generator/dfm/`
- `rc_mechanism_generator/utils/`
- `examples/create_mock_scene.py`
- `examples/rcgen_mock_scene.blend`

## Instalacao

1. Comprima a pasta `rc_mechanism_generator` em zip (ou use `dist/RC_Mechanism_Generator.zip`).
2. Blender: `Edit > Preferences > Add-ons > Install...`.
3. Ative `RC Mechanism Generator`.
4. Abra `3D Viewport > Sidebar (N) > RC`.

## Checklist obrigatorio

### Referencias obrigatorias

- `Chassis`
- `Wheel_L`
- `Wheel_R`
- `Servo`

### Referencias opcionais

- `Tire_L`, `Tire_R`
- `WheelWell_L`, `WheelWell_R`
- `Hub_L`, `Hub_R`
- `Upright_L`, `Upright_R`
- `ServoHorn`
- `Rear Axle Center` (Ackermann auto)

### Hardpoints obrigatorios (por lado L/R)

- `LCA_In_Front_[L/R]`
- `LCA_In_Rear_[L/R]`
- `LCA_Out_[L/R]`
- `UCA_In_Front_[L/R]`
- `UCA_In_Rear_[L/R]`
- `UCA_Out_[L/R]`
- `SteeringArm_Point_[L/R]`

Se faltar item obrigatorio, o operador bloqueia modulo e reporta exatamente os nomes ausentes.

## Shock mounts (inferencia e override)

- Inferidos automaticamente: `RC_ShockTop_[L/R]`, `RC_ShockBottom_[L/R]`.
- Override manual: ative `Use Manual Shock Mounts` e aponte `Shock Top/Bottom`.
- `Reinfer Shock Mounts` recria mounts gerados.

## Tolerancias globais

Em `Tolerancias`:

- `clearance_sliding_mm`
- `clearance_press_mm`
- `hole_oversize_mm`
- `nut_trap_clearance_mm`
- `insert_pocket_clearance_mm`

Esses valores alimentam os parametros de interface mecanica usados pelos geradores.

## Fluxo recomendado

1. Preencha `Projeto`, `Referencias` e `Hardpoints`.
   Opcional: use `Auto Capture By Name` para preencher automaticamente por nomes comuns.
   `Auto-Capture Prefix` permite capturar nomes com prefixo (ex.: `car01_wheel_l`).
   `Auto-Capture Scope` permite limitar para objetos de colecoes selecionadas/ativa.
2. Rode `Validate References` e `Validate Hardpoints`.
3. Use `Generate All`.
4. Ajuste parametros e rode `Update All` quando mover refs/hardpoints.
5. Rode `Run Printability Checks`.
6. Rode `Export Manufacturing Pack`.

## Export Manufacturing Pack

Gera pasta em `export_dir/rcgen_id/` contendo:

- STL por peca (`export_stl`),
- 3MF por peca (`export_3mf`, quando operador disponivel),
- auto-split de pecas oversized em `PART_A/PART_B` + `PIN_1/PIN_2` quando `auto_split_large_parts` estiver ativo,
- aplicacao de sockets por boolean nas metades splitadas para encaixe dos pinos,
- perfil anti-rotacao configuravel em `Split Key Profile` (`ROUND`, `HEX`, `D-Flat`),
- orientacao do perfil `HEX/D` automatica pelo eixo estimado de maior esforco da peca (excluindo eixo de corte),
- `Split Orientation Bias` para preferir alinhamento com `Chassis Forward` ou `Chassis Right` no perfil anti-rotacao,
- `BOM.csv` e `BOM.json`,
- `ASSEMBLY.md` com sequencia, tolerancias e orientacao sugerida,
- `manifest.json` com lista de arquivos exportados.

## DFM checks (MVP)

`Run Printability Checks` valida:

- malha non-manifold (erro),
- dimensao minima abaixo de `min_wall_mm` (erro),
- furo perto da borda (warning aproximado),
- overhang acima de limite (warning aproximado),
- peca maior que volume de impressao (warning/erro conforme config),
- interferencia com wheel well por bbox (warning).

## Exemplo

Script de cena mock:

```bash
blender --factory-startup --python examples/create_mock_scene.py
```

Para salvar blend:

```bash
blender --factory-startup --python examples/create_mock_scene.py -- "examples/rcgen_mock_scene.blend"
```

## Limitacoes atuais

- Interferencia por `bbox` (nao BVH).
- Furos/nut traps/insert pockets sao parametrizados e metadatados; integracao booleana detalhada ainda simplificada.
- Split automatico utiliza plano medio no maior eixo da peca (MVP), podendo exigir ajuste manual em geometrias complexas.
- Ackermann e validacoes cinematicas sao aproximadas.

## Troubleshooting

- `Missing references`: confira secao Referencias.
- `Missing hardpoints`: confira todos empties L/R.
- `Tie rod impossible`: ajuste `Servo Horn Length` ou `SteeringArm_Point`.
- `Shock stroke larger than total length`: reduza curso ou aumente comprimento.
- `3MF exporter not available`: habilite/exporte somente STL.
